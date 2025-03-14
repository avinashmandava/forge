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
from testdata.test_data import test_data
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from db import cleanup_database

# Configuration
API_BASE_URL = "http://localhost:8000/api"
LOG_FILE = "extraction_test_results.jsonl"

# Initialize rich console for better output
console = Console()

class TestLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        # Create/clear the log file
        with open(self.log_file, 'w') as f:
            f.write('')

    async def log_result(self, entry: Dict):
        """Log a test result entry with timestamp"""
        try:
            entry["timestamp"] = datetime.now().isoformat()
            # Write directly to file first
            with open(self.log_file, 'a') as f:
                json.dump(entry, f)
                f.write('\n')

            # Then try to send to API
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_BASE_URL}/log", json=entry) as response:
                    return await response.json()
        except Exception as e:
            console.print(f"[red]Error logging result: {e}[/red]")
            return {"error": str(e)}

async def create_tenant(company_name: str) -> Optional[str]:
    """Create a new tenant and return its ID"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_BASE_URL}/create_tenant", json={
                "display_name": company_name
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    console.print(f"[green]Created tenant for {company_name}: {data['tenant_id']}[/green]")
                    return data["tenant_id"]
                else:
                    text = await response.text()
                    console.print(f"[red]Failed to create tenant. Status: {response.status}[/red]")
                    console.print(f"[red]Response: {text}[/red]")
                    return None
    except Exception as e:
        console.print(f"[red]Error creating tenant for {company_name}: {e}[/red]")
        return None

async def extract_data(tenant_id: str, text: str) -> Dict:
    """Send text to extraction endpoint and return result"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_BASE_URL}/extract", json={
                "tenant_id": tenant_id,
                "text": text
            }) as response:
                result = await response.json()
                return result
    except Exception as e:
        console.print(f"[red]Error in extraction: {e}[/red]")
        return {"error": str(e)}

async def process_company(company: Dict, logger: TestLogger, progress: Progress, task_id: int):
    """Process all entries for a single company"""
    company_name = company["name"]
    entries = company["entries"]

    # Create tenant
    tenant_id = await create_tenant(company_name)
    if not tenant_id:
        progress.update(task_id, advance=len(entries))
        return

    # Process each entry
    for entry in entries:
        # Extract data
        result = await extract_data(tenant_id, entry["text"])

        # Log the result
        log_entry = {
            "company": company_name,
            "tenant_id": tenant_id,
            "date": entry["date"],
            "input_text": entry["text"],
            "extraction_result": result
        }
        await logger.log_result(log_entry)

        # Update progress
        progress.update(task_id, advance=1)

        # Small delay to avoid overwhelming the system
        await asyncio.sleep(1)

async def main():
    console.print(Panel.fit("Starting Extraction Tests", style="bold magenta"))

    # Clean up database before starting
    console.print("[yellow]Cleaning up database...[/yellow]")
    await cleanup_database()
    console.print("[green]Database cleaned[/green]")

    # Initialize logger
    logger = TestLogger(LOG_FILE)

    # Calculate total entries
    total_entries = sum(len(company["entries"]) for company in test_data["companies"])

    console.print(f"\nFound [cyan]{len(test_data['companies'])}[/cyan] companies with [cyan]{total_entries}[/cyan] total entries")

    # Process companies with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("Processing entries...", total=total_entries)

        for company in test_data["companies"]:
            console.print(f"\n[yellow]Processing {company['name']}...[/yellow]")
            await process_company(company, logger, progress, task_id)

    console.print(Panel.fit("Test Run Completed!", style="bold green"))
    console.print(f"\nResults have been logged to [cyan]{LOG_FILE}[/cyan]")

if __name__ == "__main__":
    try:
        # Install rich dependencies if not present
        try:
            import rich
        except ImportError:
            console.print("[yellow]Installing required dependencies...[/yellow]")
            import subprocess
            subprocess.check_call(["pip", "install", "rich"])
            console.print("[green]Dependencies installed successfully![/green]")

        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test run interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Test run failed with error: {e}[/red]")
        sys.exit(1)
