#!/usr/bin/env python3

import requests
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

def create_test_tenant():
    """Create a test tenant for our examples"""
    response = requests.post(
        f"{API_URL}/api/create_tenant",
        json={"display_name": "Test Tenant"}
    )
    if response.status_code == 200:
        return response.json()["tenant_id"]
    else:
        print(f"Error creating tenant: {response.text}")
        sys.exit(1)

def load_test_data(tenant_id):
    """Load some test data for our examples"""
    test_data = [
        "John is the CEO of Acme Corp.",
        "Sarah works for Acme Corp as a developer.",
        "Acme Corp is headquartered in New York.",
        "Globex is a competitor of Acme Corp.",
        "John previously worked at Globex.",
        "Sarah and John are colleagues."
    ]

    for text in test_data:
        response = requests.post(
            f"{API_URL}/api/extract",
            json={"tenant_id": tenant_id, "text": text}
        )
        if response.status_code != 200:
            print(f"Error loading test data: {response.text}")
            return False

    return True

def test_query(tenant_id, query):
    """Test a natural language query"""
    print(f"\n--- Testing Query: '{query}' ---\n")

    response = requests.post(
        f"{API_URL}/api/query",
        json={"tenant_id": tenant_id, "query": query}
    )

    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    result = response.json()

    if not result.get("success", False):
        print(f"Query failed: {result.get('error', 'Unknown error')}")
        if "query" in result:
            print(f"Generated Cypher: {result['query']}")
        return

    print(f"Generated Cypher Query:\n{result['query']}\n")

    # Print the formatted response
    formatted = result["results"]["formatted_response"]
    print("Summary:")
    print(formatted["summary"])

    print("\nInsights:")
    for insight in formatted["insights"]:
        print(f"- {insight}")

    if formatted.get("limitations"):
        print("\nLimitations:")
        print(formatted["limitations"])

    # Print raw results
    print("\nRaw Results:")
    print(json.dumps(result["results"]["raw_results"], indent=2))

def main():
    # Create a test tenant
    tenant_id = create_test_tenant()
    print(f"Created test tenant with ID: {tenant_id}")

    # Load test data
    print("Loading test data...")
    if not load_test_data(tenant_id):
        print("Failed to load test data.")
        sys.exit(1)

    print("Test data loaded successfully!")

    # Test some queries
    test_queries = [
        "Who works at Acme Corp?",
        "What companies are mentioned in the data?",
        "What is the relationship between John and Sarah?",
        "Where is Acme Corp headquartered?",
        "What is John's employment history?"
    ]

    for query in test_queries:
        test_query(tenant_id, query)

    # Optionally, allow interactive queries
    print("\n--- Interactive Query Mode ---")
    print("Enter 'exit' to quit.")

    while True:
        user_query = input("\nEnter your query: ")
        if user_query.lower() == "exit":
            break

        test_query(tenant_id, user_query)

if __name__ == "__main__":
    main()
