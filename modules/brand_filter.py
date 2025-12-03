"""
Brand Filter Module
Client-side filtering for asymmetric brand analysis
"""

import pandas as pd
from typing import List


def filter_dataframe_by_brands(df: pd.DataFrame, brands: List[str], mode: str = 'full') -> pd.DataFrame:
    """
    Filter switching dataframe by brands for Period 2 (client-side)
    
    This enables toggling between "Filtered View" (symmetric) and "Full View" (asymmetric)
    without re-querying BigQuery.
    
    Args:
        df: Raw switching data (Period 2 is unfiltered)
        brands: List of brands that were filtered in Period 1
        mode: 'filtered' = symmetric filter (current behavior)
              'full' = asymmetric filter (show where filtered brands went)
    
    Returns:
        Filtered dataframe based on mode
    
    Examples:
        # Filtered view: Only show COLGATE → COLGATE flows
        df_filtered = filter_dataframe_by_brands(df, ['COLGATE'], mode='filtered')
        
        # Full view: Show COLGATE → ALL BRANDS flows
        df_full = filter_dataframe_by_brands(df, ['COLGATE'], mode='full')
    """
    if not brands or mode == 'full':
        # Full mode: return all data (no filtering on Period 2)
        return df.copy()
    
    # Filtered mode: apply symmetric filter (remove non-filtered brands from Period 2)
    # IMPORTANT: Do NOT include MIXED in special categories for filtered view
    # MIXED contains multiple brands and would inflate Switch_Out metrics
    special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY'}
    
    # Filter logic: Keep rows where prod_2025 is either:
    # 1. In the selected brands
    # 2. A special category (NEW_TO_CATEGORY, LOST_FROM_CATEGORY only)
    filtered_df = df[
        df['prod_2025'].isin(brands) | 
        df['prod_2025'].isin(special_categories)
    ].copy()
    
    return filtered_df


def get_filter_description(brands: List[str], mode: str) -> str:
    """
    Get human-readable description of current filter mode
    
    Args:
        brands: List of filtered brands
        mode: 'filtered' or 'full'
    
    Returns:
        Description string
    """
    if not brands:
        return "All brands (no filter)"
    
    brand_list = ", ".join(brands)
    
    if mode == 'filtered':
        return f"🔒 Filtered View: {brand_list} → {brand_list}"
    else:
        return f"🔓 Full View: {brand_list} → All Brands"
