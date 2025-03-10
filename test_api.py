import asyncio
import httpx
import json

async def test_crm_api():
    # Configure longer timeouts for API calls
    timeout = httpx.Timeout(
        connect=30.0,  # connection timeout
        read=30.0,    # read timeout
        write=30.0,   # write timeout
        pool=30.0     # pool timeout
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        # First list all companies
        print("\nListing all companies...")
        response = await client.get("http://localhost:8000/api/v1/crm/companies/")

        if response.status_code == 200:
            companies = response.json()
            print("Existing companies:")
            print(json.dumps(companies, indent=2))

            # Check if Databricks exists
            databricks = next((c for c in companies if c["name"] == "Databricks"), None)
            if databricks:
                company_response = databricks
                print("\nFound existing Databricks company:")
                print(json.dumps(company_response, indent=2))
            else:
                # Create a company if it doesn't exist
                company_data = {
                    "name": "Databricks",
                    "industry": "Technology",
                    "website": "https://databricks.com",
                    "description": "Leading unified analytics platform"
                }

                print("\nCreating new company:", json.dumps(company_data, indent=2))
                response = await client.post(
                    "http://localhost:8000/api/v1/crm/companies/",
                    json=company_data
                )
                print("Response status code:", response.status_code)

                if response.status_code != 200:
                    print("Error creating company:", response.text)
                    return

                company_response = response.json()
                print("\nCreated company:")
                print(json.dumps(company_response, indent=2))
        else:
            print("Error listing companies:", response.text)
            return

        if not company_response:
            print("Failed to get or create company")
            return

        # Check if contact exists
        print("\nListing contacts...")
        response = await client.get("http://localhost:8000/api/v1/crm/contacts/")

        contact_response = None
        if response.status_code == 200:
            contacts = response.json()
            # Check if Bill exists
            contact_response = next(
                (c for c in contacts if c["email"] == "bill.thompson@databricks.com"),
                None
            )
            if contact_response:
                print("\nFound existing contact:")
                print(json.dumps(contact_response, indent=2))

        if not contact_response:
            # Create a contact if doesn't exist
            contact_data = {
                "first_name": "Bill",
                "last_name": "Thompson",
                "email": "bill.thompson@databricks.com",
                "phone": "+1-555-123-4567",
                "position": "VP Sales",
                "company_id": company_response["id"]
            }

            print("\nCreating new contact:", json.dumps(contact_data, indent=2))
            response = await client.post(
                "http://localhost:8000/api/v1/crm/contacts/",
                json=contact_data
            )
            print("Response status code:", response.status_code)
            if response.status_code != 200:
                print("Error creating contact:", response.text)
                return

            contact_response = response.json()
            print("\nCreated contact:")
            print(json.dumps(contact_response, indent=2))

        # Process an interaction
        interaction_text = """Just had a great meeting with Bill from Databricks. He's very interested in our enterprise solution. They have a budget of $500k and need implementation by Q3. Bill mentioned concerns about integration with their existing systems. Need to schedule a technical deep dive next week."""

        print("\nSending interaction data:", interaction_text)
        for attempt in range(3):  # Try up to 3 times
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/crm/process-interaction/",
                    json={"text": interaction_text}
                )
                print("Response status code:", response.status_code)
                if response.status_code != 200:
                    print("Error response:", response.text)
                    return

                interaction_response = response.json()
                print("\nProcessed interaction:")
                print(json.dumps(interaction_response, indent=2))
                break  # Success, exit the retry loop
            except httpx.TimeoutException:
                if attempt == 2:  # Last attempt
                    print("Failed after 3 attempts due to timeout")
                    raise
                print(f"Attempt {attempt + 1} timed out, retrying...")
                await asyncio.sleep(1)  # Wait a second before retrying

if __name__ == "__main__":
    asyncio.run(test_crm_api())
