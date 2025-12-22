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
    if not brands:
        # No brand filter: return all data
        return df.copy()
    
    if mode == 'full':
        # Full View: Show where selected brands went
        # Filter prod_2024 to selected brands only
        # Keep ALL prod_2025 destinations visible
        return df[df['prod_2024'].isin(brands)].copy()
    
    # Filtered mode: apply OTHERS aggregation for both periods
    # This allows Switch In calculation while keeping focus on selected brands
    special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY'}
    
    filtered_df = df.copy()
    
    # Step 1: Convert non-selected brands in prod_2024 to 'OTHERS'
    # Keep: selected brands + NEW_TO_CATEGORY
    # Convert to 'OTHERS': everything else
    should_rename_2024_to_others = (
        ~filtered_df['prod_2024'].isin(brands) &  # Not a selected brand
        (filtered_df['prod_2024'] != 'NEW_TO_CATEGORY')  # Keep NEW_TO_CATEGORY as-is
    )
    filtered_df.loc[should_rename_2024_to_others, 'prod_2024'] = 'OTHERS'
    
    # Step 2: Convert non-selected brands in prod_2025 to 'OTHERS'
    # Keep: selected brands + special categories (NEW_TO_CATEGORY, LOST_FROM_CATEGORY) + MIXED
    # Convert to 'OTHERS': everything else
    should_rename_2025_to_others = (
        ~filtered_df['prod_2025'].isin(brands) &  # Not a selected brand
        ~filtered_df['prod_2025'].isin(special_categories) &  # Not a special category
        (filtered_df['prod_2025'] != 'MIXED')  # Keep MIXED as-is
    )
    filtered_df.loc[should_rename_2025_to_others, 'prod_2025'] = 'OTHERS'
    
    # Step 3: Aggregate by grouping (sum customers and sales for OTHERS flows)
    agg_dict = {'customers': 'sum'}
    if 'sales_2024' in filtered_df.columns:
        agg_dict['sales_2024'] = 'sum'
    if 'sales_2025' in filtered_df.columns:
        agg_dict['sales_2025'] = 'sum'
    if 'total_sales' in filtered_df.columns:
        agg_dict['total_sales'] = 'sum'
    
    filtered_df = filtered_df.groupby(['prod_2024', 'prod_2025', 'move_type'], as_index=False).agg(agg_dict)
    
    # Step 4: Filter out unwanted OTHERS flows to reduce confusion
    # Keep OTHERS only when it flows TO focused brands (Switch In)
    # Remove: OTHERS → OTHERS, OTHERS → LOST, OTHERS → MIXED, etc.
    # Keep all flows FROM focused brands (including → OTHERS for Switch Out visibility)
    filtered_df = filtered_df[
        # Keep all flows FROM focused brands or NEW_TO_CATEGORY
        (filtered_df['prod_2024'].isin(brands) | (filtered_df['prod_2024'] == 'NEW_TO_CATEGORY')) |
        # OR keep OTHERS flows only when going TO focused brands
        ((filtered_df['prod_2024'] == 'OTHERS') & (filtered_df['prod_2025'].isin(brands)))
    ]
    
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
