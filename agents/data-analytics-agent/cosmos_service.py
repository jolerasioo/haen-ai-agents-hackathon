import os
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as cosmos_exceptions
from azure.cosmos.partition_key import PartitionKey
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CosmosDBService:
    def __init__(self):
        # Initialize Cosmos client
        self.client = cosmos_client.CosmosClient(
            url=os.environ["COSMOS_ENDPOINT"],
            credential=os.environ["COSMOS_KEY"]
        )
        self.database_name = os.environ["COSMOS_DATABASE"]
        
        # Get the database
        try:
            self.database = self.client.get_database_client(self.database_name)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            print(f"Database '{self.database_name}' not found")
            self.database = None
    
    def get_database_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get the schema of all containers in the database.
        Returns a dictionary with container names as keys and a list of columns as values.
        """
        if not self.database:
            return {"error": "Database not found"}
        
        schema = {}
        
        # Get all containers
        containers = list(self.database.list_containers())
        
        for container_info in containers:
            container_name = container_info['id']
            container = self.database.get_container_client(container_name)
            
            # Get a sample item to infer schema
            items = list(container.query_items(
                query="SELECT TOP 1 * FROM c",
                enable_cross_partition_query=True
            ))
            
            if items:
                sample_item = items[0]
                columns = []
                
                # Process the sample item to extract column info
                for key, value in sample_item.items():
                    # Skip system properties
                    if key.startswith('_'):
                        continue
                    
                    if isinstance(value, dict):
                        data_type = "object"
                    elif isinstance(value, list):
                        data_type = "array"
                    elif isinstance(value, bool):
                        data_type = "boolean"
                    elif isinstance(value, int):
                        data_type = "integer"
                    elif isinstance(value, float):
                        data_type = "float"
                    elif isinstance(value, str):
                        try:
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                            data_type = "datetime"
                        except ValueError:
                            data_type = "string"
                    else:
                        data_type = str(type(value).__name__)
                    
                    columns.append({
                        "name": key,
                        "type": data_type
                    })
                
                schema[container_name] = columns
            else:
                schema[container_name] = []
        
        return schema
    
    def run_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Run a SQL query against Cosmos DB.
        """
        if not self.database:
            return {"error": "Database not found"}
        
        if not sql_query.strip():
            return {"error": "SQL query is empty"}
        
        try:
            # Parse the SQL query to determine the container
            # This is a simple parser and might not work for complex queries
            query_parts = sql_query.split()
            container_name = None
            
            # Find the FROM clause
            for i, part in enumerate(query_parts):
                if part.upper() == "FROM" and i + 1 < len(query_parts):
                    container_name = query_parts[i + 1].rstrip(',;')
                    break
            
            if not container_name:
                return {"error": "Could not determine container name from query"}
            
            # Get the container
            try:
                container = self.database.get_container_client(container_name)
            except cosmos_exceptions.CosmosResourceNotFoundError:
                return {"error": f"Container '{container_name}' not found"}
            
            # Execute the query
            items = list(container.query_items(
                query=sql_query,
                enable_cross_partition_query=True
            ))
            
            # Convert to pandas DataFrame for analysis
            if items:
                df = pd.DataFrame(items)
                
                # Remove system properties
                for col in list(df.columns):
                    if col.startswith('_'):
                        df.drop(col, axis=1, inplace=True)
                
                # Generate summary statistics
                summary = {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                }
                
                # Get column statistics
                column_stats = {}
                for col in df.columns:
                    col_data = df[col]
                    
                    # Skip complex types
                    if col_data.dtype == 'object' and all(isinstance(x, (dict, list)) for x in col_data if x is not None):
                        continue
                    
                    stats = {
                        "dtype": str(col_data.dtype)
                    }
                    
                    # Add numeric statistics
                    if pd.api.types.is_numeric_dtype(col_data):
                        stats.update({
                            "min": col_data.min(),
                            "max": col_data.max(),
                            "mean": col_data.mean(),
                            "median": col_data.median(),
                            "std": col_data.std(),
                            "null_count": col_data.isna().sum(),
                        })
                    # Add string statistics
                    elif pd.api.types.is_string_dtype(col_data):
                        stats.update({
                            "unique_count": col_data.nunique(),
                            "null_count": col_data.isna().sum(),
                            "sample_values": col_data.dropna().sample(min(5, len(col_data.dropna()))).tolist() if not col_data.empty else []
                        })
                    # Add datetime statistics
                    elif pd.api.types.is_datetime64_dtype(col_data):
                        stats.update({
                            "min": col_data.min(),
                            "max": col_data.max(),
                            "null_count": col_data.isna().sum(),
                        })
                    
                    column_stats[col] = stats
                
                # Add sample data
                sample_data = df.head(5).to_dict(orient='records')
                
                result = {
                    "success": True,
                    "query": sql_query,
                    "summary": summary,
                    "column_stats": column_stats,
                    "sample_data": sample_data,
                    "full_result": items,
                }
                
                return result
            else:
                return {
                    "success": True,
                    "query": sql_query,
                    "message": "Query executed successfully but returned no results",
                    "full_result": []
                }
        
        except Exception as e:
            return {
                "success": False,
                "query": sql_query,
                "error": str(e)
            }
    
    def run_analytical_query(self, sql_query: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Run a SQL query and provide analytical insights.
        
        Parameters:
        - sql_query: The SQL query to execute
        - analysis_type: Type of analysis to perform (summary, trend, distribution, correlation)
        
        Returns:
        - Dictionary containing analysis results
        """
        # Run the base query
        query_result = self.run_sql_query(sql_query)
        
        if not query_result.get("success", False):
            return query_result
        
        if query_result.get("full_result") and len(query_result["full_result"]) > 0:
            df = pd.DataFrame(query_result["full_result"])
            
            # Remove system properties
            for col in list(df.columns):
                if col.startswith('_'):
                    df.drop(col, axis=1, inplace=True)
            
            # Perform different types of analysis
            if analysis_type == "summary":
                # Already done in run_sql_query
                pass
            
            elif analysis_type == "trend":
                # Identify datetime columns for trend analysis
                datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_dtype(df[col]) or 
                                (pd.api.types.is_string_dtype(df[col]) and 
                                 col.lower().find('date') >= 0 or col.lower().find('time') >= 0)]
                
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                
                trend_analysis = {}
                
                if datetime_cols and numeric_cols:
                    datetime_col = datetime_cols[0]  # Use the first datetime column
                    
                    for numeric_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                        try:
                            # Convert to datetime if it's a string
                            if pd.api.types.is_string_dtype(df[datetime_col]):
                                df[datetime_col] = pd.to_datetime(df[datetime_col], errors='coerce')
                            
                            # Sort by the datetime column
                            df_sorted = df.sort_values(by=datetime_col)
                            
                            # Group by day and calculate statistics
                            df_grouped = df_sorted.groupby(df_sorted[datetime_col].dt.date)[numeric_col].agg(['count', 'min', 'max', 'mean'])
                            
                            trend_data = []
                            for date, row in df_grouped.iterrows():
                                trend_data.append({
                                    'date': date.isoformat(),
                                    'count': int(row['count']),
                                    'min': float(row['min']),
                                    'max': float(row['max']),
                                    'mean': float(row['mean'])
                                })
                            
                            trend_analysis[numeric_col] = {
                                'time_column': datetime_col,
                                'data': trend_data
                            }
                        except Exception as e:
                            trend_analysis[numeric_col] = {
                                'error': str(e)
                            }
                
                query_result['trend_analysis'] = trend_analysis
            
            elif analysis_type == "distribution":
                # Analyze distribution of numeric columns
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                
                distribution_analysis = {}
                
                for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                    try:
                        # Calculate percentiles
                        percentiles = [0, 10, 25, 50, 75, 90, 100]
                        percentile_values = [float(x) for x in df[col].quantile([p/100 for p in percentiles]).values]
                        
                        # Create histogram data
                        hist_data, bin_edges = np.histogram(df[col].dropna(), bins=10)
                        
                        histogram = []
                        for i in range(len(hist_data)):
                            histogram.append({
                                'bin_min': float(bin_edges[i]),
                                'bin_max': float(bin_edges[i+1]),
                                'count': int(hist_data[i])
                            })
                        
                        distribution_analysis[col] = {
                            'percentiles': {str(p): v for p, v in zip(percentiles, percentile_values)},
                            'histogram': histogram
                        }
                    except Exception as e:
                        distribution_analysis[col] = {
                            'error': str(e)
                        }
                
                query_result['distribution_analysis'] = distribution_analysis
            
            elif analysis_type == "correlation":
                # Calculate correlation between numeric columns
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                
                if len(numeric_cols) >= 2:
                    try:
                        corr_matrix = df[numeric_cols].corr().to_dict()
                        
                        # Format correlation data
                        correlation_data = []
                        for col1 in numeric_cols:
                            for col2 in numeric_cols:
                                if col1 != col2:
                                    correlation_data.append({
                                        'column1': col1,
                                        'column2': col2,
                                        'correlation': float(corr_matrix[col1][col2])
                                    })
                        
                        # Sort by absolute correlation value, descending
                        correlation_data.sort(key=lambda x: abs(x['correlation']), reverse=True)
                        
                        query_result['correlation_analysis'] = correlation_data
                    except Exception as e:
                        query_result['correlation_analysis'] = {
                            'error': str(e)
                        }
                else:
                    query_result['correlation_analysis'] = {
                        'message': 'Need at least 2 numeric columns for correlation analysis'
                    }
        
        return query_result