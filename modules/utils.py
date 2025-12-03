"""
Utilities Module
Helper functions for the Everything-Switching Analysis app
"""

import streamlit as st
import pandas as pd
from typing import Optional
from io import BytesIO
import config


def format_number(num: int) -> str:
    """
    Format number with thousand separators
    
    Args:
        num (int): Number to format
    
    Returns:
        str: Formatted number
    """
    return f"{num:,}"


def calculate_cost_thb(gb_processed: float) -> float:
    """
    Calculate BigQuery cost in Thai Baht
    
    Args:
        gb_processed (float): Gigabytes processed
    
    Returns:
        float: Cost in THB
    """
    try:
        cost_per_gb = float(st.secrets.get("BIGQUERY_COST_PER_GB_THB", "17.5"))
        return gb_processed * cost_per_gb
    except:
        return gb_processed * 17.5  # Default fallback


def display_cost_info(gb_processed: float):
    """
    Display BigQuery cost information in Streamlit
    
    Args:
        gb_processed (float): Gigabytes processed
    """
    cost_thb = calculate_cost_thb(gb_processed)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="📊 Data Processed",
            value=f"{gb_processed:.4f} GB"
        )
    with col2:
        st.metric(
            label="💰 Estimated Cost",
            value=f"฿{cost_thb:.2f}"
        )


def parse_barcode_mapping(mapping_text: str) -> dict:
    """
    Parse barcode mapping text into dictionary
    
    Args:
        mapping_text (str): Text with barcode-description pairs
    
    Returns:
        dict: Dictionary mapping barcodes to descriptions
    """
    if not mapping_text or not mapping_text.strip():
        return {}
    
    mapping = {}
    lines = mapping_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Support both comma and tab separated
        parts = line.replace('\t', ',').split(',', 1)
        
        if len(parts) == 2:
            barcode = parts[0].strip()
            description = parts[1].strip()
            if barcode and description:
                mapping[barcode] = description
    
    return mapping


def validate_barcode_mapping(mapping_text: str) -> tuple[bool, str]:
    """
    Validate barcode mapping format
    
    Args:
        mapping_text (str): Text to validate
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not mapping_text or not mapping_text.strip():
        return True, ""
    
    lines = mapping_text.strip().split('\n')
    valid_lines = 0
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        parts = line.replace('\t', ',').split(',', 1)
        
        if len(parts) != 2:
            return False, f"Line {i}: Invalid format. Expected 'barcode,description'"
        
        valid_lines += 1
    
    if valid_lines == 0:
        return False, "No valid barcode mappings found"
    
    if valid_lines > config.MAX_BARCODE_MAPPINGS:
        return False, f"Too many mappings ({valid_lines}). Maximum allowed: {config.MAX_BARCODE_MAPPINGS}"
    
    return True, f"✅ {valid_lines} valid mappings"


def create_excel_export(df: pd.DataFrame, summary_df: pd.DataFrame) -> BytesIO:
    """
    Create Excel file with multiple sheets for export
    
    Args:
        df (pd.DataFrame): Raw query results
        summary_df (pd.DataFrame): Brand summary data
    
    Returns:
        BytesIO: Excel file in memory
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write summary sheet
        summary_df.to_excel(
            writer,
            sheet_name=config.EXCEL_SHEET_NAMES['summary'],
            index=False
        )
        
        # Write detailed flow sheet
        df.to_excel(
            writer,
            sheet_name=config.EXCEL_SHEET_NAMES['details'],
            index=False
        )
        
        # Create movement type summary
        movement_summary = df.groupby('move_type').agg({
            'customers': 'sum'
        }).reset_index()
        movement_summary.to_excel(
            writer,
            sheet_name='Movement Types',
            index=False
        )
    
    output.seek(0)
    return output


def display_filter_summary(
    analysis_mode: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    category: str,
    brands: list,
    product_contains: Optional[str],
    threshold: float,
    custom_mapping_count: int = 0
):
    """
    Display a summary card of current filters
    
    Args:
        analysis_mode (str): Selected analysis mode
        period1_start (str): Period 1 start date
        period1_end (str): Period 1 end date
        period2_start (str): Period 2 start date
        period2_end (str): Period 2 end date
        category (str): Selected category
        brands (list): Selected brands
        product_contains (str): Product name filter
        threshold (float): Primary threshold
        custom_mapping_count (int): Number of custom barcode mappings
    """
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Current Analysis Settings</span>
    </div>
""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        **Analysis Mode:**  
        {config.ANALYSIS_MODES[analysis_mode]['label']}
        
        **Category:**  
        {category}
        
        **Primary Threshold:**  
        {threshold*100:.0f}%
        """)
    
    with col2:
        st.markdown(f"""
        **Period 1:**  
        {period1_start} to {period1_end}
        
        **Period 2:**  
        {period2_start} to {period2_end}
        """)
    
    with col3:
        brands_text = f"{len(brands)} brands" if brands else "All brands"
        product_text = f"Contains '{product_contains}'" if product_contains else "All products"
        custom_text = f"{custom_mapping_count} custom mappings" if custom_mapping_count > 0 else "No custom mappings"
        
        st.markdown(f"""
        **Brands:**  
        {brands_text}
        
        **Product Filter:**  
        {product_text}
        
        **Custom Mappings:**  
        {custom_text}
        """)
    
    st.markdown("---")


def show_debug_query(query: str):
    """
    Store the SQL query in session state for later viewing
    
    Args:
        query (str): SQL query to display
    """
    # Store query in session state for later viewing
    st.session_state.last_executed_query = query


def get_brand_color(brand: str) -> str:
    """
    Get color for a brand from config or generate a default
    
    Args:
        brand (str): Brand name
    
    Returns:
        str: Hex color code
    """
    return config.BRAND_COLORS.get(brand, '#2196F3')
