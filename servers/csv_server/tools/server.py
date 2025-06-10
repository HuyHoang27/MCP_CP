from fastmcp import FastMCP, Context
from tools.prompts import DataExplorationPrompts, PromptArgs, PROMPT_TEMPLATE, DataExplorationTools, \
    LOAD_CSV_TOOL_DESCRIPTION, LoadCsv, RUN_SCRIPT_TOOL_DESCRIPTION, RunScript, ScriptRunner
from fastmcp.prompts.prompt import PromptMessage, TextContent
from pydantic import Field

from fastapi import UploadFile, File
import shutil


mcp = FastMCP("MCP Server CSV", host="0.0.0.0", port=8001)

@mcp.prompt(
    name = DataExplorationPrompts.EXPLORE_DATA,
    description = 'A prompt to explore a csv dataset as a data scientist',
)
def data_analysis_prompt(
    csv_path: str = Field(description=PromptArgs.CSV_PATH),
    topic: str = Field(description=PromptArgs.TOPIC)
    ) -> list[PromptMessage]:
    prompt = PROMPT_TEMPLATE.format(csv_path=csv_path, topic=topic)
    return [
        PromptMessage(
            role='user',
            content=TextContent(type="text",text=prompt.strip()),
        )
    ]

@mcp.tool()
async def request_info(ctx: Context) -> str:
    return f"Server: {ctx.fastmcp.name}\n" \
           f"Session: {ctx.session}\n" \
           f"Request: {ctx.request_context}\n"

@mcp.tool()
async def upload_file(file: UploadFile = File(...)):
    with open(f"/app/uploaded/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

@mcp.resource("data://temp/{city}")
def get_temp(city: str): 
    return 25.0

obj = ScriptRunner()
mcp.add_tool(obj.load_csv, DataExplorationTools.LOAD_CSV, LOAD_CSV_TOOL_DESCRIPTION, LoadCsv.model_json_schema())
mcp.add_tool(obj.safe_eval, DataExplorationTools.RUN_SCRIPT, RUN_SCRIPT_TOOL_DESCRIPTION, RunScript.model_json_schema())
mcp.add_tool(obj.list_all_variables, "list_all_variables", "List all variables in the current session")

    