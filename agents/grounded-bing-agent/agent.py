import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import BingGroundingTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BingGroundedAgent:
    def __init__(self):
        # Initialize the client with connection string
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        # Get the Bing connection
        self.bing_connection = self.project_client.connections.get(
            connection_name=os.environ["BING_CONNECTION_NAME"]
        )
        
        # Initialize the Bing tool
        self.bing = BingGroundingTool(connection_id=self.bing_connection.id)
        
        # Create the agent with Bing tool
        self.agent = self.project_client.agents.create_agent(
            model="gpt-4o",
            name="bing-grounded-agent",
            instructions="You are a helpful assistant that uses Bing search to provide up-to-date information.",
            tools=self.bing.definitions
        )
    
    def get_agent_id(self):
        return self.agent.id
    
    def create_thread(self):
        return self.project_client.agents.create_thread()
    
    def send_message(self, thread_id, content):
        message = self.project_client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=content
        )
        return message
    
    def process_query(self, thread_id, query):
        # Add user message
        self.send_message(thread_id, query)
        
        # Create and process the run
        run = self.project_client.agents.create_and_process_run(
            thread_id=thread_id,
            agent_id=self.agent.id
        )
        
        # Get messages from the thread (including the agent's response)
        messages = self.project_client.agents.list_messages(thread_id=thread_id)
        
        # Return the latest message from the assistant
        for message in reversed(list(messages)):
            if message.role == "assistant":
                return message.content[0].text
                
        return "No response received from the agent."