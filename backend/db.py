from neo4j import GraphDatabase
import os

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
)

async def create_tenant(tenant_id: str, display_name: str):
    with driver.session() as session:
        # Create tenant node for segregation
        session.run(
            "MERGE (t:Tenant {id: $tenant_id, display_name: $display_name})",
            tenant_id=tenant_id, display_name=display_name
        )
        # Default sales funnel: Lead → Qualification → Demo → Negotiation → Closed
        session.run(
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
            """,
            tenant_id=tenant_id
        )

async def get_schema(tenant_id: str):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (t:Tenant {id: $tenant_id})-[:BELONGS_TO]-(s:Stage)
            OPTIONAL MATCH (s)-[:NEXT_STAGE]->(next:Stage)
            RETURN s.id AS id, s.name AS name, next.id AS next_id
            """,
            tenant_id=tenant_id
        )
        stages = [{"id": r["id"], "name": r["name"], "next": r["next_id"]} for r in result]
        return {"tenant_id": tenant_id, "stages": stages}
