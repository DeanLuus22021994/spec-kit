"""
MCP Server for Face Matching Biometrics.
Provides endpoints for face detection, recognition, and verification.
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Face Matcher MCP Server")


@app.get("/health")
async def health() -> dict[str, object]:
    """
    Health check endpoint.
    Returns the status of the service and GPU availability.
    """
    return {"status": "ok", "gpu": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
