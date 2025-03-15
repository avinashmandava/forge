from neo4j import GraphDatabase
import os
from typing import Dict, Any, Optional
import json
from src.models.graph import Node, Relationship, ExtractedData

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

async def create_tenant(tenant_id: str, display_name: str):
    print(f"\n=== Creating Tenant ===")
    print(f"ID: {tenant_id}")
    print(f"Name: {display_name}")

    with driver.session() as session:
        # Create tenant node
        session.run(
            """
            CREATE (t:Tenant {id: $tenant_id, name: $display_name, created_at: datetime()})
            """,
            tenant_id=tenant_id,
            display_name=display_name
        )

        # Create constraints if they don't exist (this is idempotent)
        constraints = [
            "CREATE CONSTRAINT tenant_id IF NOT EXISTS FOR (t:Tenant) REQUIRE t.id IS UNIQUE",
        ]

        for constraint in constraints:
            try:
                session.run(constraint)
            except Exception as e:
                print(f"Warning: Couldn't create constraint. This is normal if it already exists: {e}")

async def get_schema(tenant_id: str) -> Dict[str, Any]:
    with driver.session() as session:
        # Get node types
        result = session.run(
            """
            MATCH (n)
            WHERE n:Tenant AND n.id = $tenant_id OR
                  EXISTS((n)<-[:BELONGS_TO]-(:Tenant {id: $tenant_id}))
            RETURN DISTINCT labels(n) as node_types
            """,
            tenant_id=tenant_id
        )
        node_types = [record["node_types"][0] for record in result if record["node_types"][0] != "Tenant"]

        # Get relationship types
        result = session.run(
            """
            MATCH (a)-[r]->(b)
            WHERE
                (a:Tenant AND a.id = $tenant_id) OR
                (b:Tenant AND b.id = $tenant_id) OR
                EXISTS((a)<-[:BELONGS_TO]-(:Tenant {id: $tenant_id})) OR
                EXISTS((b)<-[:BELONGS_TO]-(:Tenant {id: $tenant_id}))
            RETURN DISTINCT type(r) as rel_type
            """,
            tenant_id=tenant_id
        )
        rel_types = [record["rel_type"] for record in result if record["rel_type"] != "BELONGS_TO"]

        return {
            "node_types": node_types,
            "relationship_types": rel_types
        }

async def insert_graph_data(tenant_id: str, data: ExtractedData) -> bool:
    try:
        print(f"\n=== Inserting Graph Data ===")
        print(f"Tenant ID: {tenant_id}")
        print(f"Nodes: {len(data['nodes'])}")
        print(f"Relationships: {len(data['relationships'])}")

        # First, ensure tenant exists
        with driver.session() as session:
            tenant_check = session.run(
                "MATCH (t:Tenant {id: $tenant_id}) RETURN count(t) as count",
                tenant_id=tenant_id
            )
            tenant_exists = tenant_check.single()["count"] > 0

            if not tenant_exists:
                print(f"Error: Tenant {tenant_id} does not exist")
                return False

        # Create nodes and link them to tenant
        for node in data["nodes"]:
            with driver.session() as session:
                # Create node with Tenant relationship
                session.run(
                    f"""
                    MATCH (t:Tenant {{id: $tenant_id}})
                    MERGE (n:{node['type']} {{name: $name}})
                    MERGE (n)-[:BELONGS_TO]->(t)
                    """,
                    tenant_id=tenant_id,
                    name=node["name"]
                )
                print(f"Created/Updated node: {node['type']} - {node['name']}")

        # Create relationships
        for rel in data["relationships"]:
            with driver.session() as session:
                # Find the from and to nodes within this tenant's context
                result = session.run(
                    f"""
                    MATCH (from)-[:BELONGS_TO]->(t:Tenant {{id: $tenant_id}}),
                          (to)-[:BELONGS_TO]->(t:Tenant {{id: $tenant_id}})
                    WHERE from.name = $from_name AND to.name = $to_name
                    MERGE (from)-[r:{rel['type']}]->(to)
                    RETURN count(r) as created
                    """,
                    tenant_id=tenant_id,
                    from_name=rel["from_id"],
                    to_name=rel["to_id"]
                )
                created = result.single()["created"]
                print(f"Relationship: {rel['from_id']} -[{rel['type']}]-> {rel['to_id']} (created: {created})")

        return True
    except Exception as e:
        print(f"Error inserting graph data: {e}")
        import traceback
        traceback.print_exc()
        return False

async def cleanup_database():
    """Delete all nodes and relationships in the database - use for testing only"""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Database cleaned up")
