"""
BigQuery Client Module
Handles BigQuery connection and query execution with cost tracking
"""

import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from typing import Tuple, Optional


def get_bigquery_client() -> bigquery.Client:
    """
    Initialize and return BigQuery client using Streamlit secrets
    
    Returns:
        bigquery.Client: Authenticated BigQuery client
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["bigquery"]
        )
        client = bigquery.Client(credentials=credentials)
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize BigQuery client: {str(e)}")
        st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def execute_query(query: str) -> Tuple[pd.DataFrame, float]:
    """
    Execute BigQuery query and return results with bytes processed
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        Tuple[pd.DataFrame, float]: Query results and bytes processed (in GB)
    """
    client = get_bigquery_client()
    
    try:
        with st.spinner("🔄 Executing BigQuery query..."):
            # Configure query job
            job_config = bigquery.QueryJobConfig()
            
            # Execute query
            query_job = client.query(query, job_config=job_config)
            
            # Get results
            results = query_job.result()
            df = results.to_dataframe()
            
            # Get bytes processed
            bytes_processed = query_job.total_bytes_processed or 0
            gb_processed = bytes_processed / (1024 ** 3)  # Convert to GB
            
            return df, gb_processed
            
    except Exception as e:
        st.error(f"❌ Query execution failed: {str(e)}")
        st.code(query, language="sql")
        raise e


def get_distinct_categories() -> list:
    """
    Get distinct categories from product master table
    
    Returns:
        list: List of unique category names
    """
    query = f"""
    SELECT DISTINCT CategoryName
    FROM `commercial-prod-375618.pcb_data_prod.PCB_PRODUCT_MASTER`
    WHERE CategoryName IS NOT NULL
    ORDER BY CategoryName
    """
    
    try:
        df, _ = execute_query(query)
        return df['CategoryName'].tolist()
    except Exception:
        return []


def get_categories() -> list:
    """
    Alias for get_distinct_categories for compatibility
    
    Returns:
        list: List of unique category names
    """
    return get_distinct_categories()


def get_subcategories(category: str) -> list:
    """
    Get distinct subcategories for a specific category
    
    Args:
        category (str): Category name to filter by
        
    Returns:
        list: List of unique subcategory names
    """
    # Escape single quotes
    category_escaped = category.replace("'", "''")
    
    query = f"""
    SELECT DISTINCT SubCategoryName
    FROM `commercial-prod-375618.pcb_data_prod.PCB_PRODUCT_MASTER`
    WHERE CategoryName = '{category_escaped}'
      AND SubCategoryName IS NOT NULL
    ORDER BY SubCategoryName
    """
    
    try:
        df, _ = execute_query(query)
        return df['SubCategoryName'].tolist()
    except Exception:
        return []


def get_brands_by_category(category: str) -> list:
    """
    Get distinct brands for a specific category
    
    Args:
        category (str): Category name to filter by
        
    Returns:
        list: List of unique brand names
    """
    # Escape single quotes
    category_escaped = category.replace("'", "''")
    
    query = f"""
    SELECT DISTINCT Brand
    FROM `commercial-prod-375618.pcb_data_prod.PCB_PRODUCT_MASTER`
    WHERE CategoryName = '{category_escaped}'
      AND Brand IS NOT NULL
    ORDER BY Brand
    """
    
    try:
        df, _ = execute_query(query)
        return df['Brand'].tolist()
    except Exception:
        return []


def test_connection() -> bool:
    """
    Test BigQuery connection
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        client = get_bigquery_client()
        # Simple query to test connection
        query = "SELECT 1 as test"
        query_job = client.query(query)
        query_job.result()
        return True
    except Exception as e:
        st.error(f"❌ Connection test failed: {str(e)}")
        return False
