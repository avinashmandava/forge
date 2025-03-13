from fastapi import FastAPI
from pydantic import BaseModel
from db import create_tenant
from forge_agents import extract_data
import uuid

app = FastAPI()

class TenantRequest(BaseModel):
    display_name: str

class ExtractRequest(BaseModel):
    tenant_id: str
    text: str

@app.post("/api/create_tenant")
async def create_tenant_endpoint(request: TenantRequest):
    tenant_id = str(uuid.uuid4())
    await create_tenant(tenant_id, request.display_name)
    return {"tenant_id": tenant_id, "display_name": request.display_name}

@app.post("/api/extract")
async def extract_endpoint(request: ExtractRequest):
    result = await extract_data(request.tenant_id, request.text)
    return {"result": result}
