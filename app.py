"""Everything-Switching Analysis Application"""
import streamlit as st
from datetime import datetime, timedelta
from modules import bigquery_client, data_processor, visualizations, utils, query_builder, ai_analyzer, auth
import config
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Everything-Switching", page_icon="🔄", layout="wide")

# Load Custom CSS
def load_css():
    try:
        with open('assets/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# Load Tailwind CSS CDN
def load_tailwind():
    st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            prefix: 'tw-',
            important: true
        }
    </script>
    """, unsafe_allow_html=True)

load_css()
load_tailwind()

# Authentication check
if not auth.is_authenticated():
    auth.show_login_page()
    st.stop()

# Main app (only visible after login)
# Custom Header with ES Logo
st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 30px; padding-top: 10px;">
        <div style="
            width: 45px; 
            height: 45px; 
            background: #0f3d3e; 
            border-radius: 10px; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            color: white;
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 18px;
            letter-spacing: -1px;
            box-shadow: 0 4px 10px rgba(15, 61, 62, 0.2);
        ">
            ES
        </div>
        <div style="
            font-family: 'Inter', sans-serif; 
            font-weight: 800; 
            font-size: 28px; 
            color: #0f3d3e; 
            letter-spacing: -1px;
        ">
            Everything-Switching Analysis
        </div>
    </div>
""", unsafe_allow_html=True)

# Add logout button in sidebar
with st.sidebar:
    if st.button("🚪 Logout", use_container_width=True):
        auth.logout()

if 'query_executed' not in st.session_state:
    st.session_state.query_executed = False


st.sidebar.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
        <span style="font-size: 18px; font-weight: 700; color: white;">Analysis Mode</span>
    </div>
""", unsafe_allow_html=True)
analysis_mode = st.sidebar.radio("Select mode", config.ANALYSIS_MODES, label_visibility="collapsed")

st.sidebar.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; margin-top: 20px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2.01.89-2.01 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>
        <span style="font-size: 18px; font-weight: 700; color: white;">Before Period</span>
    </div>
""", unsafe_allow_html=True)
col1, col2 = st.sidebar.columns(2)
with col1:
    period1_start = st.date_input("Start", datetime(2024, 1, 1), key="before_start")
with col2:
    period1_end = st.date_input("End", datetime(2024, 1, 31), key="before_end")

st.sidebar.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; margin-top: 20px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2.01.89-2.01 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>
        <span style="font-size: 18px; font-weight: 700; color: white;">After Period</span>
    </div>
""", unsafe_allow_html=True)
col3, col4 = st.sidebar.columns(2)
with col3:
    period2_start = st.date_input("Start", datetime(2025, 1, 1), key="after_start")
with col4:
    period2_end = st.date_input("End", datetime(2025, 1, 31), key="after_end")

st.sidebar.markdown("---")
with st.sidebar.expander("🏪 Store Settings", expanded=True):
    store_filter_type = st.radio("Store Type", ["All Store", "Same Store"], label_visibility="collapsed")

    store_opening_cutoff = None
    if store_filter_type == "Same Store":
        default_cutoff = datetime(2023, 12, 31)
        store_opening_cutoff = st.date_input(
            "Opened before", 
            default_cutoff,
            help="Only include stores that opened before this date",
            key="store_cutoff"
        ).strftime("%Y-%m-%d")

st.sidebar.markdown("---")
with st.sidebar.expander("🔍 Product Filters", expanded=True):
    available_categories = bigquery_client.get_categories()
    selected_categories = st.multiselect("Category", available_categories, default=[available_categories[0]] if available_categories else [])

    selected_subcategories = []
    if selected_categories:
        all_subcategories = []
        for cat in selected_categories:
            subcats = bigquery_client.get_subcategories(cat)
            all_subcategories.extend(subcats)
        all_subcategories = list(set(all_subcategories))
        selected_subcategories = st.multiselect("SubCategory", all_subcategories)

    brands_text = st.text_input("Brands", placeholder="เช่น NIVEA, VASELINE, CITRA", help="Enter brand names separated by commas")
    selected_brands = [b.strip() for b in brands_text.split(',') if b.strip()] if brands_text else []

    product_name_contains = st.text_input("Product Contains", placeholder="เช่น โลชั่น, ครีม, นม", help="ใส่คำค้นหาได้หลายคำคั่นด้วยคอมม่า (OR condition)")

    product_name_not_contains = st.text_input("Product NOT Contains", placeholder="เช่น PM_, PROMO", help="กรองสินค้าที่มีคำนี้ออก (AND NOT condition)")

st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Advanced Settings", expanded=False):
    primary_threshold = st.slider("Primary %", float(config.MIN_PRIMARY_THRESHOLD*100), float(config.MAX_PRIMARY_THRESHOLD*100), float(config.DEFAULT_PRIMARY_THRESHOLD*100), step=5.0) / 100.0

    barcode_mapping_text = ""
    if analysis_mode == "Custom Type":
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; margin-top: 20px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/></svg>
            <span style="font-size: 18px; font-weight: 700; color: white;">Barcode Mapping</span>
        </div>
    """, unsafe_allow_html=True)
        barcode_mapping_text = st.text_area("Paste barcode mapping", barcode_mapping_text, height=150, placeholder="barcode,product_type", help="Format: barcode,product_type (one per line)")

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)

if run_analysis or st.session_state.query_executed:
    if run_analysis:
        selected_category = selected_categories[0] if selected_categories else None
        
        # Validate required fields
        if not selected_category:
            st.error("⚠️ Please select at least one category to run the analysis.")
            st.stop()
        
        # Query ALL brands in category (no brand filter at BigQuery level)
        # Brand filtering will be done client-side for Focus View
        query_all_brands = query_builder.build_switching_query(
            analysis_mode, 
            period1_start.strftime("%Y-%m-%d"), 
            period1_end.strftime("%Y-%m-%d"), 
            period2_start.strftime("%Y-%m-%d"), 
            period2_end.strftime("%Y-%m-%d"), 
            selected_category, 
            None,  # No brand filter - get all brands
            product_name_contains or None,
            product_name_not_contains or None,
            primary_threshold, 
            barcode_mapping_text if analysis_mode == "Custom Type" else None,
            store_filter_type,
            store_opening_cutoff
        )
        
        utils.show_debug_query(query_all_brands)
        df, gb_processed = bigquery_client.execute_query(query_all_brands)
        st.session_state.results_df = df
        st.session_state.gb_processed = gb_processed
        st.session_state.query_executed = True
        # Don't calculate summary_df yet - wait until after view mode toggle
    
    df = st.session_state.results_df
    gb_processed = st.session_state.gb_processed
    if df is None or len(df) == 0:
        st.warning("⚠️ No data")
        st.stop()
    
    # Admin-only: Cost and Query Display
    if auth.is_admin():
        if gb_processed > 0:
            st.markdown("---")
            col_cost1, col_cost2 = st.columns([3, 1])
            with col_cost1:
                utils.display_cost_info(gb_processed)
            with col_cost2:
                st.markdown("")  # Spacer
                if st.button("🔍 View SQL Query", use_container_width=True):
                    st.session_state.show_query = not st.session_state.get('show_query', False)
        
            # Show query if button clicked
            if st.session_state.get('show_query', False) and 'last_executed_query' in st.session_state:
                with st.expander("📝 Executed SQL Query", expanded=True):
                    st.code(st.session_state.last_executed_query, language="sql")
    else:
        # User sees no cost/query sections
        st.markdown("---")
    
    display_category = selected_categories[0] if selected_categories else None
    
    # Smart Brand/Product Filter based on Analysis Mode
    special_categories = ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED']
    
    # Check if we're in Product Switch mode (for display logic later)
    is_product_switch_mode = (analysis_mode == "Product Switch")
    
    # BOTH Brand Switch and Product Switch:
    # - SQL query returns PRODUCT-level data
    # - Dropdown shows BRANDS (from mapping)
    # - The difference is in DISPLAY:
    #   - Brand Switch: aggregate to brand level
    #   - Product Switch: keep product level
    
    # Load product-to-brand mapping (needed for BOTH modes)
    st.caption("🔄 Loading product-brand mapping...")
    
    # Query product master to get Brand for all products in the category
    mapping_query = f"""
    SELECT DISTINCT
      ProductName,
      Brand
    FROM `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_PRODUCT_MASTER}`
    WHERE CategoryName = '{selected_categories[0] if selected_categories else ""}'
    """
    
    try:
        mapping_df, _ = bigquery_client.execute_query(mapping_query)
        
        # Create product-to-brand mapping
        product_to_brand_map = dict(zip(mapping_df['ProductName'], mapping_df['Brand']))
        
        # Get unique brands based on analysis mode
        if is_product_switch_mode:
            # Product Switch mode: df['prod_2024'] contains ProductNames
            # Map ProductNames to Brands using product_to_brand_map
            all_products_in_data = [p for p in df['prod_2024'].unique() if p not in special_categories]
            brands_set = set()
            for product in all_products_in_data:
                if product in product_to_brand_map:
                    brands_set.add(product_to_brand_map[product])
            all_brands_in_data = sorted(brands_set)
        else:
            # Brand Switch mode: df['prod_2024'] already contains Brand names
            # Get brands directly from the query results
            all_brands_in_data = sorted([b for b in df['prod_2024'].unique() if b not in special_categories])
        
        if is_product_switch_mode:
            filter_label = "Select Brands"
            filter_help = "💡 Select brands to see **product-level** switching within those brands"
        else:
            filter_label = "Select Brands"
            filter_help = "💡 Select brands to see **brand-level** aggregated switching"
        
    except Exception as e:
        st.error(f"Error loading product mapping: {e}")
        # Fallback: use direct values from query
        all_brands_in_data = sorted([b for b in df['prod_2024'].unique() if b not in special_categories])
        product_to_brand_map = {}
        filter_label = "Select Items"
        filter_help = "💡 Select items to analyze"
    
    # Post-Query Brand Filter - Rich Minimal Modern Design
    st.markdown("""
    <style>
    /* Target the container directly without needing marker div */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(+ div[data-testid="stMultiSelect"]) {
        background: #ffffff;
        border: 1.5px solid #d0d0d0;
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 32px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(+ div[data-testid="stMultiSelect"]):hover {
        border-color: #b0b0b0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #e8e8e8;">
            <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #0f3d3e 0%, #1a5f60 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(15, 61, 62, 0.2);">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M17.63 5.84C17.27 5.33 16.67 5 16 5L5 5.01C3.9 5.01 3 5.9 3 7v10c0 1.1.9 1.99 2 1.99L16 19c.67 0 1.27-.33 1.63-.84L22 12l-4.37-6.16zM16 17H5V7h11l3.55 5L16 17z"/></svg>
            </div>
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #1a1a1a; letter-spacing: -0.3px;">Select Brands</div>
                <div style="font-size: 13px; color: #666; margin-top: 2px;">Choose brands to analyze instantly</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        selected_brands = st.multiselect(
            filter_label,
            options=all_brands_in_data,
            default=None,
            help=filter_help,
            key="brand_filter_post_query",
            label_visibility="collapsed"
        )
        
        if not selected_brands:
            st.markdown("""
            <div style="background: #f8f9fa; border-left: 3px solid #0f3d3e; padding: 16px 20px; border-radius: 6px; margin-top: 16px;">
                <div style="font-size: 14px; color: #555; line-height: 1.6;">
                    <strong>👆 Select brands above</strong> to view insights
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        # Display selected brands elegantly
        if is_product_switch_mode and product_to_brand_map:
            # Count products under selected brands
            selected_products = [p for p, b in product_to_brand_map.items() if b in selected_brands]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); border-left: 3px solid #4caf50; padding: 14px 20px; border-radius: 6px; margin-top: 16px;">
                <div style="font-size: 13px; color: #2e7d32; font-weight: 600;">
                    ✓ Analyzing {len(selected_brands)} brand{"s" if len(selected_brands) > 1 else ""} ({len(selected_products)} products): <span style="font-weight: 700;">{", ".join(selected_brands)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); border-left: 3px solid #4caf50; padding: 14px 20px; border-radius: 6px; margin-top: 16px;">
                <div style="font-size: 13px; color: #2e7d32; font-weight: 600;">
                    ✓ Analyzing {len(selected_brands)} brand{"s" if len(selected_brands) > 1 else ""}: <span style="font-weight: 700;">{", ".join(selected_brands)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Apply Product Filtering for Product Switch Mode
    if is_product_switch_mode and selected_brands and product_to_brand_map:
        # Filter DataFrame to show only products from selected brands
        # Use accurate product_to_brand_map from BigQuery
        def is_product_in_brand(product_name, selected_brands, mapping):
            """Check if product belongs to any selected brand using accurate mapping"""
            if product_name in special_categories:
                return True  # Keep special categories
            # Use BigQuery mapping for accurate brand lookup
            brand = mapping.get(product_name)
            if brand and brand in selected_brands:
                return True
            return False
        
        # Filter rows where either prod_2024 or prod_2025 belongs to selected brands
        mask = (
            df['prod_2024'].apply(lambda x: is_product_in_brand(x, selected_brands, product_to_brand_map)) |
            df['prod_2025'].apply(lambda x: is_product_in_brand(x, selected_brands, product_to_brand_map))
        )
        df = df[mask].copy()
        
        st.caption(f"🔍 Filtered to {len(df)} customer flows involving products from {', '.join(selected_brands)}")
    
    # Note: No need to update filter summary here since we moved brand filter
    # utils.display_filter_summary(...) - will update this later if needed
    
    # Placeholder for Executive KPIs - will be calculated after filtering
    # Will be rendered after filtering
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 1: Customer Flow</span>
    </div>
""", unsafe_allow_html=True)
    
    # Apply brand filtering based on selection from sidebar
    df_display = df  # Default to full data
    
    if selected_brands:
        from modules import brand_filter
        
        # Apply client-side filter
        if is_product_switch_mode and product_to_brand_map:
            # Product Switch mode: df contains ProductNames
            # Need to get list of products that belong to selected brands
            products_in_selected_brands = [
                product for product, brand in product_to_brand_map.items() 
                if brand in selected_brands
            ]
            df_display = brand_filter.filter_dataframe_by_brands(df, products_in_selected_brands, 'filtered')
        else:
            # Brand Switch mode: df already contains Brand names
            # Filter directly by selected brand names
            df_display = brand_filter.filter_dataframe_by_brands(df, selected_brands, 'filtered')
    
    # KEY DIFFERENCE BETWEEN MODES:
    # - Brand Switch: Aggregate product-level data to BRAND level for display
    # - Product Switch: Keep PRODUCT level for display
    
    if is_product_switch_mode:
        # Product Switch: Keep product-level data
        item_label = 'Product'
        df_for_summary = df_display  # No aggregation needed
    else:
        # Brand Switch: df_display already contains Brand names (no aggregation needed)
        item_label = 'Brand'
        df_for_summary = df_display
    
    # Calculate summary
    summary_df = data_processor.calculate_brand_summary(df_for_summary, item_label=item_label)
    
    # Remove OTHERS from summary table to show only focused brands
    # But keep OTHERS in df_display so Waterfall/Matrix can show Switch In from OTHERS
    if selected_brands and len(summary_df) > 0:
        # Safety check: ensure column exists before filtering
        if item_label in summary_df.columns:
            summary_df = summary_df[summary_df[item_label] != 'OTHERS'].copy()
        # Note: We keep df_display as-is (with OTHERS flows) for Waterfall/Matrix visualization
    
    # Use summary_df for display
    summary_df_display = summary_df
    
    # --- Executive KPIs ---
    kpis = data_processor.calculate_executive_kpis(summary_df, summary_df, item_label=item_label)
    
    # Render Executive Summary Section at the top (but calculated here after filtering)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Executive Summary</span>
    </div>
    """, unsafe_allow_html=True)
    
    if kpis:
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            total_movement_fmt = utils.format_number(kpis['total_movement'])
            st.markdown(f"""
            <article class="tw-rounded-xl tw-bg-white tw-p-6 tw-ring-1 tw-ring-inset tw-ring-gray-200 tw-shadow-sm">
                <p class="tw-text-sm tw-font-medium tw-text-gray-500">Total Movement</p>
                <p class="tw-mt-2 tw-text-3xl tw-font-bold tw-text-teal-900">{total_movement_fmt}</p>
                <p class="tw-mt-1 tw-text-xs tw-text-gray-400">Customers</p>
            </article>
            """, unsafe_allow_html=True)
            
        with k2:
            net_cat = kpis['net_category_movement']
            is_positive = net_cat >= 0
            icon = "↑" if is_positive else "↓"
            color_class = "tw-text-emerald-600" if is_positive else "tw-text-red-600"
            bg_class = "tw-bg-emerald-50" if is_positive else "tw-bg-red-50"
            net_cat_fmt = utils.format_number(abs(net_cat))
            st.markdown(f"""
            <article class="tw-rounded-xl tw-bg-white tw-p-6 tw-ring-1 tw-ring-inset tw-ring-gray-200 tw-shadow-sm">
                <p class="tw-text-sm tw-font-medium tw-text-gray-500">Net Movement</p>
                <p class="tw-mt-2 tw-text-3xl tw-font-bold {color_class}">{icon} {net_cat_fmt}</p>
                <span class="tw-inline-flex tw-items-center tw-gap-1 tw-rounded-full {bg_class} tw-px-2 tw-py-0.5 tw-mt-1">
                    <span class="tw-text-xs tw-font-medium {color_class}">Total In - Out</span>
                </span>
            </article>
            """, unsafe_allow_html=True)
            
        with k3:
            winner_val_fmt = utils.format_number(kpis['winner_val'])
            st.markdown(f"""
            <article class="tw-rounded-xl tw-bg-white tw-p-6 tw-ring-1 tw-ring-inset tw-ring-gray-200 tw-shadow-sm">
                <p class="tw-text-sm tw-font-medium tw-text-gray-500">Biggest Winner</p>
                <p class="tw-mt-2 tw-text-xl tw-font-bold tw-text-teal-900 tw-truncate" title="{kpis['winner_name']}">{kpis['winner_name']}</p>
                <span class="tw-inline-flex tw-items-center tw-gap-1 tw-rounded-full tw-bg-emerald-50 tw-px-2 tw-py-0.5 tw-mt-1">
                    <span class="tw-text-xs tw-font-semibold tw-text-emerald-600">↑ +{winner_val_fmt}</span>
                </span>
            </article>
            """, unsafe_allow_html=True)
            
        with k4:
            loser_val = kpis['loser_val']
            loser_val_formatted = utils.format_number(abs(loser_val))
            st.markdown(f"""
            <article class="tw-rounded-xl tw-bg-white tw-p-6 tw-ring-1 tw-ring-inset tw-ring-gray-200 tw-shadow-sm">
                <p class="tw-text-sm tw-font-medium tw-text-gray-500">Biggest Loser</p>
                <p class="tw-mt-2 tw-text-xl tw-font-bold tw-text-teal-900 tw-truncate" title="{kpis['loser_name']}">{kpis['loser_name']}</p>
                <span class="tw-inline-flex tw-items-center tw-gap-1 tw-rounded-full tw-bg-red-50 tw-px-2 tw-py-0.5 tw-mt-1">
                    <span class="tw-text-xs tw-font-semibold tw-text-red-600">↓ {loser_val_formatted}</span>
                </span>
            </article>
            """, unsafe_allow_html=True)
            
        with k5:
            churn_rate_fmt = f"{kpis['churn_rate']:.1f}"
            # Color based on churn rate severity
            if kpis['churn_rate'] > 50:
                churn_color = "tw-text-red-600"
            elif kpis['churn_rate'] > 30:
                churn_color = "tw-text-amber-600"
            else:
                churn_color = "tw-text-emerald-600"
            st.markdown(f"""
            <article class="tw-rounded-xl tw-bg-white tw-p-6 tw-ring-1 tw-ring-inset tw-ring-gray-200 tw-shadow-sm">
                <p class="tw-text-sm tw-font-medium tw-text-gray-500">Attrition Rate</p>
                <p class="tw-mt-2 tw-text-3xl tw-font-bold {churn_color}">{churn_rate_fmt}%</p>
                <p class="tw-mt-1 tw-text-xs tw-text-gray-400">Out / Total</p>
            </article>
            """, unsafe_allow_html=True)
    
    # Data source for Sankey - use filtered data
    labels, sources, targets, values = data_processor.prepare_sankey_data(df_display)
    st.plotly_chart(visualizations.create_sankey_diagram(labels, sources, targets, values, None), use_container_width=True)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 2: Competitive Matrix</span>
    </div>
""", unsafe_allow_html=True)
    st.plotly_chart(visualizations.create_competitive_heatmap(data_processor.prepare_heatmap_data(df_display)), use_container_width=True)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 3: Brand Deep Dive</span>
    </div>
""", unsafe_allow_html=True)
    # Get available items for analysis with safety check
    if item_label in summary_df_display.columns:
        available_brands_for_analysis = summary_df_display[item_label].tolist()
    elif 'Brand' in summary_df_display.columns:
        available_brands_for_analysis = summary_df_display['Brand'].tolist()
    elif 'Product' in summary_df_display.columns:
        available_brands_for_analysis = summary_df_display['Product'].tolist()
    else:
        available_brands_for_analysis = []
    if available_brands_for_analysis:
        brand_options = available_brands_for_analysis
        
        selected_focus_brand = st.selectbox("Select brand", brand_options, key="focus_brand")
        
        if selected_focus_brand:
            # Use df_display (filtered) for waterfall to show data for selected brands
            st.plotly_chart(visualizations.create_waterfall_chart(data_processor.prepare_waterfall_data(df_display, selected_focus_brand), selected_focus_brand), use_container_width=True)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 4: Summary Tables & Charts</span>
    </div>
""", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Summary", "Brand Switching", "Loyalty", "Charts", "Raw", "Export"])
    with tab1:
        st.markdown("### Brand Movement Summary")
        display_summary = visualizations.create_summary_table_display(summary_df_display)
        
        # Sort by 2024_Total descending as requested
        if '2024_Total' in display_summary.columns:
            display_summary = display_summary.sort_values(by='2024_Total', ascending=False)
            
        def make_table(df):
            # Define rich gradient colors for each column group
            gradient_colors = {
                'Brand': 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
                '2024_Total': 'linear-gradient(135deg, #e67e22 0%, #d35400 100%)',
                'Stayed': 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)',
                'Stayed_%': 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)',
                'Switch_Out': 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)',
                'Switch_Out_%': 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)',
                'Gone': 'linear-gradient(135deg, #ec7063 0%, #e74c3c 100%)',
                'Gone_%': 'linear-gradient(135deg, #ec7063 0%, #e74c3c 100%)',
                'Total_Out': 'linear-gradient(135deg, #c0392b 0%, #922b21 100%)',
                'Switch_In': 'linear-gradient(135deg, #27ae60 0%, #1e8449 100%)',
                'New_Customer': 'linear-gradient(135deg, #52be80 0%, #27ae60 100%)',
                'Total_In': 'linear-gradient(135deg, #1e8449 0%, #145a32 100%)',
                '2025_Total': 'linear-gradient(135deg, #3498db 0%, #2874a6 100%)',
                'Net_Movement': 'linear-gradient(135deg, #2874a6 0%, #1b4f72 100%)'
            }
            
            # Define balanced column widths - EQUAL WIDTHS as requested
            col_widths = {
                'Brand': '7%',
                '2024_Total': '7%', 'Stayed': '7%', 'Stayed_%': '7%',
                'Switch_Out': '7%', 'Switch_Out_%': '7%',
                'Gone': '7%', 'Gone_%': '7%', 'Total_Out': '7%',
                'Switch_In': '7%', 'New_Customer': '7%', 'Total_In': '7%',
                '2025_Total': '7%', 'Net_Movement': '7%'
            }
            
            # Build table with rich styling
            h = '<div style="box-shadow: 0 4px 12px rgba(0,0,0,0.25); border-radius: 8px; overflow: hidden; width: 100%;">'
            h += '<table style="width:100%; font-size:12px; border-collapse: collapse; margin: 0; padding: 0; table-layout: fixed;"><thead><tr>'
            
            for col in df.columns:
                width = col_widths.get(col, '6%')
                gradient = gradient_colors.get(col, 'linear-gradient(135deg, #607D8B 0%, #455A64 100%)')
                h += f'''<th style="
                    background: {gradient}; 
                    color: white; 
                    padding: 12px; 
                    vertical-align: middle; 
                    text-align: center; 
                    width: {width}; 
                    white-space: nowrap;
                    border-right: 1px solid rgba(255,255,255,0.15);
                    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
                    font-weight: 600;
                ">{col.replace("_"," ")}</th>'''
            
            h += '</tr></thead><tbody>'
            
            for idx, row in df.iterrows():
                # Alternate row colors with hover effect (no scale)
                bg_color = '#fafafa' if idx % 2 == 0 else '#ffffff'
                h += f'<tr style="border-bottom: 1px solid #e0e0e0; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor=\'#f0f0f0\';" onmouseout="this.style.backgroundColor=\'{bg_color}\';">'
                
                for i, (col, v) in enumerate(row.items()):
                    fmt = f"{v:.1f}%" if isinstance(v,(int,float)) and '%' in col else f"{v:,.0f}" if isinstance(v,(int,float)) else str(v)
                    align = "left" if i == 0 else "center"
                    font_weight = "600" if i == 0 else "normal"
                    h += f'<td style="padding: 10px; text-align: {align}; vertical-align: middle; font-weight: {font_weight};">{fmt}</td>'
                
                h += '</tr>'
            
            h += '</tbody></table></div>'
            return h
        
        st.markdown(make_table(display_summary), unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M6.99 11L3 15l3.99 4v-3H14v-2H6.99v-3zM21 9l-3.99-4v3H10v2h7.01v3L21 9z"/></svg>
        <span style="font-size: 20px; font-weight: 700; color: #0f3d3e;">Brand Switching Details</span>
    </div>
""", unsafe_allow_html=True)
        st.caption("Top brand-to-brand switching flows (sorted by From Brand A→Z, then Customers High→Low)")
        
        switching_summary = data_processor.get_brand_switching_summary(df_display, top_n=20)
        
        if len(switching_summary) > 0:
            # Sort: From Brand ASC, then Customers DESC
            switching_summary = switching_summary.sort_values(
                by=['From_Brand', 'Customers'],
                ascending=[True, False]
            ).reset_index(drop=True)
            
            # Build table rows using list
            rows = []
            for _, row in switching_summary.iterrows():
                rows.append(
                    '<tr>'
                    f'<td class="from-brand">{row["From_Brand"]}</td>'
                    f'<td class="to-brand">{row["To_Brand"]}</td>'
                    f'<td class="customers-col">{row["Customers"]:,.0f}</td>'
                    f'<td class="pct-col">{row["Pct_of_From_Brand"]:.2f}%</td>'
                    '</tr>'
                )
            
            table_body = ''.join(rows)
            
            # Classy table without JavaScript
            html = '''
<style>
    .switching-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        border-radius: 8px;
        overflow: hidden;
    }
    .switching-table thead th {
        color: white;
        padding: 14px;
        text-align: center;
        font-weight: 600;
        position: sticky;
        top: 0;
        border-right: 1px solid rgba(255,255,255,0.15);
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .switching-table thead th:nth-child(1) {
        background: linear-gradient(135deg, #c94b4b 0%, #4b134f 100%);
    }
    .switching-table thead th:nth-child(2) {
        background: linear-gradient(135deg, #0575e6 0%, #021b79 100%);
    }
    .switching-table thead th:nth-child(3) {
        background: linear-gradient(135deg, #134e5e 0%, #71b280 100%);
    }
    .switching-table thead th:nth-child(4) {
        background: linear-gradient(135deg, #f12711 0%, #f5af19 100%);
    }
    .switching-table tbody tr {
        border-bottom: 1px solid #e0e0e0;
        transition: all 0.2s;
    }
    .switching-table tbody tr:hover {
        background-color: #f0f0f0;
        transform: scale(1.01);
    }
    .switching-table tbody td {
        padding: 12px;
        text-align: center;
        vertical-align: middle;
    }
    .switching-table tbody tr:nth-child(even) {
        background-color: #fafafa;
    }
    .from-brand {
        background-color: #ffebee !important;
        font-weight: 600;
        color: #c62828;
    }
    .to-brand {
        background-color: #e8f5e9 !important;
        font-weight: 600;
        color: #2e7d32;
    }
    .customers-col {
        font-weight: 600;
        color: #1565c0;
    }
    .pct-col {
        color: #f57c00;
        font-weight: 500;
    }
</style>
<div style="max-height: 600px; overflow-y: auto;">
    <table class="switching-table">
        <thead>
            <tr>
                <th style="width: 30%;">From Brand</th>
                <th style="width: 30%;">To Brand</th>
                <th style="width: 20%;">Customers</th>
                <th style="width: 20%;">% of From Brand</th>
            </tr>
        </thead>
        <tbody>''' + table_body + '''
        </tbody>
    </table>
</div>
'''
            
            st.markdown(html, unsafe_allow_html=True)
            st.info("💡 **คำอธิบาย:** % of From Brand = จำนวนลูกค้าที่ย้ายจาก Brand นั้น / ลูกค้าทั้งหมดของ Brand ในช่วง Before Period")
        else:
            st.warning("⚠️ ไม่พบข้อมูลการ switch ระหว่าง brand")
    
    # Tab 3: Loyalty (moved from tab6)
    with tab3:
        st.markdown("### � Cohort & Loyalty Analysis")
        st.caption("Analysis of customer retention and churn behavior between the two periods.")
        
        cohort_metrics = data_processor.calculate_cohort_metrics(df_display)
        
        if cohort_metrics:
            c1, c2, c3 = st.columns(3)
            with c1:
                retention_rate_fmt = f"{cohort_metrics['retention_rate']:.1f}"
                st.markdown(f"""
                <div class="premium-card" style="padding: 20px; text-align: center; border-left: 5px solid #2e7d32;">
                    <div style="font-size: 16px; color: #666; margin-bottom: 5px;">Retention Rate</div>
                    <div style="font-size: 32px; font-weight: 800; color: #2e7d32;">{retention_rate_fmt}%</div>
                    <div style="font-size: 12px; color: #666;">Customers who stayed with same brand</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                switch_rate_fmt = f"{cohort_metrics['switch_rate']:.1f}"
                st.markdown(f"""
                <div class="premium-card" style="padding: 20px; text-align: center; border-left: 5px solid #f57c00;">
                    <div style="font-size: 16px; color: #666; margin-bottom: 5px;">Switch Rate</div>
                    <div style="font-size: 32px; font-weight: 800; color: #f57c00;">{switch_rate_fmt}%</div>
                    <div style="font-size: 12px; color: #666;">Customers who switched brands</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                churn_rate_fmt_2 = f"{cohort_metrics['churn_rate']:.1f}"
                st.markdown(f"""
                <div class="premium-card" style="padding: 20px; text-align: center; border-left: 5px solid #c62828;">
                    <div style="font-size: 16px; color: #666; margin-bottom: 5px;">Churn Rate</div>
                    <div style="font-size: 32px; font-weight: 800; color: #c62828;">{churn_rate_fmt_2}%</div>
                    <div style="font-size: 12px; color: #666;">Customers lost from category</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("#### Customer Base Composition by Brand")
            
            # Get per-brand cohort metrics
            brand_cohort = data_processor.calculate_cohort_metrics_by_brand(df_display)
            
            if brand_cohort['brands']:
                # Brand filter for too many brands
                all_chart_brands = brand_cohort['brands']
                if len(all_chart_brands) > 6:
                    chart_brand_filter = st.multiselect(
                        "Select brands to display (max 10)",
                        options=all_chart_brands,
                        default=all_chart_brands[:6],
                        max_selections=10,
                        key="chart_brand_filter"
                    )
                else:
                    chart_brand_filter = all_chart_brands
                
                # Filter data based on selection
                if chart_brand_filter:
                    indices = [i for i, b in enumerate(brand_cohort['brands']) if b in chart_brand_filter]
                    filtered_brands = [brand_cohort['brands'][i] for i in indices]
                    filtered_retained = [brand_cohort['retained'][i] for i in indices]
                    filtered_switched = [brand_cohort['switched'][i] for i in indices]
                    filtered_churned = [brand_cohort['churned'][i] for i in indices]
                else:
                    filtered_brands = brand_cohort['brands']
                    filtered_retained = brand_cohort['retained']
                    filtered_switched = brand_cohort['switched']
                    filtered_churned = brand_cohort['churned']
                
                # Create grouped bar chart
                fig_comp = go.Figure()
                
                fig_comp.add_trace(go.Bar(
                    name='Retained',
                    x=filtered_brands,
                    y=filtered_retained,
                    marker_color='#2e7d32',
                    text=filtered_retained,
                    texttemplate='%{text:,.0f}',
                    textposition='auto'
                ))
                
                fig_comp.add_trace(go.Bar(
                    name='Switched',
                    x=filtered_brands,
                    y=filtered_switched,
                    marker_color='#f57c00',
                    text=filtered_switched,
                    texttemplate='%{text:,.0f}',
                    textposition='auto'
                ))
                
                fig_comp.add_trace(go.Bar(
                    name='Churned',
                    x=filtered_brands,
                    y=filtered_churned,
                    marker_color='#c62828',
                    text=filtered_churned,
                    texttemplate='%{text:,.0f}',
                    textposition='auto'
                ))
                
                fig_comp.update_layout(
                    title="Customer Fate by Brand (From Period 1)",
                    barmode='group',
                    height=450,
                    plot_bgcolor='white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis_tickangle=-45 if len(filtered_brands) > 4 else 0
                )
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("No brand data available for cohort chart.")
        else:
            st.info("No data available for cohort analysis.")
    
    # Tab 4: Charts (moved from tab3)
    with tab4:
        st.markdown("### �📈 Market Overview")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(visualizations.create_movement_type_pie(df_display), use_container_width=True)
        with c2:
            metric = st.selectbox("Metric", ['Net_Movement','Total_In','Total_Out','Stayed'])
            st.plotly_chart(visualizations.create_brand_comparison_bar(summary_df, metric), use_container_width=True)
            
        st.markdown("---")
        st.markdown("### ⚔️ Competitive Analysis (Net Gain/Loss)")
        
        # Brand Selector for Net Gain/Loss
        # Default to biggest winner or loser if available, else first brand
        # Get unique items with safety check
        if item_label in summary_df.columns:
            unique_items = sorted(summary_df[item_label].unique().tolist())
        elif 'Brand' in summary_df.columns:
            unique_items = sorted(summary_df['Brand'].unique().tolist())
        elif 'Product' in summary_df.columns:
            unique_items = sorted(summary_df['Product'].unique().tolist())
        else:
            unique_items = []
        
        if unique_items:
            default_brand_index = 0
            if kpis and kpis.get('winner_name') != "None":
                 try:
                     default_brand_index = unique_items.index(kpis['winner_name'])
                 except:
                     pass
                     
            target_brand = st.selectbox("Select Focus Brand", unique_items, index=default_brand_index, key="net_gain_loss_brand")
        
            # Create and display chart
            fig_net_flow = visualizations.create_net_gain_loss_chart(df_display, target_brand)
            st.plotly_chart(fig_net_flow, use_container_width=True)
        else:
            st.info("No brands available for competitive analysis.")
    
    # Tab 5: Raw (moved from tab4)
    with tab5:
        st.markdown("### Raw Data")
        st.dataframe(df_display, use_container_width=True, height=400)
        st.markdown("### Top 10 Flows")
        st.dataframe(data_processor.get_top_flows(df_display, n=10), use_container_width=True)
    
    # Tab 6: Export (moved from tab5)
    with tab6:
        st.markdown("### Export")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📊 Excel", utils.create_excel_export(df_display, summary_df), f"switching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with c2:
            st.download_button("📄 CSV", df_display.to_csv(index=False), f"switching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 40px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M12 2c-5.52 0-10 4.48-10 10s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">AI-Powered Insights</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("✨ Generate Complete Analysis"):
        ai_category = selected_categories[0] if selected_categories else None
        
        # Extract brands for highlighting
        # If user filtered by brands, use those; otherwise extract from data
        brands_for_ai = selected_brands if selected_brands else []
        
        # If no brands filtered, extract unique brands from data for highlighting
        if not brands_for_ai:
            special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED'}
            all_items = set()
            all_items.update(df_display['prod_2024'].unique())
            all_items.update(df_display['prod_2025'].unique())
            
            # Extract brands (first word) from products
            for item in all_items:
                if item not in special_categories:
                    # Extract brand (first word)
                    brand = item.split()[0] if item.split() else item
                    brands_for_ai.append(brand)
            
            # Remove duplicates and limit to top brands by customer count
            brands_for_ai = list(set(brands_for_ai))
            # Limit to top 10 brands for highlighting (avoid too many colors)
            if len(brands_for_ai) > 10:
                brand_customers = df_display.groupby(df_display['prod_2024'].apply(lambda x: x.split()[0] if x.split() and x not in special_categories else x))['customers'].sum()
                top_brands = brand_customers.nlargest(10).index.tolist()
                brands_for_ai = [b for b in brands_for_ai if b in top_brands]
        
        insights = ai_analyzer.generate_insights(df_display, summary_df, ai_category, brands_for_ai, analysis_mode, f"{period1_start} to {period1_end}", f"{period2_start} to {period2_end}")
        if insights:
            st.markdown(insights, unsafe_allow_html=True)
else:
    st.info("👈 Configure and click **Run Analysis**")
st.markdown("---")
st.markdown('<div style="text-align:center; color:#666">Everything-Switching | BigQuery & OpenAI</div>', unsafe_allow_html=True)
