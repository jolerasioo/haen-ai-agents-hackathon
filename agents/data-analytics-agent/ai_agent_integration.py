import os
import json
from typing import Dict, List, Any, Optional
import logging

from agent_service import DataAnalyticsAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AiAgentIntegration:
    def __init__(self):
        # Initialize the data analytics agent
        self.data_analytics_agent = DataAnalyticsAgent()
        
        # System messages for AI agent
        self.system_messages = {
            "get_schema": """
You are a Data Analytics Assistant specialized in analyzing SQL database schema.
Analyze the provided database schema and help the user understand:
1. What tables/containers are available
2. What columns each table/container has
3. The data types of each column
4. Potential relationships between tables/containers
5. Recommendations for queries based on the available schema

Present the information in a clear, concise format and be ready to suggest SQL queries
that would be useful for analyzing this data.
""",
            "run_query": """
You are a Data Analytics Assistant specialized in analyzing SQL query results.
Analyze the provided query results and help the user understand:
1. Overall statistics (row count, value ranges, etc.)
2. Distribution of values
3. Notable patterns or outliers
4. Relevant business insights based on the data domain

Keep your responses concise and informative, focusing on what would be most valuable to the user.
Present the most important insights first, followed by supporting details.
For numerical data, include key statistics like min, max, average, and distribution.
For categorical data, include frequency distribution and notable categories.
When appropriate, suggest additional analyses that might yield valuable insights.
"""
        }
    
    async def process_get_schema_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the GetDbSchema tool call from the AI Agent.
        
        Arguments: None
        Returns: Database schema information
        """
        try:
            # Get the database schema
            schema = self.data_analytics_agent.get_database_schema()
            
            # Generate a human-readable summary
            summary = self.data_analytics_agent.summarize_schema(schema)
            
            return {
                "schema": schema,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error processing GetDbSchema tool: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def process_run_sql_query_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the RunSqlQuery tool call from the AI Agent.
        
        Arguments:
        - query: SQL query to execute
        - analysis_type: Type of analysis to perform (optional)
        
        Returns: Query results and analysis
        """
        try:
            # Extract arguments
            query = arguments.get("query")
            analysis_type = arguments.get("analysis_type", "summary")
            
            if not query:
                return {
                    "error": "SQL query is required"
                }
            
            # Run the query
            if analysis_type and analysis_type != "summary":
                results = self.data_analytics_agent.execute_analytical_query(query, analysis_type)
            else:
                results = self.data_analytics_agent.execute_sql_query(query)
            
            # Generate a human-readable summary
            summary = self.data_analytics_agent.analyze_results(results)
            
            return {
                "query": query,
                "results": results,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error processing RunSqlQuery tool: {str(e)}")
            return {
                "error": str(e)
            }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get the tool definitions for the Azure AI Agent Service.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "GetDbSchema",
                    "description": "Get the database schema for the available data sources.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RunSqlQuery",
                    "description": "Run a SQL query against the database and get the results with analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute against the database."
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "Type of analysis to perform (summary, trend, distribution, correlation).",
                                "enum": ["summary", "trend", "distribution", "correlation"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]