from fastapi import FastAPI
from fastmcp import FastMCP
from fastapi import UploadFile, File
import shutil

# Your existing FastAPI application
fastapi_app = FastAPI(title="My Existing API")

@fastapi_app.get("/status")
def get_status(): 
    return {"status": "running"}

@fastapi_app.post("/items")
def create_item(name: str, price: float): 
    return {"id": 1, "name": name, "price": price}

@fastapi_app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    with open(f"/app/uploaded/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

# Generate an MCP server directly from the FastAPI app
mcp_server = FastMCP.from_fastapi(fastapi_app)

if __name__ == "__main__":
    mcp_server.run(transport="sse")