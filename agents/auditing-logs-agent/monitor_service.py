import os
import json
from datetime import datetime
from typing import Dict, Any, List

from azure.monitor.ingestion import LogsIngestionClient
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from models import AuditLog, LogSeverity

# Load environment variables
load_dotenv()


class MonitorService:
    def __init__(self):
        # Initialize Azure Monitor clients
        self.credential = DefaultAzureCredential()
        self.ingestion_client = LogsIngestionClient(credential=self.credential)
        self.query_client = LogsQueryClient(credential=self.credential)
        
        self.workspace_id = os.environ["AZURE_MONITOR_WORKSPACE_ID"]
        self.workspace_key = os.environ["AZURE_MONITOR_WORKSPACE_KEY"]
        
        # Define the log type (table name)
        self.log_type = "AuditLogs_CL"
    
    async def send_log_to_monitor(self, log: AuditLog):
        """Send an audit log to Azure Monitor"""
        # Convert the log to a dictionary
        log_dict = log.dict()
        
        # Convert datetime to string
        log_dict["timestamp"] = log_dict["timestamp"].isoformat()
        
        # Convert enum values to strings
        log_dict["category"] = log_dict["category"].value
        log_dict["severity"] = log_dict["severity"].value
        
        # Add severity mapping for Azure Monitor
        severity_map = {
            LogSeverity.INFO.value: 1,
            LogSeverity.WARNING.value: 2,
            LogSeverity.ERROR.value: 3,
            LogSeverity.CRITICAL.value: 4
        }
        log_dict["severityLevel"] = severity_map.get(log_dict["severity"], 1)
        
        # Create body for ingestion
        body = [log_dict]
        
        # Send log to Azure Monitor
        self.ingestion_client.upload(
            rule_id=self.workspace_id,
            stream_name=self.log_type,
            logs=body
        )
    
    async def query_monitor_logs(self, query: str, timespan: str = "P1D") -> List[Dict[str, Any]]:
        """Query logs from Azure Monitor"""
        # Execute the query
        response = self.query_client.query_workspace(
            workspace_id=self.workspace_id,
            query=query,
            timespan=timespan
        )
        
        # Process the query results
        if not response or not response.tables:
            return []
        
        table = response.tables[0]
        
        # Convert the results to a list of dictionaries
        results = []
        for row in table.rows:
            result = {}
            for i, column in enumerate(table.columns):
                result[column.name] = row[i]
            results.append(result)
        
        return results


class SentinelService:
    def __init__(self):
        # Initialize Azure Sentinel (Log Analytics) client
        self.credential = DefaultAzureCredential()
        self.query_client = LogsQueryClient(credential=self.credential)
        
        self.workspace_id = os.environ["AZURE_SENTINEL_WORKSPACE_ID"]
        self.log_type = "AuditLogs_CL"  # Using the same log type as Monitor
    
    async def query_sentinel(self, query: str, timespan: str = "P1D") -> List[Dict[str, Any]]:
        """Query logs from Azure Sentinel (Log Analytics)"""
        # Execute the query
        response = self.query_client.query_workspace(
            workspace_id=self.workspace_id,
            query=query,
            timespan=timespan
        )
        
        # Process the query results
        if not response or not response.tables:
            return []
        
        table = response.tables[0]
        
        # Convert the results to a list of dictionaries
        results = []
        for row in table.rows:
            result = {}
            for i, column in enumerate(table.columns):
                result[column.name] = row[i]
            results.append(result)
        
        return results
    
    async def get_security_incidents(self, timespan: str = "P7D") -> List[Dict[str, Any]]:
        """Get security incidents from Azure Sentinel"""
        # Query for security incidents
        query = f"""
        SecurityIncident
        | where TimeGenerated > ago({timespan})
        | project IncidentNumber, Title, Severity, Status, CreatedTime, LastModifiedTime
        | order by CreatedTime desc
        """
        
        return await self.query_sentinel(query, timespan)