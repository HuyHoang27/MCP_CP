from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

from fastmcp.prompts.prompt import TextContent
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR
import pandas as pd
import numpy as np
import scipy
import sklearn
# import matplotlib.pyplot as plt
# import seaborn as sns
# import plotly.express as px
import statsmodels.api as sm
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# import subprocess
# import tempfile
# import docker

class DataExplorationPrompts(str, Enum):
    EXPLORE_DATA = "explore-data"

class PromptArgs(str, Enum):
    CSV_PATH = "csv_path"
    TOPIC = "topic"
    
PROMPT_TEMPLATE = """
You are a professional Data Scientist tasked with performing exploratory data analysis on a dataset. Your goal is to provide insightful analysis while ensuring stability and manageable result sizes.

Your response must be written in Vietnamese.

First, load the CSV file from the following path:

<csv_path>
{csv_path}
</csv_path>

Your analysis should focus on the following topic:

<analysis_topic>
{topic}
</analysis_topic>

You have access to the following tools for your analysis:
1. load_csv: Use this to load the CSV file.
2. run-script: Use this to execute Python scripts on the MCP server.

Please follow these steps carefully:

1. Load the CSV file using the load_csv tool.

2. Explore the dataset. Provide a brief summary of its structure, including the number of rows, columns, and data types. Wrap your exploration process in <dataset_exploration> tags, including:
   - List of key statistics about the dataset
   - Potential challenges you foresee in analyzing this data

3. Wrap your thought process in <analysis_planning> tags:
   Analyze the dataset size and complexity:
   - How many rows and columns does it have?
   - Are there any potential computational challenges based on the data types or volume?
   - What kind of questions would be appropriate given the dataset's characteristics and the analysis topic?
   - How can we ensure that our questions won't result in excessively large outputs?

   Based on this analysis:
   - List 10 potential questions related to the analysis topic
   - Evaluate each question against the following criteria:
     * Directly related to the analysis topic
     * Can be answered with reasonable computational effort
     * Will produce manageable result sizes
     * Provides meaningful insights into the data
   - Select the top 5 questions that best meet all criteria

4. List the 5 questions you've selected, ensuring they meet the criteria outlined above.

5. For each question, follow these steps:
   a. Wrap your thought process in <analysis_planning> tags:
      - How can I structure the Python script to efficiently answer this question?
      - What data preprocessing steps are necessary?
      - How can I limit the output size to ensure stability?
      - What type of visualization would best represent the results?
      - Outline the main steps the script will follow
   
   b. Write a Python script to answer the question. Include comments explaining your approach and any measures taken to limit output size.
   
   c. Use the run_script tool to execute your Python script on the MCP server.
   
   d. Use the run_script tool again to execute a Python script that generates a chart using one of the following libraries: matplotlib, seaborn, or plotly (Python version). Include all necessary code to produce the visualization.

6. After completing the analysis for all 5 questions, provide a brief summary of your findings and any overarching insights gained from the data.

Remember to prioritize stability and manageability in your analysis. If at any point you encounter potential issues with large result sets, adjust your approach accordingly.

Please begin your analysis by loading the CSV file and providing an initial exploration of the dataset.
"""

class DataExplorationTools(str, Enum):
    LOAD_CSV = "load_csv"
    RUN_SCRIPT = "run_script"


LOAD_CSV_TOOL_DESCRIPTION = """
Load CSV File Tool

Purpose:
Load a local CSV file into a DataFrame.

Usage Notes:
	•	If a df_name is not provided, the tool will automatically assign names sequentially as df_1, df_2, and so on.
"""

class LoadCsv(BaseModel):
    csv_path: str
    df_name: str
    
RUN_SCRIPT_TOOL_DESCRIPTION = """
Python Script Execution Tool

Purpose:
Execute Python scripts for specific data analytics tasks.

Allowed Actions
	1.	Print Results: Output will be displayed as the script’s stdout.
	2.	[Optional] Save DataFrames: Store DataFrames in memory for future use by specifying a save_to_memory name.

Prohibited Actions
	1.	Overwriting Original DataFrames: Do not modify existing DataFrames to preserve their integrity for future tasks.
	2.	Creating Charts: Chart generation is not permitted.
"""

class RunScript(BaseModel):
    script: str
    save_to_memory: Optional[List[str]] = None
    
class ScriptRunner:
    def __init__(self):
        self.data = {}
        self.df_count = 0
        self.notes: list[str] = []

    def load_csv(self, csv_path: str, df_name: str):
        self.df_count += 1
        if not df_name:
            df_name = f"df_{self.df_count}"
        try:
            self.data[df_name] = pd.read_csv(csv_path)
            self.notes.append(f"Successfully loaded CSV into dataframe '{df_name}'")
            return [
                TextContent(type="text", text=f"Successfully loaded CSV into dataframe '{df_name}'")
            ]
        except Exception as e:
            raise McpError(
                INTERNAL_ERROR, f"Error loading CSV: {str(e)}"
            ) from e

    def safe_eval(self, script: str, save_to_memory: Optional[List[str]] = None):
        """safely run a script, return the result if valid, otherwise return the error message"""
        # first extract dataframes from the self.data
        local_dict = {
            **{df_name: df for df_name, df in self.data.items()},
        }
        # execute the script and return the result and if there is error, return the error message
        stdout = StringIO()
        stderr = StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # pylint: disable=exec-used
                exec(script, \
                    {'pd': pd, 'np': np, 'scipy': scipy, 'sklearn': sklearn, 'statsmodels': sm}, \
                    local_dict)

            self.notes.append(f"Running script: \n{script}")
            output = stdout.getvalue()
            errors = stderr.getvalue()
        except Exception as e:
            raise McpError(INTERNAL_ERROR, f"Error running script: {str(e)}") from e

        # check if the result is a dataframe
        if save_to_memory:
            for df_name in save_to_memory:
                self.notes.append(f"Saving dataframe '{df_name}' to memory")
                self.data[df_name] = local_dict.get(df_name)
        result = ""
        if output:
            result += f"Output:\n{output}\n"
        if errors:
            result += f"Errors:\n{errors}\n"

        self.notes.append(f"Result: {output}")
        return [
            TextContent(type="text", text=f"{result}"),
        ]
    
    def list_all_variables(self):
        """List all variables in the current session"""
        vars_dict = {
            k: repr(v) for k, v in self.data.items() 
            if not k.startswith('_') and k != '__builtins__'
        }
        
        if not vars_dict:
            return [
                TextContent(
                    type="text",
                    text="No variables in current session."
                )
            ]
        
        # Format variables list
        var_list = "\n".join(f"{k} = {v}" for k, v in vars_dict.items())
        return [
            TextContent(
                type="text",
                text=f"Current session variables:\n\n{var_list}"
            )
        ]
    # def exec_docker(self, script: str):
    #     client = docker.from_env()
    #     with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_script:
    #         tmp_script.write(script)
    #         tmp_script_path = tmp_script.name
    #     container = None
    #     try 
        
    #     return None