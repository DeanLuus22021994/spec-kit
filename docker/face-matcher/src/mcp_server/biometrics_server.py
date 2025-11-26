import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Face Matcher MCP Server")


@app.get("/health")
async def health():
    return {"status": "ok", "gpu": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
