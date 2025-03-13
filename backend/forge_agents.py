from openai import OpenAI
from neo4j import GraphDatabase
from agents import Agent, Runner
from db import get_schema
import os

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
)

extract_agent = Agent(
    name="DataExtractor",
    instructions="Extract structured data (Contact, Deal, Stage, Task) from text using a Neo4j schema for a specific tenant.",
    tools=[
        {
            "name": "insert_data",
            "description": "Insert extracted entities and relationships into Neo4j for a tenant",
            "handler": lambda data: neo4j_driver.session().run(
                """
                MATCH (t:Tenant {id: $tenant_id})
                UNWIND $nodes AS node
                MERGE (n:{node.type} {id: $tenant_id + '-' + randomUUID(), name: node.name})-[:BELONGS_TO]->(t)
                WITH t, $relationships AS rels UNWIND rels AS rel
                MATCH (from {id: rel.from}), (to {id: rel.to})
                MERGE (from)-[r:{rel.type}]->(to)
                """,
                tenant_id=data["tenant_id"], nodes=data["nodes"], relationships=data["relationships"]
            ),
            "schema": {
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "nodes": {"type": "array", "items": {"type": "object", "properties": {"type": "string", "name": "string"}}},
                    "relationships": {"type": "array", "items": {"type": "object", "properties": {"from": "string", "to": "string", "type": "string"}}}
                }
            }
        }
    ]
)

async def extract_data(tenant_id: str, text: str) -> str:
    schema = await get_schema(tenant_id)
    result = await Runner.run(extract_agent, f"Extract from: '{text}' using schema: {schema}")
    return result.final_output
