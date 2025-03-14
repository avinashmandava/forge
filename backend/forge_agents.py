from openai import OpenAI
from neo4j import GraphDatabase
from agents import Agent, Runner
from db import get_schema, insert_graph_data
from typing_extensions import TypedDict
import os
import json
from typing import Optional
import traceback

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

class ExtractedData(TypedDict):
    nodes: list[Node]
    relationships: list[Relationship]

def validate_extracted_data(data: dict) -> Optional[ExtractedData]:
    """Validate the structure of extracted data before processing."""
    try:
        if not isinstance(data, dict):
            return None
        if not all(k in data for k in ['nodes', 'relationships']):
            return None

        # Validate nodes
        if not isinstance(data['nodes'], list):
            return None
        for node in data['nodes']:
            if not isinstance(node, dict) or not all(k in node for k in ['type', 'name']):
                return None
            if not isinstance(node['type'], str) or not isinstance(node['name'], str):
                return None

        # Validate relationships
        if not isinstance(data['relationships'], list):
            return None
        for rel in data['relationships']:
            if not isinstance(rel, dict) or not all(k in rel for k in ['from_id', 'to_id', 'type']):
                return None
            if not all(isinstance(rel[k], str) for k in ['from_id', 'to_id', 'type']):
                return None

        return ExtractedData(nodes=data['nodes'], relationships=data['relationships'])
    except Exception:
        return None

def strip_markdown_codeblock(text: str) -> str:
    """Remove markdown code block markers if present."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        # Remove first line if it contains ```json or similar
        lines = text.split("\n")
        if len(lines) > 2:
            lines = lines[1:-1]
        else:
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()

extract_agent = Agent(
    name="DataExtractor",
    instructions="""You are a precise data extractor. Your job is to extract structured data from text and return it as raw JSON (not wrapped in markdown code blocks).

ENTITIES TO EXTRACT:
- Contact (person): Extract name and any identifying details
- Deal (product/company): Extract company name or product details
- Stage: Must be one of: Lead, Qualification, Demo, Negotiation, Closed
- Task: Extract any actions or follow-ups

RELATIONSHIP TYPES:
Only use these exact relationship types:
- HAS_DEAL: from Contact to Deal
- IN_STAGE: from Deal to Stage
- HAS_TASK: from Contact to Task
- NEXT_STAGE: from Stage to Stage (already exists in schema)

RETURN FORMAT:
Return the raw JSON object directly (do not wrap in markdown code blocks, do not add any other text):
{
    "nodes": [
        {"type": "Contact", "name": "Full Name"},
        {"type": "Deal", "name": "Company/Product Name"},
        {"type": "Stage", "name": "One of the valid stages"},
        {"type": "Task", "name": "Action description"}
    ],
    "relationships": [
        {"from_id": "Contact-Full Name", "to_id": "Deal-Company Name", "type": "HAS_DEAL"},
        {"from_id": "Deal-Company Name", "to_id": "Stage-Lead", "type": "IN_STAGE"},
        {"from_id": "Contact-Full Name", "to_id": "Task-Action description", "type": "HAS_TASK"}
    ]
}

IMPORTANT RULES:
1. Return ONLY the raw JSON object
2. Do not wrap in markdown code blocks
3. Do not add any explanatory text
4. Use double quotes for strings
5. Node IDs must be "Type-Name" format
6. Every Deal must have an IN_STAGE relationship
7. Every Task must have a HAS_TASK relationship from a Contact
8. Use only the relationship types listed above
9. Stage names must match exactly: Lead, Qualification, Demo, Negotiation, or Closed
"""
)

async def extract_data(tenant_id: str, text: str) -> str:
    """Extract entities and relationships from text and save to database."""
    try:
        # Get schema for context
        schema = await get_schema(tenant_id)
        print("\n=== Schema ===")
        print(json.dumps(schema, indent=2))

        # Get raw JSON from LLM
        print("\n=== Sending to LLM ===")
        print(f"Text: {text}")
        result = await Runner.run(extract_agent, f"Extract from: '{text}' using schema: {schema}")

        print("\n=== Raw LLM Response ===")
        print(result.final_output)

        # Clean up the response by removing markdown if present
        cleaned_output = strip_markdown_codeblock(result.final_output)
        print("\n=== Cleaned Output ===")
        print(cleaned_output)

        # Parse and validate the JSON
        try:
            data = json.loads(cleaned_output)
            print("\n=== Parsed JSON ===")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print("\n=== JSON Parse Error ===")
            print(f"Error: {str(e)}")
            print("Raw text that failed to parse:", cleaned_output)
            return "Error: Invalid JSON returned from LLM"

        print("\n=== Running Validation ===")
        validated_data = validate_extracted_data(data)
        if validated_data is None:
            print("\n=== Validation Failed ===")
            print("Data structure received:")
            print(json.dumps(data, indent=2))
            print("\nExpected structure:")
            print("""
            {
                "nodes": [
                    {"type": "Contact", "name": "..."},
                    {"type": "Deal", "name": "..."},
                    {"type": "Stage", "name": "..."}
                ],
                "relationships": [
                    {"from_id": "Type-Name", "to_id": "Type-Name", "type": "..."}
                ]
            }
            """)
            return "Error: Invalid data structure returned from LLM"

        print("\n=== Validation Passed - Inserting Data ===")
        print("Data to insert:")
        print(json.dumps(validated_data, indent=2))

        # Insert validated data into database
        success = await insert_graph_data(tenant_id, validated_data)
        if not success:
            print("\n=== Database Insert Failed ===")
            print("Last attempted operation was inserting validated data:")
            print(json.dumps(validated_data, indent=2))
            return "Error: Failed to insert data into database"

        print("\n=== Database Insert Successful ===")
        return "Data extracted and saved successfully"
    except Exception as e:
        print(f"\n=== Unexpected Error in extract_data ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Stack trace:", traceback.format_exc())
        return f"Error: {str(e)}"
