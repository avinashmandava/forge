from pydantic import BaseModel
from typing import Dict, Any

class TenantRequest(BaseModel):
    display_name: str

class ExtractRequest(BaseModel):
    tenant_id: str
    text: str

class QueryRequest(BaseModel):
    tenant_id: str
    query: str

class LogEntry(BaseModel):
    company: str
    tenant_id: str
    input_text: str
    extraction_result: Dict[str, Any]
    timestamp: str
