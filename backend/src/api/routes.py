from fastapi import APIRouter, Depends
import uuid
import json
from datetime import datetime
from src.models.api import TenantRequest, ExtractRequest, LogEntry, QueryRequest
from src.services.database import create_tenant
from src.services.extraction import extract_data
from src.services.query import natural_language_to_cypher

router = APIRouter(prefix="/api")

@router.post("/create_tenant")
async def create_tenant_endpoint(request: TenantRequest):
    tenant_id = str(uuid.uuid4())
    await create_tenant(tenant_id, request.display_name)
    return {"tenant_id": tenant_id, "display_name": request.display_name}

@router.post("/extract")
async def extract_endpoint(request: ExtractRequest):
    result = await extract_data(request.tenant_id, request.text)
    return {"result": result}

@router.post("/query")
async def query_endpoint(request: QueryRequest):
    """Process a natural language query and convert it to Cypher"""
    result = await natural_language_to_cypher(request.tenant_id, request.query)
    return result

@router.post("/log")
async def log_endpoint(entry: LogEntry):
    """Log test results to a file"""
    with open("extraction_test_results.jsonl", "a") as f:
        f.write(json.dumps(entry.dict()) + "\n")
    return {"status": "logged"}
