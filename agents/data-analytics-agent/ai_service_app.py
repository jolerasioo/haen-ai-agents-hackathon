import os
import json
import logging
from typing import Dict, List, Any, Optional

import azure.functions as func
from azure.ai.assistant import Assistant, Message, ThreadMessage, Run

from dotenv import load_dotenv
from ai_agent_integration import AiAgentIntegration

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI agent integration
ai_agent_integration = AiAgentIntegration()

# Create function app
app = func.FunctionApp()

@app.route(route="AiAgentProcessor", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def process_ai_agent_request(req: func.HttpRequest) -> func.HttpResponse:
    """
    Process a request from the Azure AI Agent Service.
    """
    logger.info("Processing AI agent request")
    
    try:
        # Get request body
        req_body = req.get_json()
        
        # Extract request type
        request_type = req_body.get("type")
        
        if request_type == "tool_call":
            # Handle tool call request
            tool_call = req_body.get("tool_call", {})
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
            
            if tool_name == "GetDbSchema":
                result = await ai_agent_integration.process_get_schema_tool(arguments)
            elif tool_name == "RunSqlQuery":
                result = await ai_agent_integration.process_run_sql_query_tool(arguments)
            else:
                return func.HttpResponse(
                    json.dumps({"error": f"Unknown tool: {tool_name}"}),
                    status_code=400,
                    mimetype="application/json"
                )
            
            return func.HttpResponse(
                json.dumps(result),
                status_code=200,
                mimetype="application/json"
            )
        
        elif request_type == "message":
            # Handle message request
            message = req_body.get("message", {})
            content = message.get("content", "")
            
            # This is a simple echo handler
            # In a real application, you would process the message and generate a response
            return func.HttpResponse(
                json.dumps({
                    "response": f"Received message: {content}",
                    "suggested_tools": ["GetDbSchema", "RunSqlQuery"]
                }),
                status_code=200,
                mimetype="application/json"
            )
        
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown request type: {request_type}"}),
                status_code=400,
                mimetype="application/json"
            )
    
    except Exception as e:
        logger.error(f"Error processing AI agent request: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="GetToolDefinitions", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
async def get_tool_definitions(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get the tool definitions for the Azure AI Agent Service.
    """
    logger.info("Getting tool definitions")
    
    try:
        # Get tool definitions
        tool_definitions = ai_agent_integration.get_tool_definitions()
        
        return func.HttpResponse(
            json.dumps({"tools": tool_definitions}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logger.error(f"Error getting tool definitions: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )