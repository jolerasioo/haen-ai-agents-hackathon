import azure.functions as func
import logging
import os
import json
import sys
print("\n\n\n\n\n--- Python sys.path used by Functions runtime: ---") # <-- Add this line
print(sys.path) # <-- Add this line
print("-------------------------------------------------\n\n\n\n\n") # <-- Add this line
import jsonref
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails, ToolSet, FunctionTool
from dotenv import load_dotenv
from typing import Callable, Set, Dict, List, Optional, Any

from mock_cosmosdb_service import get_all_citizen_data

load_dotenv()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="coms_ai_agent_func")
def coms_ai_agent_func(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    message = None # Initialize message
    chat_history = None # Initialize chat_history

    try:
        req_body = req.get_json()
        logging.info(f"Request body JSON: {req_body}")
    except ValueError:
        logging.error("Request body is not valid JSON")
        return func.HttpResponse(
             "Please pass a valid JSON object in the request body",
             status_code=400
        )

    chat_history = req_body.get('chatHistory')
    logging.info(f"Chat history from body: {chat_history}")
   
    message = chat_history[-1].get('content')
    logging.info(f"Message from chat history: {message}")
    
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=os.environ["PROJECT_CONNECTION_STRING"],
    )

    # open the OpenAPI spec file
    with open('.\data\communications_api.json', 'r') as f:
        openapi_spec = jsonref.loads(f.read())
    
    # read the system prompt file
    with open('.\data\system_prompt.txt', 'r') as f:
        system_prompt: str = f.read()

    logging.info(f"System prompt read: {system_prompt}")

    # Create Auth object for the OpenApiTool (note that connection or managed identity auth setup requires additional setup in Azure)
    auth = OpenApiAnonymousAuthDetails()

    # Initialize agent OpenAPI tool using the read in OpenAPI spec
    openapi = OpenApiTool(name="send_alert_communications", spec=openapi_spec, description="Send new alert via SMS for general citizen and outbound phone call for vulnerable citizens", auth=auth)
    logging.info(f"OpenAPI tool created: {openapi.definitions}")
    ## Citizen data tool
    #data_function: Set[Callable[..., Any]] = {
    #    "get_all_citizen_data": get_all_citizen_data,
    #}
#
    #data_tool = FunctionTool(get_all_citizen_data)
    #
    #toolset = ToolSet(data_tool)
    

    # Create agent with OpenAPI tool and process assistant run
    try:
        with project_client:
            agent = project_client.agents.create_agent(
                model="gpt-4o",
                name="alerts-agent",
                instructions=system_prompt,
                tools=openapi.definitions #.append(data_tool)
            )
            logging.info(f"Created agent, ID: {agent.id}")

            # Create thread for communication
            thread = project_client.agents.create_thread()
            logging.info(f"Created thread, ID: {thread.id}")
    except Exception as e:
        logging.error(f"Error creating agent or thread: {e}")
        return func.HttpResponse(
            "Error creating agent or thread",
            status_code=500
        )


    # Create message to thread
    try:
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=message,
        )
        logging.info(f"Created message, ID: {message.id}")
    except Exception as e:
        logging.error(f"Error creating message: {e}")
        return func.HttpResponse(
            "Error creating message",
            status_code=500
        )

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    logging.info(f"Run finished with status: {run.status}")

    if run.status == "failed":
        logging.error(f"Run failed: {run.last_error}")

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    logging.info(f"Messages: {messages}")

    logging.info(f"Assistant response: {messages.get_last_message_by_role('assistant').text.value}")

    # Delete the assistant when done
    #project_client.agents.delete_agent(agent.id)
    #print("Deleted agent")