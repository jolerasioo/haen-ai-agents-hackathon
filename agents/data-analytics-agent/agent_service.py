import os
import json
from typing import Dict, List, Any, Optional
import pandas as pd

from dotenv import load_dotenv

from cosmos_service import CosmosDBService

# Load environment variables
load_dotenv()

class DataAnalyticsAgent:
    def __init__(self):
        # Initialize Cosmos DB service
        self.cosmos_service = CosmosDBService()
        
        # Load system prompts
        self.system_prompt = """
You are a Data Analytics Assistant specialized in analyzing data from a Cosmos DB database.
Your task is to help users understand their data by summarizing query results and providing insights.

When analyzing data, consider the following aspects:
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
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get the schema of the database using the Cosmos DB service.
        """
        return self.cosmos_service.get_database_schema()
    
    def execute_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query using the Cosmos DB service.
        """
        return self.cosmos_service.run_sql_query(sql_query)
    
    def execute_analytical_query(self, sql_query: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Execute an analytical query using the Cosmos DB service.
        """
        return self.cosmos_service.run_analytical_query(sql_query, analysis_type)
    
    def analyze_results(self, query_results: Dict[str, Any]) -> str:
        """
        Analyze query results and provide a human-readable summary.
        
        This would typically be done through the AI agent, but here we implement
        a simplified version of result analysis.
        """
        if not query_results.get("success", False):
            return f"ERROR: {query_results.get('error', 'Unknown error occurred')}"
        
        if "full_result" not in query_results or not query_results["full_result"]:
            return "The query did not return any results."
        
        # Basic summary
        summary = []
        summary.append(f"Query returned {query_results['summary']['row_count']} rows with {query_results['summary']['column_count']} columns.")
        
        # Column analysis
        col_insights = []
        if "column_stats" in query_results:
            for col_name, stats in query_results["column_stats"].items():
                col_type = stats.get("dtype", "unknown")
                
                # For numeric columns
                if "mean" in stats:
                    col_insights.append(
                        f"- Column '{col_name}' (numeric): range {stats['min']} to {stats['max']}, " +
                        f"average {stats['mean']:.2f}, median {stats['median']:.2f}"
                    )
                # For string columns
                elif "unique_count" in stats:
                    col_insights.append(
                        f"- Column '{col_name}' (string): {stats['unique_count']} unique values, " +
                        f"{stats['null_count']} null values"
                    )
                # For datetime columns
                elif "min" in stats and col_type.startswith("datetime"):
                    col_insights.append(
                        f"- Column '{col_name}' (datetime): range from {stats['min']} to {stats['max']}"
                    )
        
        if col_insights:
            summary.append("\nColumn Analysis:")
            summary.extend(col_insights)
        
        # Sample data
        if "sample_data" in query_results and query_results["sample_data"]:
            summary.append("\nSample Data (first 5 rows):")
            
            # Create a formatted sample table
            df = pd.DataFrame(query_results["sample_data"])
            
            # Limit column width for display
            with pd.option_context('display.max_colwidth', 30):
                table_str = df.to_string(index=False)
            
            summary.append(f"```\n{table_str}\n```")
        
        # Trend analysis
        if "trend_analysis" in query_results:
            for col, trend_data in query_results["trend_analysis"].items():
                if "error" not in trend_data:
                    summary.append(f"\nTrend Analysis for '{col}':")
                    summary.append(f"- Time series based on '{trend_data['time_column']}'")
                    
                    if trend_data["data"]:
                        first_point = trend_data["data"][0]
                        last_point = trend_data["data"][-1]
                        
                        change = last_point["mean"] - first_point["mean"]
                        pct_change = (change / first_point["mean"]) * 100 if first_point["mean"] != 0 else float('inf')
                        
                        direction = "increased" if change > 0 else "decreased"
                        
                        summary.append(
                            f"- Value has {direction} from {first_point['mean']:.2f} to {last_point['mean']:.2f} " +
                            f"({abs(pct_change):.1f}% {direction}) over the time period"
                        )
        
        # Correlation analysis
        if "correlation_analysis" in query_results and isinstance(query_results["correlation_analysis"], list):
            if query_results["correlation_analysis"]:
                summary.append("\nCorrelation Analysis:")
                
                # Show top 3 correlations
                for i, corr in enumerate(query_results["correlation_analysis"][:3]):
                    summary.append(
                        f"- {corr['column1']} and {corr['column2']}: {corr['correlation']:.2f} correlation"
                    )
        
        return "\n".join(summary)
    
    def summarize_schema(self, schema: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Generate a human-readable summary of the database schema.
        """
        if "error" in schema:
            return f"ERROR: {schema['error']}"
        
        if not schema:
            return "The database does not contain any containers."
        
        summary = ["Database Schema:"]
        
        for container_name, columns in schema.items():
            summary.append(f"\nContainer: {container_name}")
            
            if not columns:
                summary.append("  (Empty container or no schema information available)")
                continue
            
            summary.append("  Columns:")
            for column in columns:
                summary.append(f"  - {column['name']} ({column['type']})")
        
        return "\n".join(summary)