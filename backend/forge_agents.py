from openai import OpenAI
from neo4j import GraphDatabase
from agents import Agent, Runner, function_tool
from db import get_schema
from typing_extensions import TypedDict
import os

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
)

class Node(TypedDict):
    type: str
    name: str

class Relationship(TypedDict):
    from_id: str
    to_id: str
    type: str

@function_tool
def insert_data(tenant_id: str, nodes: list[Node], relationships: list[Relationship]) -> str:
    """Insert extracted entities and relationships into Neo4j for a tenant."""
    with neo4j_driver.session() as session:
        # Insert nodes, map fake IDs to real ones
        node_ids = {}
        for node in nodes:
            result = session.run(
                f"""
                MATCH (t:Tenant {{id: $tenant_id}})
                MERGE (n:{node['type']} {{id: $tenant_id + '-' + randomUUID(), name: $name}})-[:BELONGS_TO]->(t)
                RETURN n.id AS id
                """,
                tenant_id=tenant_id, name=node['name']
            ).single()
            # Map LLM's fake ID to real ID
            fake_id = f"{node['type']}-{node['name']}"
            node_ids[fake_id] = result["id"]

        # Insert relationships using mapped IDs
        for rel in relationships:
            from_id = node_ids.get(rel["from_id"], rel["from_id"])
            to_id = node_ids.get(rel["to_id"], rel["to_id"])
            session.run(
                f"""
                MATCH (from) WHERE from.id = $from_id
                MATCH (to) WHERE to.id = $to_id
                MERGE (from)-[r:{rel['type']}]->(to)
                """,
                from_id=from_id, to_id=to_id
            )
    return "Data inserted successfully"

extract_agent = Agent(
    name="DataExtractor",
    instructions="Extract Contact (person), Deal (product), Stage (Lead/Qualification/Demo/Negotiation/Closed), Task (action) from text using the schema. Format as JSON like {'nodes': [{'type': 'Contact', 'name': 'Bill'}], 'relationships': [{'from_id': 'Contact-Bill', 'to_id': 'Deal-Solution', 'type': 'HAS_DEAL'}]}. Call insert_data with tenant_id and this JSON, then return 'Data saved'.",
    tools=[insert_data]
)

async def extract_data(tenant_id: str, text: str) -> str:
    schema = await get_schema(tenant_id)
    result = await Runner.run(extract_agent, f"Extract from: '{text}' using schema: {schema} for tenant_id: '{tenant_id}'")
    return result.final_output
