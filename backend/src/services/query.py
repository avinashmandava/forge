from openai import OpenAI
import os
from typing import Dict, Any, List, Optional
import json
from src.services.database import get_schema, driver

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def validate_cypher_query(query: str) -> Dict[str, Any]:
    """Basic validation of a Cypher query for safety"""
    # Check for common unsafe patterns or potential issues
    lower_query = query.lower()

    # Disallow data modification queries
    if any(keyword in lower_query for keyword in ["create", "delete", "remove", "set", "merge"]):
        return {
            "valid": False,
            "reason": "Data modification queries are not allowed"
        }

    # Only allow READ operations
    if not any(keyword in lower_query for keyword in ["match", "return"]):
        return {
            "valid": False,
            "reason": "Query must include MATCH and RETURN clauses"
        }

    return {"valid": True}

async def format_query_results(results: List[Dict[str, Any]], query: str, natural_language_query: str) -> Dict[str, Any]:
    """Use LLM to format query results in a natural, user-friendly way"""

    # Convert results to a string for the prompt
    results_str = json.dumps(results, indent=2)

    prompt = f"""
    I executed the following Cypher query:
    ```
    {query}
    ```

    This query was generated to answer the natural language question:
    "{natural_language_query}"

    The query returned the following results:
    ```
    {results_str}
    ```

    Please provide:
    1. A natural language summary of the results that directly answers the original question
    2. Any key insights or patterns visible in the data
    3. If the results seem incomplete or potentially incorrect, mention what might be missing

    Format your response as a JSON object with these keys:
    - summary: A complete answer to the original question based on the data
    - insights: An array of key insights from the data
    - limitations: Any limitations of the results or potential issues
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {"role": "system", "content": "You are a data analyst assistant that helps interpret query results from a graph database."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    formatted_response = json.loads(response.choices[0].message.content)
    return {
        "raw_results": results,
        "formatted_response": formatted_response
    }

async def execute_cypher_query(query: str) -> List[Dict[str, Any]]:
    """Execute a Cypher query and return the results"""
    try:
        with driver.session() as session:
            result = session.run(query)
            # Convert Neo4j records to a list of dictionaries
            records = [dict(record) for record in result]
            return records
    except Exception as e:
        print(f"Error executing Cypher query: {e}")
        return []

async def natural_language_to_cypher(tenant_id: str, query: str) -> Dict[str, Any]:
    """Convert a natural language query to a Cypher query and execute it"""
    try:
        # Get existing schema for the tenant
        schema = await get_schema(tenant_id)

        # Create a prompt that includes schema information and examples
        prompt = f"""
        Convert the following natural language question into a Neo4j Cypher query.

        SCHEMA INFORMATION:
        - Node types in the database: {schema['node_types']}
        - Relationship types in the database: {schema['relationship_types']}
        - All nodes belong to a tenant with ID: {tenant_id}
        - All nodes are connected to the tenant via a BELONGS_TO relationship

        CONSTRAINTS:
        - Query MUST only return data connected to tenant with ID: {tenant_id}
        - Query must include a tenant filter: MATCH (n)-[:BELONGS_TO]->(:Tenant {{id: "{tenant_id}"}})
        - Only READ operations are allowed (MATCH, RETURN, WHERE, etc.)
        - No data modification operations (CREATE, DELETE, SET, etc.)

        EXAMPLE CONVERSIONS:

        Natural Language: "Show me all Person nodes"
        Cypher:
        ```
        MATCH (p:Person)-[:BELONGS_TO]->(:Tenant {{id: "{tenant_id}"}})
        RETURN p.name
        ```

        Natural Language: "Which companies are related to John?"
        Cypher:
        ```
        MATCH (p:Person {{name: "John"}})-[:BELONGS_TO]->(:Tenant {{id: "{tenant_id}"}})
        MATCH (p)-[r]-(c:Company)
        RETURN p.name as person, type(r) as relationship, c.name as company
        ```

        YOUR TASK:
        Convert this natural language query to a valid Cypher query:
        "{query}"

        Return ONLY the Cypher query with no additional text or explanations. The query must be optimized, correct, and follow Neo4j best practices.
        """

        # Get the Cypher query from OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=[
                {"role": "system", "content": "You are a database expert that converts natural language queries to Cypher queries for Neo4j graph databases."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        cypher_query = response.choices[0].message.content.strip()

        # Extract code if wrapped in backticks
        if "```" in cypher_query:
            # Extract content between code blocks
            cypher_query = cypher_query.split("```")[1]
            # Remove language identifier if present (like "cypher")
            if cypher_query.lower().startswith("cypher"):
                cypher_query = cypher_query[6:].strip()
            else:
                cypher_query = cypher_query.strip()

        # Validate the query for safety
        validation = await validate_cypher_query(cypher_query)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["reason"],
                "query": cypher_query
            }

        # Execute the query
        results = await execute_cypher_query(cypher_query)

        # Format results using LLM
        formatted_results = await format_query_results(results, cypher_query, query)

        return {
            "success": True,
            "query": cypher_query,
            "results": formatted_results
        }

    except Exception as e:
        import traceback
        print(f"Error processing natural language query: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }
