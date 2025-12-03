"""
Data Processor Module
Processes query results and prepares data for visualizations
"""

import pandas as pd
from typing import Dict, List, Tuple


def aggregate_to_brand_level(df: pd.DataFrame, product_master_lookup: Dict[str, str] = None) -> pd.DataFrame:
    """
    Aggregate product-level switching data to brand-level
    
    Args:
        df: Product-level switching dataframe with columns: prod_2024, prod_2025, customers, move_type
        product_master_lookup: Optional dict mapping product names to brands
    
    Returns:
        Brand-level switching dataframe with same structure
    """
    # If no lookup provided, try to extract brand from product name
    df_agg = df.copy()
    
    # Keep special categories as-is
    special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED'}
    
    def extract_brand(product_name):
        # Handle None, NaN, or empty values
        if pd.isna(product_name) or not product_name:
            return 'Unknown'
        
        # Convert to string if not already
        product_name = str(product_name).strip()
        
        if product_name in special_categories:
            return product_name
        
        # Extract first word as brand
        parts = product_name.split()
        return parts[0] if parts else 'Unknown'
    
    # If we have a lookup, use it
    if product_master_lookup:
        df_agg['brand_2024'] = df_agg['prod_2024'].map(product_master_lookup).fillna('Unknown')
        df_agg['brand_2025'] = df_agg['prod_2025'].map(product_master_lookup).fillna('Unknown')
    else:
        # Fallback: try to extract brand (first word)
        df_agg['brand_2024'] = df_agg['prod_2024'].apply(extract_brand)
        df_agg['brand_2025'] = df_agg['prod_2025'].apply(extract_brand)
    
    # Aggregate to brand level
    brand_df = df_agg.groupby(['brand_2024', 'brand_2025', 'move_type'], dropna=False).agg({
        'customers': 'sum'
    }).reset_index()
    
    # Rename to match expected columns
    brand_df = brand_df.rename(columns={
        'brand_2024': 'prod_2024',
        'brand_2025': 'prod_2025'
    })
    
    return brand_df


def calculate_brand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate movement summary for each brand"""
    
    all_brands = set()
    all_brands.update(df['prod_2024'].unique())
    all_brands.update(df['prod_2025'].unique())
    
    special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED'}
    brands = sorted([b for b in all_brands if b not in special_categories])
    
    summary_data = []
    
    for brand in brands:
        stayed = df[(df['prod_2024'] == brand) & (df['prod_2025'] == brand) & (df['move_type'] == 'stayed')]['customers'].sum()
        switch_out = df[(df['prod_2024'] == brand) & (df['prod_2025'] != brand) & (df['prod_2025'] != 'LOST_FROM_CATEGORY') & (df['move_type'] == 'switched')]['customers'].sum()
        gone = df[(df['prod_2024'] == brand) & (df['prod_2025'] == 'LOST_FROM_CATEGORY')]['customers'].sum()
        switch_in = df[(df['prod_2024'] != brand) & (df['prod_2024'] != 'NEW_TO_CATEGORY') & (df['prod_2025'] == brand) & (df['move_type'] == 'switched')]['customers'].sum()
        new_customer = df[(df['prod_2024'] == 'NEW_TO_CATEGORY') & (df['prod_2025'] == brand)]['customers'].sum()
        
        # Total In = Stayed + Switch In + New Customer
        total_in = stayed + switch_in + new_customer
        total_out = switch_out + gone
        net_movement = total_in - total_out
        
        period1_total = stayed + switch_out + gone
        period2_total = stayed + switch_in + new_customer
        
        summary_data.append({
            'Brand': brand,
            '2024_Total': period1_total,
            'Stayed': stayed,
            'Switch_Out': switch_out,
            'Gone': gone,
            'Switch_In': switch_in,
            'New_Customer': new_customer,
            '2025_Total': period2_total,
            'Total_In': total_in,
            'Total_Out': total_out,
            'Net_Movement': net_movement,
            # % based on Period 1 for outflows
            'Stayed_%': round(stayed / period1_total * 100, 1) if period1_total > 0 else 0,
            'Switch_Out_%': round(switch_out / period1_total * 100, 1) if period1_total > 0 else 0,
            'Gone_%': round(gone / period1_total * 100, 1) if period1_total > 0 else 0,
            # %Share based on Total In for inflows
            'Switch_In_%': round(switch_in / total_in * 100, 1) if total_in > 0 else 0,
            'New_Customer_%': round(new_customer / total_in * 100, 1) if total_in > 0 else 0,
        })
    
    return pd.DataFrame(summary_data)


def prepare_sankey_data(df: pd.DataFrame) -> Tuple[List, List, List]:
    """Prepare data for Sankey diagram"""
    labels_2024 = df['prod_2024'].unique().tolist()
    labels_2025 = df['prod_2025'].unique().tolist()
    
    all_labels = []
    label_mapping = {}
    
    for label in labels_2024:
        if label not in label_mapping:
            # Replace label names for display
            display_label = label.replace('NEW_TO_CATEGORY', 'New Customers').replace('LOST_FROM_CATEGORY', 'Gone')
            label_mapping[label] = len(all_labels)
            all_labels.append(display_label)
    
    for label in labels_2025:
        period2_key = f"{label}_2025"
        if period2_key not in label_mapping:
            display_label = label.replace('NEW_TO_CATEGORY', 'New Customers').replace('LOST_FROM_CATEGORY', 'Gone')
            label_mapping[period2_key] = len(all_labels)
            all_labels.append(display_label)
    
    sources, targets, values = [], [], []
    for _, row in df.iterrows():
        source_idx = label_mapping[row['prod_2024']]
        target_idx = label_mapping[f"{row['prod_2025']}_2025"]
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(row['customers'])
    
    return all_labels, sources, targets, values


def prepare_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for competitive matrix heatmap"""
    # Replace labels for display
    df_display = df.copy()
    df_display['prod_2024'] = df_display['prod_2024'].replace({'NEW_TO_CATEGORY': 'New Customers', 'LOST_FROM_CATEGORY': 'Gone'})
    df_display['prod_2025'] = df_display['prod_2025'].replace({'NEW_TO_CATEGORY': 'New Customers', 'LOST_FROM_CATEGORY': 'Gone'})
    
    return df_display.pivot_table(index='prod_2024', columns='prod_2025', values='customers', fill_value=0, aggfunc='sum')


def prepare_waterfall_data(df: pd.DataFrame, brand: str) -> Dict:
    """Prepare data for waterfall chart"""
    period1_total = df[df['prod_2024'] == brand]['customers'].sum()
    period2_total = df[df['prod_2025'] == brand]['customers'].sum()
    
    new_customers = df[(df['prod_2024'] == 'NEW_TO_CATEGORY') & (df['prod_2025'] == brand)]['customers'].sum()
    switch_in = df[(df['prod_2024'] != brand) & (df['prod_2024'] != 'NEW_TO_CATEGORY') & (df['prod_2025'] == brand) & (df['move_type'] == 'switched')]['customers'].sum()
    switch_out = df[(df['prod_2024'] == brand) & (df['prod_2025'] != brand) & (df['prod_2025'] != 'LOST_FROM_CATEGORY') & (df['move_type'] == 'switched')]['customers'].sum()
    gone = df[(df['prod_2024'] == brand) & (df['prod_2025'] == 'LOST_FROM_CATEGORY')]['customers'].sum()
    
    return {
        'labels': ['2024 Total', 'New Customers', 'Switch In', 'Switch Out', 'Gone', '2025 Total'],
        'values': [period1_total, new_customers, switch_in, -switch_out, -gone, period2_total],
        'measure': ['absolute', 'relative', 'relative', 'relative', 'relative', 'total']
    }


def get_top_flows(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Get top N customer flows"""
    top = df.nlargest(n, 'customers')[['prod_2024', 'prod_2025', 'customers', 'move_type']].copy()
    # Replace labels for display
    top['prod_2024'] = top['prod_2024'].replace({'NEW_TO_CATEGORY': 'New Customers', 'LOST_FROM_CATEGORY': 'Gone'})
    top['prod_2025'] = top['prod_2025'].replace({'NEW_TO_CATEGORY': 'New Customers', 'LOST_FROM_CATEGORY': 'Gone'})
    return top


def get_brand_switching_summary(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Get detailed brand switching flows with percentages
    
    Args:
        df: Switching dataframe
        top_n: Number of top switching flows to return
    
    Returns:
        DataFrame with columns: From_Brand, To_Brand, Customers, Pct_of_From_Brand
    """
    # Filter only switched movements (exclude stayed, new, gone)
    switched_df = df[df['move_type'] == 'switched'].copy()
    
    # Remove NEW_TO_CATEGORY and LOST_FROM_CATEGORY
    switched_df = switched_df[
        (switched_df['prod_2024'] != 'NEW_TO_CATEGORY') &
        (switched_df['prod_2024'] != 'LOST_FROM_CATEGORY') &
        (switched_df['prod_2025'] != 'NEW_TO_CATEGORY') &
        (switched_df['prod_2025'] != 'LOST_FROM_CATEGORY')
    ].copy()
    
    if len(switched_df) == 0:
        return pd.DataFrame(columns=['From_Brand', 'To_Brand', 'Customers', 'Pct_of_From_Brand'])
    
    # Calculate baseline for each from_brand (total customers in 2024)
    brand_2024_totals = df.groupby('prod_2024')['customers'].sum().to_dict()
    
    # Prepare switching summary
    switching_data = []
    for _, row in switched_df.iterrows():
        from_brand = row['prod_2024']
        to_brand = row['prod_2025']
        customers = row['customers']
        
        # Calculate percentage of source brand
        from_brand_total = brand_2024_totals.get(from_brand, 0)
        pct_of_from = (customers / from_brand_total * 100) if from_brand_total > 0 else 0
        
        switching_data.append({
            'From_Brand': from_brand,
            'To_Brand': to_brand,
            'Customers': customers,
            'Pct_of_From_Brand': round(pct_of_from, 2)
        })
    
    # Create DataFrame and sort by customers
    switching_summary = pd.DataFrame(switching_data)
    switching_summary = switching_summary.sort_values('Customers', ascending=False).head(top_n)
    
    return switching_summary


def calculate_executive_kpis(summary_df: pd.DataFrame, summary_df_full: pd.DataFrame = None) -> Dict:
    """
    Calculate high-level executive KPIs
    
    Args:
        summary_df: Brand summary dataframe (filtered data) - for Total Movement, Net Flow, Churn
        summary_df_full: Brand summary dataframe (full category data) - for Winner/Loser comparison
        
    Returns:
        Dictionary with KPI metrics
    """
    if len(summary_df) == 0:
        return {}
    
    # If full data not provided, use filtered data for everything
    if summary_df_full is None:
        summary_df_full = summary_df
        
    # 1. Total Category Movement (Total customers in Period 1) - FROM FILTERED DATA
    total_movement = summary_df['2024_Total'].sum()
    
    # 2. Biggest Winner (Max Net Movement > 0) - FROM FULL DATA
    winners = summary_df_full[summary_df_full['Net_Movement'] > 0]
    if len(winners) > 0:
        biggest_winner = winners.loc[winners['Net_Movement'].idxmax()]
        winner_name = biggest_winner['Brand']
        winner_val = biggest_winner['Net_Movement']
    else:
        winner_name = "None"
        winner_val = 0
        
    # 3. Biggest Loser (Min Net Movement) - FROM FULL DATA
    if len(summary_df_full) > 0:
        # If only one brand and it's positive, still show it as "loser" (relative to itself)
        biggest_loser = summary_df_full.loc[summary_df_full['Net_Movement'].idxmin()]
        loser_name = biggest_loser['Brand']
        loser_val = biggest_loser['Net_Movement']
    else:
        loser_name = "None"
        loser_val = 0
        
    # 4. Overall Churn Rate (Total Gone + Switch Out / Total Period 1) - FROM FILTERED DATA
    total_gone = summary_df['Gone'].sum()
    total_switch_out = summary_df['Switch_Out'].sum()
    churn_rate = ((total_gone + total_switch_out) / total_movement * 100) if total_movement > 0 else 0
    
    # 5. Net Movement Category Level - FROM FILTERED DATA
    # Formula: (New + Switch In) - (Switch Out + Gone)
    total_new = summary_df['New_Customer'].sum()
    total_switch_in = summary_df['Switch_In'].sum()
    net_category_movement = (total_new + total_switch_in) - (total_switch_out + total_gone)
    
    return {
        'total_movement': total_movement,
        'winner_name': winner_name,
        'winner_val': winner_val,
        'loser_name': loser_name,
        'loser_val': loser_val,
        'churn_rate': churn_rate,
        'net_category_movement': net_category_movement,
        'total_new': total_new,
        'total_gone': total_gone
    }


def calculate_cohort_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate Cohort and Loyalty metrics
    
    Args:
        df: Switching dataframe
        
    Returns:
        Dictionary with loyalty metrics
    """
    # 1. Repeat Purchase Rate (Stayed / Total Period 1)
    # Note: This is an approximation based on switching data. 
    # True cohort analysis needs transaction-level data over time.
    # Here we use "Stayed" as a proxy for loyalty/retention between the two periods.
    
    total_period1 = df[df['prod_2024'] != 'NEW_TO_CATEGORY']['customers'].sum()
    stayed_customers = df[df['move_type'] == 'stayed']['customers'].sum()
    
    retention_rate = (stayed_customers / total_period1 * 100) if total_period1 > 0 else 0
    
    # 2. One-time Buyers (Gone / Total Period 1) - Proxy
    gone_customers = df[df['prod_2025'] == 'LOST_FROM_CATEGORY']['customers'].sum()
    churn_rate = (gone_customers / total_period1 * 100) if total_period1 > 0 else 0
    
    # 3. Switchers (Switched Out / Total Period 1)
    switch_out = df[(df['move_type'] == 'switched') & (df['prod_2025'] != 'LOST_FROM_CATEGORY')]['customers'].sum()
    switch_rate = (switch_out / total_period1 * 100) if total_period1 > 0 else 0
    
    return {
        'retention_rate': retention_rate,
        'churn_rate': churn_rate,
        'switch_rate': switch_rate,
        'stayed_customers': stayed_customers,
        'gone_customers': gone_customers,
        'switch_out_customers': switch_out,
        'total_base': total_period1
    }
