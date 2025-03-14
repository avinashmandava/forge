from neo4j import GraphDatabase
import os
from typing import Dict, Any, Optional
from typing_extensions import TypedDict
import json

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

class Node(TypedDict):
    type: str
    name: str

class Relationship(TypedDict):
    from_id: str
    to_id: str
    type: str

class ExtractedData(TypedDict):
    nodes: list[Node]
    relationships: list[Relationship]

async def create_tenant(tenant_id: str, display_name: str):
    print(f"\n=== Creating Tenant ===")
    print(f"ID: {tenant_id}")
    print(f"Name: {display_name}")

    with driver.session() as session:
        # Create tenant node for segregation
        result = session.run(
            "MERGE (t:Tenant {id: $tenant_id, display_name: $display_name}) RETURN t",
            tenant_id=tenant_id, display_name=display_name
        ).single()
        print(f"Created tenant node: {result}")

        # Default sales funnel: Lead → Qualification → Demo → Negotiation → Closed
        result = session.run(
            """
            MATCH (t:Tenant {id: $tenant_id})
            MERGE (l:Stage {id: $tenant_id + '-1', name: 'Lead'})-[:BELONGS_TO]->(t)
            MERGE (q:Stage {id: $tenant_id + '-2', name: 'Qualification'})-[:BELONGS_TO]->(t)
            MERGE (d:Stage {id: $tenant_id + '-3', name: 'Demo'})-[:BELONGS_TO]->(t)
            MERGE (n:Stage {id: $tenant_id + '-4', name: 'Negotiation'})-[:BELONGS_TO]->(t)
            MERGE (c:Stage {id: $tenant_id + '-5', name: 'Closed'})-[:BELONGS_TO]->(t)
            MERGE (l)-[:NEXT_STAGE]->(q)
            MERGE (q)-[:NEXT_STAGE]->(d)
            MERGE (d)-[:NEXT_STAGE]->(n)
            MERGE (n)-[:NEXT_STAGE]->(c)
            RETURN l, q, d, n, c
            """,
            tenant_id=tenant_id
        ).single()
        print(f"Created stage nodes: {result}")

async def get_schema(tenant_id: str) -> Dict[str, Any]:
    print(f"\n=== Getting Schema for Tenant {tenant_id} ===")
    with driver.session() as session:
        result = session.run(
            """
            MATCH (t:Tenant {id: $tenant_id})-[:BELONGS_TO]-(s:Stage)
            OPTIONAL MATCH (s)-[:NEXT_STAGE]->(next:Stage)
            RETURN s.id AS id, s.name AS name, next.id AS next_id
            ORDER BY s.id
            """,
            tenant_id=tenant_id
        )
        stages = [{"id": r["id"], "name": r["name"], "next": r["next_id"]} for r in result]
        print(f"Found stages: {json.dumps(stages, indent=2)}")
        return {"tenant_id": tenant_id, "stages": stages}

async def insert_graph_data(tenant_id: str, data: ExtractedData) -> bool:
    """Insert extracted entities and relationships into Neo4j for a tenant.
    Returns True if successful, False if there was an error."""
    print(f"\n=== Inserting Graph Data for Tenant {tenant_id} ===")
    print("Data to insert:")
    print(json.dumps(data, indent=2))

    try:
        with driver.session() as session:
            # Insert nodes, map fake IDs to real ones
            node_ids = {}
            for node in data['nodes']:
                print(f"\nCreating node: {node['type']} - {node['name']}")
                # Construct query dynamically but safely
                node_type = node['type']  # Already validated as string
                query = f"""
                    MATCH (t:Tenant {{id: $tenant_id}})
                    MERGE (n:{node_type} {{id: $node_id, name: $name}})
                    MERGE (n)-[:BELONGS_TO]->(t)
                    RETURN n.id AS id, n.name AS name, labels(n) AS labels
                """
                result = session.run(
                    query,
                    tenant_id=tenant_id,
                    node_id=f"{tenant_id}-{node_type}-{node['name']}",
                    name=node['name']
                ).single()

                print(f"Created node result: {result}")

                # Map LLM's fake ID to real ID
                fake_id = f"{node['type']}-{node['name']}"
                node_ids[fake_id] = result["id"] if result else None

            print("\nNode ID mappings:")
            print(json.dumps(node_ids, indent=2))

            # Insert relationships using mapped IDs
            for rel in data['relationships']:
                from_id = node_ids.get(rel["from_id"], rel["from_id"])
                to_id = node_ids.get(rel["to_id"], rel["to_id"])
                rel_type = rel['type']  # Already validated as string
                print(f"\nCreating relationship: {rel_type} from {from_id} to {to_id}")

                query = f"""
                    MATCH (from) WHERE from.id = $from_id
                    MATCH (to) WHERE to.id = $to_id
                    MERGE (from)-[r:{rel_type}]->(to)
                    RETURN type(r) AS type, from.name AS from_name, to.name AS to_name
                """
                result = session.run(
                    query,
                    from_id=from_id,
                    to_id=to_id
                ).single()

                print(f"Created relationship result: {result}")

            # Verify the data was inserted
            print("\nVerifying data insertion...")
            result = session.run(
                """
                MATCH (t:Tenant {id: $tenant_id})<-[:BELONGS_TO]-(n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN labels(n) AS node_type, n.name AS name,
                       type(r) AS rel_type, m.name AS target_name
                """,
                tenant_id=tenant_id
            ).data()

            print("Verification results:")
            print(json.dumps(result, indent=2))

            return True
    except Exception as e:
        print(f"\n=== Error inserting data: {str(e)} ===")
        return False

async def cleanup_database():
    """Delete all nodes and relationships in the database."""
    try:
        with driver.session() as session:
            # Delete all relationships first
            session.run("MATCH ()-[r]->() DELETE r")
            # Then delete all nodes
            session.run("MATCH (n) DELETE n")
            print("Database cleaned successfully")
            return True
    except Exception as e:
        print(f"Error cleaning up database: {e}")
        return False
