import azure.functions as func
import datetime
import json
import logging
import os
import asyncio
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.processes.local_runtime import KernelProcessEvent, start
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()

@app.route(route="authority_action_func", auth_level=func.AuthLevel.ANONYMOUS)
def authority_action_func(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info(f"Request body: {req.get_body()}")

    ai_proj_client = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=os.environ["PROJECT_CONNECTION_STRING"],
    )

    # get agents from the AI project
    try:
        protocol_agent = get_agent_from_ai_proj(ai_proj_client, os.environ["PROTOCOL_AGENT_ID"])
        audit_agent = get_agent_from_ai_proj(ai_proj_client, os.environ["AUDIT_AGENT_ID"])
        action_api_agent = get_agent_from_ai_proj(ai_proj_client, os.environ["ACTION_API_AGENT_ID"])
        logging.info(f"Agents retrieved: {protocol_agent.name}, {audit_agent.name}, {action_api_agent.name}")
    except Exception as e:
        logging.error(f"Error retrieving agents: {e}")
        return func.HttpResponse(
            "Error retrieving agents",
            status_code=500
        )
    
    ####
    # process framework
    #####
    process_builder = ProcessBuilder(name="AuthorityActionProcess")

    # steps
    get_latest_updates_step = process_builder.add_step(audit_agent)
    analyze_protocol_step = process_builder.add_step(protocol_agent)
    explore_actions_step = process_builder.add_step(action_api_agent)

    # process flow
    process_builder.on_input_event(start).send_event_to(get_latest_updates_step)
    get_latest_updates_step.on_function_result().send_event_to(analyze_protocol_step)
    analyze_protocol_step.on_function_result().send_event_to(explore_actions_step) # add human in the loop when new feature becomes available
    explore_actions_step.on_function_result().end_process()
    logging.info("Process completed successfully.")










def get_agent_from_ai_proj(client: AIProjectClient, agent_id: str):
    # Initialize the AIProjectClient with DefaultAzureCredential
    
    # Call the agent service to get the list of agents
    agent = client.agents.get_agent(agent_id=agent_id)
    return agent
    

