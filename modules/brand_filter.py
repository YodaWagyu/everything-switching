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
    
    # Filtered mode: apply symmetric filter with OTHERS aggregation
    # IMPORTANT: Do NOT include MIXED in special categories for filtered view
    # MIXED contains multiple brands and would inflate Switch_Out metrics
    special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY'}
    
    # Step 1: Filter prod_2024 to selected brands only
    # This ensures we only look at customers from selected brands in Period 1
    filtered_df = df[df['prod_2024'].isin(brands)].copy()
    
    # Step 2: For prod_2025, convert non-selected brands to 'OTHERS'
    # This maintains total customer count while providing focused view
    # Keep: selected brands + special categories
    # Convert to 'OTHERS': everything else except MIXED (which should be kept as-is for transparency)
    
    # Create a mask for destinations that should be renamed to OTHERS
    should_rename_to_others = (
        ~filtered_df['prod_2025'].isin(brands) &  # Not a selected brand
        ~filtered_df['prod_2025'].isin(special_categories) &  # Not a special category
        (filtered_df['prod_2025'] != 'MIXED')  # Keep MIXED as-is
    )
    
    # Rename to OTHERS
    filtered_df.loc[should_rename_to_others, 'prod_2025'] = 'OTHERS'
    
    # Group by the new keys and sum customers (aggregate OTHERS)
    filtered_df = filtered_df.groupby(['prod_2024', 'prod_2025', 'move_type'], as_index=False)['customers'].sum()
    
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
