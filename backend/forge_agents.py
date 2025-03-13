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
    instructions="You return the given text in uppercase."
)

async def extract_data(tenant_id: str, text: str) -> str:
    result = await Runner.run(extract_agent, f"Convert this text: '{text}'")
    return result.final_output
