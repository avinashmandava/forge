from fastapi import FastAPI
from pydantic import BaseModel
from db import create_tenant
from forge_agents import extract_data
import uuid
import json
from datetime import datetime
from typing import Dict, Any

app = FastAPI()

class TenantRequest(BaseModel):
    display_name: str

class ExtractRequest(BaseModel):
    tenant_id: str
    text: str

class LogEntry(BaseModel):
    company: str
    tenant_id: str
    input_text: str
    extraction_result: Dict[str, Any]
    timestamp: str

@app.post("/api/create_tenant")
async def create_tenant_endpoint(request: TenantRequest):
    tenant_id = str(uuid.uuid4())
    await create_tenant(tenant_id, request.display_name)
    return {"tenant_id": tenant_id, "display_name": request.display_name}

@app.post("/api/extract")
async def extract_endpoint(request: ExtractRequest):
    result = await extract_data(request.tenant_id, request.text)
    return {"result": result}

@app.post("/api/log")
async def log_endpoint(entry: LogEntry):
    """Log test results to a file"""
    with open("extraction_test_results.jsonl", "a") as f:
        f.write(json.dumps(entry.dict()) + "\n")
    return {"status": "logged"}
