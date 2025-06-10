import asyncio
from tools.server import mcp
from fastapi import FastAPI, APIRouter
import uvicorn

# mcp_app = mcp.http_app(transport="sse")
# # Tạo FastAPI app chính
# app = FastAPI(
#     title="My FastAPI + FastMCP App",
#     description="Demo app with both FastMCP and a simple API",
#     version="1.0",
#     lifespan=mcp_app.lifespan  # để MCP khởi tạo đúng
# )

# # Mount FastMCP ASGI app vào đường dẫn con /mcp
# app.mount("/mcp-server", mcp_app)

# # Tạo router đơn giản
# simple_router = APIRouter()

# @simple_router.get("/ping", tags=["Simple"])
# async def ping():
#     return {"message": "pong"}

# Đăng ký router vào app
# app.include_router(simple_router)
if __name__ == "__main__":
    # uvicorn.run(app, host="127.0.0.1", port=8000)
    mcp.run(transport="sse")
