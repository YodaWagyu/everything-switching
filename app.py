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

load_css()

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
        
        query = query_builder.build_switching_query(
            analysis_mode, 
            period1_start.strftime("%Y-%m-%d"), 
            period1_end.strftime("%Y-%m-%d"), 
            period2_start.strftime("%Y-%m-%d"), 
            period2_end.strftime("%Y-%m-%d"), 
            selected_category, 
            selected_brands, 
            product_name_contains or None,
            product_name_not_contains or None,
            primary_threshold, 
            barcode_mapping_text if analysis_mode == "Custom Type" else None,
            store_filter_type,
            store_opening_cutoff
        )
        utils.show_debug_query(query)
        df, gb_processed = bigquery_client.execute_query(query)
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
    utils.display_filter_summary(analysis_mode, period1_start.strftime("%Y-%m-%d"), period1_end.strftime("%Y-%m-%d"), period2_start.strftime("%Y-%m-%d"), period2_end.strftime("%Y-%m-%d"), display_category, selected_brands, product_name_contains, primary_threshold, len(utils.parse_barcode_mapping(barcode_mapping_text)) if analysis_mode == "Custom Type" else 0)
    
    # Placeholder for Executive KPIs - will be calculated after filtering
    # Will be rendered after filtering
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 1: Customer Flow</span>
    </div>
""", unsafe_allow_html=True)
    
    # Apply brand filtering based on view mode toggle (only shown when brands are filtered)
    df_display = df  # Default to full data
    
    if selected_brands:
        from modules import brand_filter
        
        # Show view mode toggle
        col_toggle, col_spacer = st.columns([4, 6])
        with col_toggle:
            view_mode = st.radio(
                "🔍 View Mode",
                options=['🎯 Focus View', '🌐 Category View'],
                index=0,  # Default to Focus View
                horizontal=True,
                help="🎯 Focus: Selected brands only | 🌐 Category: Full category with filtered brands highlighted",
                key="view_mode_toggle"
            )
        
        # Determine filter mode from selection
        filter_mode = 'filtered' if '🎯' in view_mode else 'full'
        
        # Apply client-side filter
        df_display = brand_filter.filter_dataframe_by_brands(df, selected_brands, filter_mode)
        
        # Show filter description
        if filter_mode == 'full':
            st.info(f"💡 **Category View**: Showing complete category with **{', '.join(selected_brands)}** highlighted")
    
    # Calculate summary AFTER determining df_display (this ensures AI gets correct data)
    summary_df = data_processor.calculate_brand_summary(df_display)
    
    # For Focus View: Remove OTHERS from summary table to show only focused brands
    # But keep OTHERS in df_display so Waterfall/Matrix can show Switch In from OTHERS
    if selected_brands and filter_mode == 'filtered':
        # Filter out OTHERS from summary (removes OTHERS row from tables)
        summary_df = summary_df[summary_df['Brand'] != 'OTHERS'].copy()
        # Note: We keep df_display as-is (with OTHERS flows) for Waterfall/Matrix visualization
    
    # Calculate full category summary (all brands)
    summary_df_full = data_processor.calculate_brand_summary(df)
    
    # For Category View: We need both full category data and filtered data
    # summary_df_full = all brands (for tables and category-wide KPIs)
    # summary_df_filtered = only selected brands from full category (for filtered KPIs)
    if selected_brands and filter_mode == 'full':
        # Category View: Filter selected brands from FULL category data
        # This gives us the selected brands' metrics within the full category context
        summary_df_filtered = summary_df_full[summary_df_full['Brand'].isin(selected_brands)].copy()
    else:
        summary_df_filtered = summary_df
    
    # Determine which summary to use for display tables
    # Category View: Use summary_df_full (all brands with 🎯 badges)
    # Focus View: Use summary_df (filtered brands only)
    if selected_brands and filter_mode == 'full':
        summary_df_display = summary_df_full
    else:
        summary_df_display = summary_df
    
    # --- Executive KPIs (Hybrid approach for Category View) ---
    if selected_brands and filter_mode == 'full':
        # Category View: Use hybrid KPIs (show both category + filtered)
        kpis = data_processor.calculate_hybrid_kpis(summary_df_full, summary_df_filtered, selected_brands)
    else:
        # Focus View or No Filter: Use standard KPIs
        kpis = data_processor.calculate_executive_kpis(summary_df, summary_df_full)
    
    # Render Executive Summary Section at the top (but calculated here after filtering)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Executive Summary</span>
    </div>
    """, unsafe_allow_html=True)
    
    if kpis:
        # Check if we're in Category View with hybrid KPIs
        is_hybrid = 'category' in kpis and 'filtered' in kpis
        
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            if is_hybrid:
                total_cat_fmt = utils.format_number(kpis['category']['total_movement'])
                total_filt_fmt = utils.format_number(kpis['filtered']['total_movement'])
                pct = kpis['filtered_percentage']
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Total Movement</div>
                    <div style="font-size: 24px; font-weight: 800; color: #0f3d3e;">{total_cat_fmt}</div>
                    <div style="font-size: 11px; color: #888; margin-top: 5px;">Category-wide</div>
                    <div style="font-size: 16px; font-weight: 600; color: #f57c00; margin-top: 8px;">🎯 {total_filt_fmt}</div>
                    <div style="font-size: 10px; color: #f57c00;">{pct}% of category</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                total_movement_fmt = utils.format_number(kpis['total_movement'])
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Total Movement</div>
                    <div style="font-size: 24px; font-weight: 800; color: #0f3d3e;">{total_movement_fmt}</div>
                    <div style="font-size: 12px; color: #666;">Customers</div>
                </div>
                """, unsafe_allow_html=True)
            
        with k2:
            if is_hybrid:
                net_cat = kpis['category']['net_category_movement']
                net_filt = kpis['filtered']['net_category_movement']
                color = "#2e7d32" if net_cat >= 0 else "#c62828"
                icon = "▲" if net_cat >= 0 else "▼"
                net_cat_fmt = utils.format_number(abs(net_cat))
                net_filt_fmt = utils.format_number(abs(net_filt))
                filt_icon = "▲" if net_filt >= 0 else "▼"
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Net Movement</div>
                    <div style="font-size: 24px; font-weight: 800; color: {color};">{icon} {net_cat_fmt}</div>
                    <div style="font-size: 11px; color: #888; margin-top: 5px;">Category-wide</div>
                    <div style="font-size: 16px; font-weight: 600; color: #f57c00; margin-top: 8px;">🎯 {filt_icon} {net_filt_fmt}</div>
                    <div style="font-size: 10px; color: #f57c00;">Filtered brands</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                net_cat = kpis['net_category_movement']
                color = "#2e7d32" if net_cat >= 0 else "#c62828"
                icon = "▲" if net_cat >= 0 else "▼"
                net_cat_fmt = utils.format_number(abs(net_cat))
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Net Movement</div>
                    <div style="font-size: 24px; font-weight: 800; color: {color};">{icon} {net_cat_fmt}</div>
                    <div style="font-size: 12px; color: {color};">Total In - Total Out</div>
                </div>
                """, unsafe_allow_html=True)
            
        with k3:
            if is_hybrid:
                winner_cat_name = kpis['category']['winner_name']
                winner_cat_val = kpis['category']['winner_val']
                winner_filt_name = kpis['filtered']['winner_name']
                winner_filt_val = kpis['filtered']['winner_val']
                winner_cat_fmt = utils.format_number(winner_cat_val)
                winner_filt_fmt = utils.format_number(winner_filt_val)
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Biggest Winner</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f3d3e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{winner_cat_name}</div>
                    <div style="font-size: 12px; font-weight: 600; color: #2e7d32;">+{winner_cat_fmt}</div>
                    <div style="font-size: 10px; color: #888; margin-top: 5px;">Category</div>
                    <div style="font-size: 14px; font-weight: 700; color: #f57c00; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">🎯 {winner_filt_name}</div>
                    <div style="font-size: 11px; font-weight: 500; color: #f57c00;">+{winner_filt_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                winner_val_fmt = utils.format_number(kpis['winner_val'])
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Biggest Winner</div>
                    <div style="font-size: 18px; font-weight: 800; color: #0f3d3e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{kpis['winner_name']}</div>
                    <div style="font-size: 14px; font-weight: 600; color: #2e7d32;">+{winner_val_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
            
        with k4:
            if is_hybrid:
                loser_cat_name = kpis['category']['loser_name']
                loser_cat_val = kpis['category']['loser_val']
                loser_filt_name = kpis['filtered']['loser_name']
                loser_filt_val = kpis['filtered']['loser_val']
                loser_cat_fmt = utils.format_number(abs(loser_cat_val))
                loser_filt_fmt = utils.format_number(abs(loser_filt_val))
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Biggest Loser</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f3d3e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{loser_cat_name}</div>
                    <div style="font-size: 12px; font-weight: 600; color: #c62828;">{loser_cat_fmt}</div>
                    <div style="font-size: 10px; color: #888; margin-top: 5px;">Category</div>
                    <div style="font-size: 14px; font-weight: 700; color: #f57c00; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">🎯 {loser_filt_name}</div>
                    <div style="font-size: 11px; font-weight: 500; color: #f57c00;">{loser_filt_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                loser_val_fmt = utils.format_number(kpis['loser_val'])
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Biggest Loser</div>
                    <div style="font-size: 18px; font-weight: 800; color: #0f3d3e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{kpis['loser_name']}</div>
                    <div style="font-size: 14px; font-weight: 600; color: #c62828;">{loser_val_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
            
        with k5:
            if is_hybrid:
                churn_cat = kpis['category']['churn_rate']
                churn_filt = kpis['filtered']['churn_rate']
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Attrition Rate</div>
                    <div style="font-size: 24px; font-weight: 800; color: #c62828;">{churn_cat:.1f}%</div>
                    <div style="font-size: 11px; color: #888; margin-top: 5px;">Category-wide</div>
                    <div style="font-size: 16px; font-weight: 600; color: #f57c00; margin-top: 8px;">🎯 {churn_filt:.1f}%</div>
                    <div style="font-size: 10px; color: #f57c00;">Filtered brands</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                churn_rate_fmt = f"{kpis['churn_rate']:.1f}"
                st.markdown(f"""
                <div class="premium-card" style="padding: 15px; text-align: center;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Attrition Rate</div>
                    <div style="font-size: 24px; font-weight: 800; color: #c62828;">{churn_rate_fmt}%</div>
                    <div style="font-size: 12px; color: #666;">Total Out / Total</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Determine data source for Sankey based on View Mode
    # Category View: Use full category data (df) to show all brands
    # Focus View: Use filtered data (df_display) to show only focused brands
    if selected_brands and filter_mode == 'full':
        sankey_df = df  # Full category data
        highlighted_brands = selected_brands
    else:
        sankey_df = df_display  # Filtered data
        highlighted_brands = None
    
    labels, sources, targets, values = data_processor.prepare_sankey_data(sankey_df)
    st.plotly_chart(visualizations.create_sankey_diagram(labels, sources, targets, values, highlighted_brands), use_container_width=True)
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
    available_brands_for_analysis = summary_df_display['Brand'].tolist()
    if available_brands_for_analysis:
        # Add badge to filtered brands in Category View
        if selected_brands and filter_mode == 'full':
            brand_options = [f"🎯 {brand}" if brand in selected_brands else brand for brand in available_brands_for_analysis]
        else:
            brand_options = available_brands_for_analysis
        
        selected_focus_brand = st.selectbox("Select brand", brand_options, key="focus_brand")
        
        # Remove badge for data processing
        selected_focus_brand_clean = selected_focus_brand.replace("🎯 ", "")
        
        if selected_focus_brand_clean:
            st.plotly_chart(visualizations.create_waterfall_chart(data_processor.prepare_waterfall_data(df_display, selected_focus_brand_clean), selected_focus_brand_clean), use_container_width=True)
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
                    # Add badge for filtered brands in Category View
                    if i == 0 and selected_brands and filter_mode == 'full' and v in selected_brands:
                        fmt = f"🎯 {v}"
                    else:
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
                
            st.markdown("#### Customer Base Composition")
            comp_data = pd.DataFrame({
                'Type': ['Retained', 'Switched', 'Churned'],
                'Customers': [cohort_metrics['stayed_customers'], cohort_metrics['switch_out_customers'], cohort_metrics['gone_customers']]
            })
            fig_comp = go.Figure(data=[go.Bar(
                x=comp_data['Type'], 
                y=comp_data['Customers'],
                marker_color=['#2e7d32', '#f57c00', '#c62828'],
                text=comp_data['Customers'],
                texttemplate='%{text:,}',
                textposition='auto'
            )])
            fig_comp.update_layout(title="Customer Fate (From Period 1)", height=400, plot_bgcolor='white')
            st.plotly_chart(fig_comp, use_container_width=True)
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
        default_brand_index = 0
        if kpis and kpis.get('winner_name') != "None":
             try:
                 default_brand_index = sorted(summary_df['Brand'].unique().tolist()).index(kpis['winner_name'])
             except:
                 pass
                 
        target_brand = st.selectbox("Select Focus Brand", sorted(summary_df['Brand'].unique()), index=default_brand_index, key="net_gain_loss_brand")
        
        # Create and display chart
        fig_net_flow = visualizations.create_net_gain_loss_chart(df_display, target_brand)
        st.plotly_chart(fig_net_flow, use_container_width=True)
    
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
