from openai import OpenAI
from typing import Optional, Dict, Any
import os
import json
import traceback
from src.models.graph import ExtractedData
from src.services.database import get_schema, insert_graph_data

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def validate_extracted_data(data: dict) -> Optional[ExtractedData]:
    """Validate that extracted data follows the expected format"""
    try:
        if not isinstance(data, dict):
            return None

        # Check for required keys
        if "nodes" not in data or "relationships" not in data:
            return None

        # Check nodes format
        if not isinstance(data["nodes"], list):
            return None

        for node in data["nodes"]:
            if not isinstance(node, dict):
                return None
            if "type" not in node or "name" not in node:
                return None

        # Check relationships format
        if not isinstance(data["relationships"], list):
            return None

        for rel in data["relationships"]:
            if not isinstance(rel, dict):
                return None
            if "from_id" not in rel or "to_id" not in rel or "type" not in rel:
                return None

        # If we got here, basic validation passed
        return ExtractedData(
            nodes=data["nodes"],
            relationships=data["relationships"]
        )
    except Exception as e:
        print(f"Validation error: {e}")
        return None

def strip_markdown_codeblock(text: str) -> str:
    """Remove markdown code block syntax if present"""
    lines = text.strip().split('\n')

    # Check if the text starts with ```json and ends with ```
    if (lines[0].startswith('```json') or lines[0] == '```') and lines[-1] == '```':
        return '\n'.join(lines[1:-1])

    return text

async def extract_data(tenant_id: str, text: str) -> Dict[str, Any]:
    try:
        # Get existing schema for the tenant
        schema = await get_schema(tenant_id)

        prompt = f"""
        Extract entities and relationships from the following text. Focus on identifying:

        1. Entities (nodes) with their types and names
        2. Relationships between entities

        Current schema (if any):
        Node types: {schema['node_types']}
        Relationship types: {schema['relationship_types']}

        Return the extracted information as a JSON object with the following structure:
        {{
            "nodes": [
                {{ "type": "EntityType", "name": "EntityName" }},
                ...
            ],
            "relationships": [
                {{ "from_id": "EntityName1", "to_id": "EntityName2", "type": "RELATIONSHIP_TYPE" }},
                ...
            ]
        }}

        TEXT TO ANALYZE:
        {text}
        """

        print("Calling OpenAI to extract data...")
        response = openai_client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=[
                {"role": "system", "content": "You are a skilled information extraction system that identifies entities and relationships from text and returns them in a structured format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        # Get the response content
        response_text = response.choices[0].message.content

        # Strip markdown if present (OpenAI might wrap in ```json...```)
        cleaned_text = strip_markdown_codeblock(response_text)

        # Parse the JSON
        extraction_result = json.loads(cleaned_text)

        # Validate the structure
        validated_data = validate_extracted_data(extraction_result)

        if not validated_data:
            return {"error": "Invalid extraction format", "raw_result": extraction_result}

        # Insert the data into the graph database
        insert_success = await insert_graph_data(tenant_id, validated_data)

        if not insert_success:
            return {
                "error": "Failed to insert data",
                "nodes": validated_data["nodes"],
                "relationships": validated_data["relationships"]
            }

        # Return the extracted data
        return {
            "success": True,
            "nodes": validated_data["nodes"],
            "relationships": validated_data["relationships"]
        }

    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"Error in extraction: {e}")
        print(traceback_str)
        return {"error": str(e), "traceback": traceback_str}
