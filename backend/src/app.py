from fastapi import FastAPI
from src.api.routes import router

# Create FastAPI app
app = FastAPI(title="Graph Extraction API")

# Include API routes
app.include_router(router)

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "API is running"}
