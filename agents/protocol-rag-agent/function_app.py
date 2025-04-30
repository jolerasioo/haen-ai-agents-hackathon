import azure.functions as func
import datetime
import json
import logging
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchTool, MessageRole

app = func.FunctionApp()

@app.route(route="protocolragagent", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def protocolragagent(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    body = req.get_body().decode("utf-8")
    body = json.loads(body)
    logging.info(f"Request body: {body}")
    msg = body.get("message")
    if not msg:
        logging.info("No message found in the request body")
        msg = "What are the main evacuation options for valencia?"
    logging.info(f"Message from request: {msg}")
    # connect to the AI project using the connection string from environment variables

    connection_string ="swedencentral.api.azureml.ms;ee8aa11d-63ce-44df-a2e9-35026390a338;rg-adminai;admin-7475"
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=connection_string,
    )

    # retrieve or create the agent
    agent = get_or_create_agent(project_client, "asst_4y8aW22JRwnRTdXk8ouhGDCu")

    # Create a thread
    thread = project_client.agents.create_thread()
    logging.info(f"Created thread, thread ID: {thread.id}")


    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=msg
    )

    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id
    )

    answer = project_client.agents.list_messages(thread_id=thread.id).get_last_text_message_by_role(MessageRole.AGENT)
    logging.info(f"Answer from agent: {answer}")

    return answer.text.value



def get_or_create_agent(ai_proj_client: AIProjectClient, agent_id: str, index_name: str = "vector-1746009530224"):
    try:
        agent = ai_proj_client.agents.get_agent(agent_id=agent_id)
        logging.info(f"Agent {agent_id} retrieved.")
        return agent
    except:
        logging.info(f"Creating new agent: {agent_id}.")
        
        # get connection id for AI Search Service
        conn_list = ai_proj_client.connections._list_connections()["value"]
        for conn in conn_list:
            if conn.get("name") == "aisearchbasic":
                conn_id = conn.get("id")
                logging.info(f"AI Search connection ID: {conn_id}")
                break

        ai_search = AzureAISearchTool(
            index_connection_id=conn_id, index_name=index_name,
            query_type="vector_semantic_hybrid"
        )

        with open('.\data\system_prompt.txt', 'r') as f:
            system_prompt: str = f.read()   


        agent = ai_proj_client.agents.create_agent(
            model="gpt-4o",
            name="protocol-rag-agent",
            instructions=system_prompt,
            tools=ai_search.definitions,
            tool_resources = ai_search.resources,
        )
        logging.info(f"Agent {agent_id} created.")
        return agent
    