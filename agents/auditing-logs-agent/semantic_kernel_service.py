import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from dotenv import load_dotenv

from models import AuditLog, LogQueryParams, LogCategory, LogSeverity

# Load environment variables
load_dotenv()


class SemanticKernelService:
    def __init__(self):
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()
        
        # Add Azure OpenAI chat completion service
        self.kernel.add_chat_service(
            "chat-completion",
            AzureChatCompletion(
                deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"]
            )
        )
        
        # Create semantic functions
        self._create_semantic_functions()
    
    def _create_semantic_functions(self):
        """Create semantic functions for log analysis"""
        # Create a plugin for log analysis
        self.log_plugin = self.kernel.create_semantic_function(
            """
            You are an AI assistant specialized in analyzing audit logs.
            
            Analyze the following audit logs and provide a summary of the activities:
            
            {{$logs}}
            
            Focus on:
            1. Key actions performed
            2. Notable security events
            3. Unusual activities or patterns
            4. Timeline of events
            5. Potential issues or concerns
            
            Return your analysis in a clear, organized format.
            """,
            plugin_name="AuditLogPlugin",
            function_name="analyze_logs",
            description="Analyzes audit logs and provides a summary"
        )
        
        # Create function for generating log descriptions
        self.description_generator = self.kernel.create_semantic_function(
            """
            Generate a concise, descriptive summary for an audit log entry with the following details:
            
            - Action: {{$action}}
            - Source: {{$source}}
            - Category: {{$category}}
            - User ID: {{$user_id}}
            - Details: {{$details}}
            
            The description should be professional, clear, and convey the important information about this action or event.
            Limit your response to a single sentence of less than 100 characters.
            """,
            plugin_name="AuditLogPlugin",
            function_name="generate_description",
            description="Generates a concise description for an audit log entry"
        )
        
        # Create function for classifying log severity
        self.severity_classifier = self.kernel.create_semantic_function(
            """
            Analyze the following audit log details and classify its severity level as one of: INFO, WARNING, ERROR, or CRITICAL.
            
            - Action: {{$action}}
            - Source: {{$source}}
            - Description: {{$description}}
            - Details: {{$details}}
            
            Consider the following guidelines:
            - INFO: Routine operations, successful actions, informational events
            - WARNING: Potential issues that don't affect functionality, suspicious activity, unusual patterns
            - ERROR: Failed operations, errors that impact functionality, security policy violations
            - CRITICAL: Severe security breaches, system failures, unauthorized access, data loss
            
            Return only the severity level as a single word (INFO, WARNING, ERROR, or CRITICAL).
            """,
            plugin_name="AuditLogPlugin",
            function_name="classify_severity",
            description="Classifies the severity of an audit log entry"
        )
    
    async def analyze_logs(self, logs: List[AuditLog]) -> str:
        """Analyze audit logs using Semantic Kernel"""
        if not logs:
            return "No logs to analyze."
        
        # Convert logs to a formatted string
        logs_str = "\n\n".join([
            f"ID: {log.id}\n"
            f"Timestamp: {log.timestamp.isoformat()}\n"
            f"Category: {log.category.value}\n"
            f"Severity: {log.severity.value}\n"
            f"Source: {log.source}\n"
            f"Action: {log.action}\n"
            f"Description: {log.description}\n"
            f"User ID: {log.user_id or 'N/A'}\n"
            f"Details: {log.details or 'N/A'}"
            for log in logs
        ])
        
        # Call the log analysis function
        context = self.kernel.create_context()
        context["logs"] = logs_str
        
        result = await self.log_plugin.invoke_async(context=context)
        
        return str(result)
    
    async def generate_log_description(self, action: str, source: str, category: str, user_id: str = None, details: Dict[str, Any] = None) -> str:
        """Generate a description for an audit log entry"""
        context = self.kernel.create_context()
        context["action"] = action
        context["source"] = source
        context["category"] = category
        context["user_id"] = user_id or "N/A"
        context["details"] = str(details) if details else "N/A"
        
        result = await self.description_generator.invoke_async(context=context)
        
        return str(result).strip()
    
    async def classify_log_severity(self, action: str, source: str, description: str, details: Dict[str, Any] = None) -> LogSeverity:
        """Classify the severity of an audit log entry"""
        context = self.kernel.create_context()
        context["action"] = action
        context["source"] = source
        context["description"] = description
        context["details"] = str(details) if details else "N/A"
        
        result = await self.severity_classifier.invoke_async(context=context)
        severity_str = str(result).strip().upper()
        
        try:
            return LogSeverity(severity_str)
        except ValueError:
            # Default to INFO if classification fails
            return LogSeverity.INFO