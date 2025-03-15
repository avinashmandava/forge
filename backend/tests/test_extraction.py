import os
from dotenv import load_dotenv

# Load environment variables from .env file - needed when running script directly
load_dotenv()

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import sys
from tests.testdata.test_data import test_data
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from src.services.database import cleanup_database

# Configuration
API_BASE_URL = "http://localhost:8000/api"
LOG_FILE = "extraction_test_results.jsonl"

# Initialize rich console for better output
console = Console()

class TestLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        # Create/clear the log file
        with open(log_file, 'w') as f:
            pass

    async def log_result(self, entry: Dict):
        """Log a result to the file and the API"""
        # Add timestamp
        entry["timestamp"] = datetime.now().isoformat()

        # Log to file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        # Log to API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_BASE_URL}/log", json=entry) as response:
                    await response.json()
        except Exception as e:
            console.print(f"[bold red]Error logging to API: {e}[/bold red]")

async def create_tenant(company_name: str) -> Optional[str]:
    """Create a tenant for the company"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/create_tenant",
                json={"display_name": company_name}
            ) as response:
                result = await response.json()
                tenant_id = result.get("tenant_id")
                if tenant_id:
                    return tenant_id
                else:
                    console.print(f"[bold red]Error creating tenant: {result}[/bold red]")
                    return None
    except Exception as e:
        console.print(f"[bold red]Error creating tenant: {e}[/bold red]")
        return None

async def extract_data(tenant_id: str, text: str) -> Dict:
    """Submit text for extraction"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/extract",
                json={"tenant_id": tenant_id, "text": text}
            ) as response:
                return await response.json()
    except Exception as e:
        console.print(f"[bold red]Error extracting data: {e}[/bold red]")
        return {"error": str(e)}

async def process_company(company: Dict, logger: TestLogger, progress: Progress, task_id: int):
    """Process a single company's test data"""
    company_name = company["name"]
    entries = company["entries"]

    # Create a tenant for this company
    tenant_id = await create_tenant(company_name)
    if not tenant_id:
        progress.update(task_id, advance=len(entries), description=f"[red]{company_name}: Failed to create tenant[/red]")
        return

    # Process each test input
    for i, entry in enumerate(entries):
        progress.update(task_id, advance=1, description=f"{company_name}: Processing input {i+1}/{len(entries)}")

        # Extract data
        extraction_result = await extract_data(tenant_id, entry["text"])

        # Log the result
        await logger.log_result({
            "company": company_name,
            "tenant_id": tenant_id,
            "date": entry["date"],
            "input_text": entry["text"],
            "extraction_result": extraction_result.get("result", {"error": "No result returned"})
        })

        # Sleep briefly to avoid overwhelming the API
        await asyncio.sleep(0.5)

    progress.update(task_id, description=f"[green]{company_name}: Completed[/green]")

async def main():
    """Run the extraction test"""
    console.print(Panel.fit("Graph Extraction Testing Tool", style="bold blue"))

    # Initialize the logger
    logger = TestLogger(LOG_FILE)

    # Clean up the database first
    console.print("[yellow]Cleaning up database...[/yellow]")
    await cleanup_database()

    # Calculate total number of test inputs
    total_inputs = sum(len(company["entries"]) for company in test_data["companies"])

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn()
    ) as progress:
        # Create tasks for each company
        tasks = []
        for company in test_data["companies"]:
            num_inputs = len(company["entries"])
            task_id = progress.add_task(f"{company['name']}: Starting...", total=num_inputs)
            tasks.append(asyncio.create_task(process_company(company, logger, progress, task_id)))

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    console.print(f"[bold green]Testing complete! Results logged to {LOG_FILE}[/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
