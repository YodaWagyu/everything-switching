"""
Everything-Switching Analysis Application
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Original by Kritin Kayaras
© 2025 All Rights Reserved
"""
import streamlit as st
from datetime import datetime, timedelta
from modules import bigquery_client, data_processor, visualizations, utils, query_builder, ai_analyzer, auth, tracking
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

# Admin Page Selector (only for admin users)
admin_page_mode = "analysis"  # Default
if auth.is_admin():
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0f3d3e 0%, #1a5f60 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <div style="color: white; font-weight: 700; font-size: 14px;">🔐 Admin Mode</div>
        </div>
        """, unsafe_allow_html=True)
        admin_page_mode = st.radio(
            "Select View:",
            ["📊 Analysis", "📈 Admin Dashboard"],
            key="admin_page_mode",
            horizontal=True
        )
        admin_page_mode = "dashboard" if "Dashboard" in admin_page_mode else "analysis"
        st.markdown("---")

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

# Global CSS for Chart Containers - rounded borders like KPI cards
st.markdown("""
<style>
/* Plotly chart containers - rounded borders and shadow */
[data-testid="stPlotlyChart"] > div {
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# ============ ADMIN DASHBOARD PAGE (Separate from Analysis) ============
if admin_page_mode == "dashboard":
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        <span style="font-size: 28px; font-weight: 800; color: #0f3d3e;">📊 Admin Dashboard - Usage Analytics</span>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Get analytics data
        analytics = tracking.get_analytics_summary()
        
        # KPI Cards Row
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.metric("📈 Total Sessions", f"{analytics['total_sessions']:,}", f"+{analytics['sessions_today']} today")
        with kpi_cols[1]:
            st.metric("🔍 Total Queries", f"{analytics['total_queries']:,}", f"+{analytics['queries_today']} today")
        with kpi_cols[2]:
            st.metric("⚡ Avg Query Time", f"{analytics['avg_query_time_ms']:.0f}ms")
        with kpi_cols[3]:
            st.metric("🌐 Unique IPs", f"{analytics['unique_ips']:,}")
        
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        
        # Second row of KPIs
        kpi_cols2 = st.columns(3)
        with kpi_cols2[0]:
            st.metric("🤖 AI Generations", f"{analytics['ai_generations']:,}")
        with kpi_cols2[1]:
            st.metric("📥 Total Exports", f"{analytics['total_exports']:,}")
        with kpi_cols2[2]:
            role_df = tracking.get_role_distribution()
            if not role_df.empty:
                admin_count = role_df[role_df['user_role'] == 'admin']['count'].sum() if 'admin' in role_df['user_role'].values else 0
                user_count = role_df[role_df['user_role'] == 'user']['count'].sum() if 'user' in role_df['user_role'].values else 0
                st.metric("👤 Admin/User Sessions", f"{admin_count} / {user_count}")
        
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        
        # Charts Row
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            st.subheader("📈 Daily Usage Trend (14 days)")
            daily_df = tracking.get_daily_usage(14)
            if not daily_df.empty and len(daily_df) > 0:
                fig_daily = go.Figure()
                fig_daily.add_trace(go.Scatter(
                    x=daily_df['date'],
                    y=daily_df['sessions'],
                    mode='lines+markers',
                    name='Sessions',
                    line=dict(color='#0f3d3e', width=3),
                    marker=dict(size=10)
                ))
                fig_daily.add_trace(go.Scatter(
                    x=daily_df['date'],
                    y=daily_df['queries'],
                    mode='lines+markers',
                    name='Queries',
                    line=dict(color='#4ECDC4', width=3),
                    marker=dict(size=10)
                ))
                fig_daily.update_layout(
                    height=350,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    xaxis_title="",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info("📊 No usage data yet - start using the app to see trends!")
        
        with chart_cols[1]:
            st.subheader("📊 Events by Type")
            events_type_df = tracking.get_events_by_type()
            if not events_type_df.empty and len(events_type_df) > 0:
                fig_events = go.Figure(data=[
                    go.Bar(
                        x=events_type_df['event_type'],
                        y=events_type_df['count'],
                        marker_color=['#0f3d3e', '#4ECDC4', '#FF6B6B', '#F7DC6F', '#BB8FCE'][:len(events_type_df)]
                    )
                ])
                fig_events.update_layout(
                    height=350,
                    margin=dict(l=20, r=20, t=30, b=20),
                    xaxis_title="Event Type",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig_events, use_container_width=True)
            else:
                st.info("📊 No events recorded yet")
        
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        
        # Recent Sessions Table
        st.subheader("📋 Recent Sessions")
        sessions_df = tracking.get_recent_sessions(15)
        if not sessions_df.empty:
            display_sessions = sessions_df.copy()
            display_sessions.columns = ['Session ID', 'Role', 'IP Address', 'Start Time', 'Last Activity', 'Events']
            st.dataframe(display_sessions, use_container_width=True, hide_index=True)
        else:
            st.info("No sessions recorded yet")
        
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        
        # Recent Activity Log with Details
        st.subheader("📜 Recent Activity Log (with Filter Details)")
        events_detail_df = tracking.get_recent_events(30)
        if not events_detail_df.empty:
            events_detail_df.columns = ['Time', 'Role', 'IP', 'Event', 'Details']
            st.dataframe(events_detail_df, use_container_width=True, hide_index=True)
        else:
            st.info("No activity recorded yet")
            
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown('<div style="text-align:center; color:#666">Everything-Switching | Admin Dashboard</div>', unsafe_allow_html=True)
    st.stop()  # Stop here - don't show analysis page

# Add logout button in sidebar
with st.sidebar:
    if st.button("🚪 Logout", use_container_width=True):
        auth.logout()

if 'query_executed' not in st.session_state:
    st.session_state.query_executed = False

if 'cross_category_executed' not in st.session_state:
    st.session_state.cross_category_executed = False

if 'sales_analysis_executed' not in st.session_state:
    st.session_state.sales_analysis_executed = False

if 'previous_analysis_mode' not in st.session_state:
    st.session_state.previous_analysis_mode = None

# =====================================================
# ANALYSIS MODE SELECTOR
# =====================================================
st.sidebar.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; margin-top: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z"/></svg>
        <span style="font-size: 18px; font-weight: 700; color: white;">Analysis Mode</span>
    </div>
""", unsafe_allow_html=True)

analysis_mode = st.sidebar.radio(
    "Select Mode",
    ["Brand/Product Switch", "Cross-Category Switch", "💰 Sales Analysis (Testing)"],
    key="analysis_mode_selector",
    label_visibility="collapsed",
    horizontal=False  # Vertical layout for 3 options
)

# Clear session state when mode changes to prevent stale data (WARN-02 fix)
if st.session_state.previous_analysis_mode != analysis_mode:
    if st.session_state.previous_analysis_mode is not None:
        # Mode changed - clear relevant session state
        keys_to_clear = [
            'results_df', 'cross_category_df', 'sales_analysis_df',
            'gb_processed', 'cross_category_gb_processed', 'sales_gb_processed'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        # Reset execution flags to False (don't delete, re-initialize)
        st.session_state.query_executed = False
        st.session_state.cross_category_executed = False
        st.session_state.sales_analysis_executed = False
    st.session_state.previous_analysis_mode = analysis_mode

st.sidebar.markdown("---")

# =====================================================
# DATE RANGE FILTERS (Common for both modes)
# =====================================================
st.sidebar.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; margin-top: 10px;">
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

# =====================================================
# CONDITIONAL FILTER PANELS BASED ON ANALYSIS MODE
# =====================================================

available_categories = bigquery_client.get_categories()

# Define is_sales_mode at global scope for accessibility in query building
is_sales_mode = analysis_mode == "💰 Sales Analysis (Testing)"

if analysis_mode == "Cross-Category Switch":
    # =====================================================
    # CROSS-CATEGORY SWITCH FILTERS
    # =====================================================
    st.sidebar.markdown("""
        <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
            <div style="color: white; font-weight: 700; font-size: 14px;">🔀 Cross-Category Mode</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 12px;">Track customers moving between categories</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Source Category/SubCategory
    with st.sidebar.expander("🎯 Source (First Period)", expanded=True):
        source_categories = st.multiselect(
            "Category", 
            available_categories, 
            key="source_categories",
            help="ลูกค้าที่ซื้อจาก Category เหล่านี้ใน First Period"
        )
        
        source_subcategories = []
        if source_categories:
            all_source_subcats = []
            for cat in source_categories:
                subcats = bigquery_client.get_subcategories(cat)
                all_source_subcats.extend(subcats)
            all_source_subcats = list(set(all_source_subcats))
            source_subcategories = st.multiselect(
                "SubCategory (Optional)", 
                all_source_subcats,
                key="source_subcategories",
                help="ถ้าไม่เลือก = ทุก SubCategory ใน Category ที่เลือก"
            )
    
    # Target Category/SubCategory
    with st.sidebar.expander("🎯 Target (After Period)", expanded=True):
        target_categories = st.multiselect(
            "Category", 
            available_categories, 
            key="target_categories",
            help="Category ที่ต้องการดูว่าลูกค้าย้ายไปหรือเปล่า"
        )
        
        target_subcategories = []
        if target_categories:
            all_target_subcats = []
            for cat in target_categories:
                subcats = bigquery_client.get_subcategories(cat)
                all_target_subcats.extend(subcats)
            all_target_subcats = list(set(all_target_subcats))
            target_subcategories = st.multiselect(
                "SubCategory (Optional)", 
                all_target_subcats,
                key="target_subcategories",
                help="ถ้าไม่เลือก = ทุก SubCategory ใน Category ที่เลือก"
            )
    
    # Advanced Settings for Cross-Category
    with st.sidebar.expander("⚙️ Advanced Settings", expanded=False):
        primary_threshold = st.slider("Primary %", float(config.MIN_PRIMARY_THRESHOLD*100), float(config.MAX_PRIMARY_THRESHOLD*100), float(config.DEFAULT_PRIMARY_THRESHOLD*100), step=5.0) / 100.0
    
    # Set these to None for Cross-Category mode
    selected_categories = source_categories
    selected_subcategories = source_subcategories
    selected_brands = []
    product_name_contains = None
    product_name_not_contains = None
    barcode_mapping_text = ""

else:
    # =====================================================
    # BRAND/PRODUCT SWITCH FILTERS (Original)
    # =====================================================
    # This handles both "Brand/Product Switch" and "💰 Sales Analysis (Testing)" modes
    # They share the same filters but Sales Analysis mode will use different query with sales columns
    
    is_sales_mode = analysis_mode == "💰 Sales Analysis (Testing)"
    
    if is_sales_mode:
        st.sidebar.markdown("""
            <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
                <div style="color: white; font-weight: 700; font-size: 14px;">💰 Sales Analysis Mode</div>
                <div style="color: rgba(255,255,255,0.8); font-size: 12px;">Testing customer movement with sales data</div>
            </div>
        """, unsafe_allow_html=True)
    
    with st.sidebar.expander("🔍 Product Filters", expanded=True):
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

    with st.sidebar.expander("⚙️ Advanced Settings", expanded=False):
        primary_threshold = st.slider("Primary %", float(config.MIN_PRIMARY_THRESHOLD*100), float(config.MAX_PRIMARY_THRESHOLD*100), float(config.DEFAULT_PRIMARY_THRESHOLD*100), step=5.0) / 100.0

    # Custom Barcode Mapping - Between Advanced Settings and Run Analysis
    with st.sidebar.expander("🏷️ Custom Barcode Mode", expanded=False):
        st.caption("Map barcodes to custom types (bypasses brand filter)")
        barcode_mapping_text = st.text_area(
            "Paste barcode mapping", 
            "", 
            height=100, 
            placeholder="8850002016620\tMEN\n8850002024458\tBasic\n\n(Copy from Excel: Barcode | Type)",
            help="Paste from Excel (tab-separated) or use comma",
            key="barcode_mapping_text_area",
            label_visibility="collapsed"
        )
        
        if barcode_mapping_text and barcode_mapping_text.strip():
            # Count valid mappings
            lines = [l.strip() for l in barcode_mapping_text.strip().split('\n') if l.strip()]
            valid_count = sum(1 for l in lines if '\t' in l or ',' in l or '  ' in l)
            st.caption(f"✓ {valid_count} barcodes mapped")
    
    # Initialize cross-category variables to None
    source_categories = []
    source_subcategories = []
    target_categories = []
    target_subcategories = []

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)

# =====================================================
# CROSS-CATEGORY SWITCH MODE
# =====================================================
if analysis_mode == "Cross-Category Switch":
    if run_analysis or st.session_state.cross_category_executed:
        if run_analysis:
            # Validate required fields
            if not source_categories:
                st.error("⚠️ Please select at least one Source Category to run the analysis.")
                st.stop()
            if not target_categories:
                st.error("⚠️ Please select at least one Target Category to run the analysis.")
                st.stop()
            
            # Build and execute Cross-Category query
            cross_cat_query = query_builder.build_cross_category_query(
                period1_start.strftime("%Y-%m-%d"),
                period1_end.strftime("%Y-%m-%d"),
                period2_start.strftime("%Y-%m-%d"),
                period2_end.strftime("%Y-%m-%d"),
                source_categories,
                source_subcategories if source_subcategories else None,
                target_categories,
                target_subcategories if target_subcategories else None,
                primary_threshold,
                store_filter_type,
                store_opening_cutoff
            )
            
            utils.show_debug_query(cross_cat_query)
            df_cross, gb_processed = bigquery_client.execute_query(cross_cat_query)
            st.session_state.cross_category_df = df_cross
            st.session_state.cross_category_gb_processed = gb_processed
            st.session_state.cross_category_executed = True
            st.session_state.cross_category_source = source_categories
            st.session_state.cross_category_target = target_categories
            st.session_state.cross_category_source_subcats = source_subcategories if source_subcategories else []
            st.session_state.cross_category_target_subcats = target_subcategories if target_subcategories else []
            st.session_state.cross_category_query = cross_cat_query  # Store for View SQL
            
            # Track query
            try:
                if 'tracking_session_id' in st.session_state:
                    query_details = {
                        'mode': 'cross_category',
                        'source_categories': source_categories,
                        'target_categories': target_categories,
                        'period1': f"{period1_start} to {period1_end}",
                        'period2': f"{period2_start} to {period2_end}",
                        'gb_processed': round(gb_processed, 2) if gb_processed else 0
                    }
                    tracking.log_event(
                        st.session_state.tracking_session_id, 
                        'query', 
                        query_details,
                        duration_ms=None
                    )
            except Exception:
                pass  # Tracking errors should not break the app
        
        # Get stored results
        df_cross = st.session_state.get('cross_category_df')
        gb_processed = st.session_state.get('cross_category_gb_processed', 0)
        
        if df_cross is None or len(df_cross) == 0:
            st.warning("⚠️ No data found for the selected categories.")
            st.stop()
        
        # Admin-only: Cost Display
        if auth.is_admin() and gb_processed > 0:
            st.markdown("---")
            utils.display_cost_info(gb_processed)
        
        # =====================================================
        # CROSS-CATEGORY RESULTS DISPLAY
        # =====================================================
        
        # Header
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 20px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#6366f1"><path d="M12 2l-5.5 9h11L12 2zm0 3.84L13.93 9h-3.87L12 5.84zM17.5 13c-2.49 0-4.5 2.01-4.5 4.5s2.01 4.5 4.5 4.5 4.5-2.01 4.5-4.5-2.01-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5zM3 21.5h8v-8H3v8zm2-6h4v4H5v-4z"/></svg>
            <span style="font-size: 28px; font-weight: 800; color: #6366f1;">Cross-Category Switching Analysis</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show source and target summary (include subcategories if selected)
        source_cats = st.session_state.get('cross_category_source', source_categories)
        source_subcats = st.session_state.get('cross_category_source_subcats', [])
        target_cats = st.session_state.get('cross_category_target', target_categories)
        target_subcats = st.session_state.get('cross_category_target_subcats', [])
        
        # Format display: Category on main line, subcategories below (if selected)
        source_cat_display = ", ".join(source_cats)
        source_subcat_display = ", ".join(source_subcats) if source_subcats else ""
        
        target_cat_display = ", ".join(target_cats)
        target_subcat_display = ", ".join(target_subcats) if target_subcats else ""
        
        # Display source and target summary using Streamlit columns (more reliable than HTML)
        with st.container():
            col_src, col_arrow, col_tgt = st.columns([2, 1, 2])
            
            with col_src:
                st.markdown("**SOURCE CATEGORY**")
                st.markdown(f"### {source_cat_display}")
                if source_subcat_display:
                    st.caption(f"↳ {source_subcat_display}")
            
            with col_arrow:
                st.markdown("")
                st.markdown("# →")
            
            with col_tgt:
                st.markdown("**TARGET CATEGORY**")
                st.markdown(f"### {target_cat_display}")
                if target_subcat_display:
                    st.caption(f"↳ {target_subcat_display}")
        
        # Calculate KPIs
        cross_kpis = data_processor.calculate_cross_category_kpis(df_cross, target_categories)
        
        # KPI Cards
        if cross_kpis:
            k1, k2, k3, k4, k5 = st.columns(5)
            
            card_base = """
                background: white; 
                padding: 16px 20px; 
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                height: 100%;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            """
            
            with k1:
                st.markdown(f"""
                <div style="{card_base}">
                    <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Source Customers</div>
                    <div style="font-size: 28px; font-weight: 500; color: #111827;">{cross_kpis['total_source_customers']:,}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">First Period</div>
                </div>
                """, unsafe_allow_html=True)
            
            with k2:
                st.markdown(f"""
                <div style="{card_base}">
                    <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Stayed</div>
                    <div style="font-size: 28px; font-weight: 500; color: #16a34a;">{cross_kpis['stayed_pct']:.1f}%</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{cross_kpis['stayed']:,} customers</div>
                </div>
                """, unsafe_allow_html=True)
            
            with k3:
                st.markdown(f"""
                <div style="{card_base}">
                    <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Switched to Target</div>
                    <div style="font-size: 28px; font-weight: 500; color: #6366f1;">{cross_kpis['target_switched_pct']:.1f}%</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{cross_kpis['target_switched']:,} customers</div>
                </div>
                """, unsafe_allow_html=True)
            
            with k4:
                st.markdown(f"""
                <div style="{card_base}">
                    <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Gone (No Purchase)</div>
                    <div style="font-size: 28px; font-weight: 500; color: #dc2626;">{cross_kpis['gone_pct']:.1f}%</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{cross_kpis['gone']:,} customers</div>
                </div>
                """, unsafe_allow_html=True)
            
            with k5:
                st.markdown(f"""
                <div style="{card_base}">
                    <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Top Target</div>
                    <div style="font-size: 20px; font-weight: 500; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{cross_kpis['top_target']}">{cross_kpis['top_target']}</div>
                    <div style="font-size: 12px; color: #6366f1; margin-top: 4px;">{cross_kpis['top_target_pct']:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
        
        
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        
        # Sankey Diagram for Cross-Category
        st.markdown("### 📊 Customer Flow (Sankey Diagram)")
        labels, sources, targets, values, sankey_link_colors, sankey_node_colors = data_processor.prepare_cross_category_sankey_data(df_cross)
        if labels and sources:
            st.plotly_chart(visualizations.create_sankey_diagram(labels, sources, targets, values, [], link_colors=sankey_link_colors, node_colors_override=sankey_node_colors), use_container_width=True)
            st.caption("🟢 Stayed | 🔵 Switched | 🔴 Gone")
        else:
            st.info("No flow data to display")
        
        # Summary Table with Styled Header (HTML like Brand Switch)
        st.markdown("### 📋 Cross-Category Flow Summary")
        summary_df = data_processor.calculate_cross_category_summary(df_cross)
        if not summary_df.empty:
            # Build HTML table rows
            rows = []
            for _, row in summary_df.iterrows():
                move_type = row.get('move_type', '')
                move_class = 'stayed-type' if move_type == 'stayed' else ('gone-type' if move_type == 'gone' else 'switched-type')
                rows.append(
                    '<tr>'
                    f'<td class="source-col">{row["Source"]}</td>'
                    f'<td class="target-col">{row["Target"]}</td>'
                    f'<td class="customers-col">{row["Customers"]:,.0f}</td>'
                    f'<td class="pct-col">{row["Pct"]:.1f}%</td>'
                    f'<td class="{move_class}">{move_type}</td>'
                    '</tr>'
                )
            
            table_body = ''.join(rows)
            
            html = '''
<style>
    .cross-cat-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-radius: 8px;
        overflow: hidden;
    }
    .cross-cat-table thead th {
        color: white;
        padding: 14px;
        text-align: center;
        font-weight: 600;
        position: sticky;
        top: 0;
        border-right: 1px solid rgba(255,255,255,0.15);
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .cross-cat-table thead th:nth-child(1) {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    }
    .cross-cat-table thead th:nth-child(2) {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    }
    .cross-cat-table thead th:nth-child(3) {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
    }
    .cross-cat-table thead th:nth-child(4) {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    .cross-cat-table thead th:nth-child(5) {
        background: linear-gradient(135deg, #64748b 0%, #475569 100%);
    }
    .cross-cat-table tbody tr {
        border-bottom: 1px solid #e0e0e0;
        transition: all 0.2s;
    }
    .cross-cat-table tbody tr:hover {
        background-color: #f0f0f0;
    }
    .cross-cat-table tbody td {
        padding: 12px;
        text-align: center;
        vertical-align: middle;
    }
    .cross-cat-table tbody tr:nth-child(even) {
        background-color: #fafafa;
    }
    .source-col {
        background-color: #eef2ff !important;
        font-weight: 600;
        color: #4f46e5;
    }
    .target-col {
        background-color: #f5f3ff !important;
        font-weight: 600;
        color: #7c3aed;
    }
    .customers-col {
        font-weight: 600;
        color: #0284c7;
    }
    .pct-col {
        color: #d97706;
        font-weight: 500;
    }
    .stayed-type {
        background-color: #dcfce7 !important;
        color: #16a34a;
        font-weight: 600;
    }
    .gone-type {
        background-color: #fee2e2 !important;
        color: #dc2626;
        font-weight: 600;
    }
    .switched-type {
        background-color: #e0e7ff !important;
        color: #4f46e5;
        font-weight: 600;
    }
</style>
<div style="max-height: 400px; overflow-y: auto;">
<table class="cross-cat-table">
    <thead>
        <tr>
            <th>Source</th>
            <th>Target</th>
            <th>Customers</th>
            <th>Percentage</th>
            <th>Move Type</th>
        </tr>
    </thead>
    <tbody>
''' + table_body + '''
    </tbody>
</table>
</div>
'''
            st.markdown(html, unsafe_allow_html=True)
        
        # Drill-down to Brand Level
        st.markdown("### 🔍 Drill-Down to Brand Level")
        
        # Get switched flows for drill-down selection
        switched_df = df_cross[df_cross['move_type'] == 'switched']
        if not switched_df.empty:
            # Get unique source-target combinations
            flow_options = switched_df.groupby(['source_label', 'target_label'])['customers'].sum().reset_index()
            flow_options = flow_options.sort_values('customers', ascending=False)
            flow_options['display'] = flow_options.apply(
                lambda x: f"{x['source_label']} → {x['target_label']} ({x['customers']:,} customers)", 
                axis=1
            )
            
            selected_flow = st.selectbox(
                "Select a flow to drill-down:",
                options=flow_options['display'].tolist(),
                key="cross_cat_drilldown"
            )
            
            if selected_flow:
                # Parse selected flow
                selected_row = flow_options[flow_options['display'] == selected_flow].iloc[0]
                source_label = selected_row['source_label']
                target_label = selected_row['target_label']
                
                # Get brand breakdown
                brand_df = data_processor.prepare_cross_category_brand_drilldown(df_cross, source_label, target_label)
                
                if not brand_df.empty:
                    st.markdown(f"**Brands in {target_label}:**")
                    
                    # Build HTML table for brand drill-down
                    brand_rows = []
                    for _, brow in brand_df.iterrows():
                        brand_rows.append(
                            '<tr>'
                            f'<td class="brand-name">{brow["Brand"]}</td>'
                            f'<td class="brand-customers">{brow["Customers"]:,.0f}</td>'
                            f'<td class="brand-pct">{brow["Pct"]:.1f}%</td>'
                            '</tr>'
                        )
                    
                    brand_table_body = ''.join(brand_rows)
                    
                    brand_html = '''
<style>
    .brand-drill-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-radius: 6px;
        overflow: hidden;
    }
    .brand-drill-table thead th {
        color: white;
        padding: 12px;
        text-align: center;
        font-weight: 600;
    }
    .brand-drill-table thead th:nth-child(1) {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    .brand-drill-table thead th:nth-child(2) {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
    }
    .brand-drill-table thead th:nth-child(3) {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    .brand-drill-table tbody tr {
        border-bottom: 1px solid #e0e0e0;
    }
    .brand-drill-table tbody tr:hover {
        background-color: #f0f0f0;
    }
    .brand-drill-table tbody td {
        padding: 10px;
        text-align: center;
    }
    .brand-drill-table tbody tr:nth-child(even) {
        background-color: #fafafa;
    }
    .brand-name {
        font-weight: 600;
        color: #059669;
    }
    .brand-customers {
        font-weight: 600;
        color: #0284c7;
    }
    .brand-pct {
        color: #d97706;
        font-weight: 500;
    }
</style>
<div style="max-height: 350px; overflow-y: auto;">
<table class="brand-drill-table">
    <thead>
        <tr>
            <th>Brand</th>
            <th>Customers</th>
            <th>% of Flow</th>
        </tr>
    </thead>
    <tbody>
''' + brand_table_body + '''
    </tbody>
</table>
</div>
'''
                    st.markdown(brand_html, unsafe_allow_html=True)
                else:
                    st.info("No brand data available for this flow.")
        else:
            st.info("No switching flows found between source and target categories.")
        
        # Export
        st.markdown("### 📥 Export Data")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv = df_cross.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Raw Data (CSV)",
                data=csv,
                file_name=f"cross_category_{source_cat_display.replace(', ', '_')}_to_{target_cat_display.replace(', ', '_')}.csv",
                mime="text/csv"
            )
        with col_exp2:
            if not summary_df.empty:
                summary_csv = summary_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Summary (CSV)",
                    data=summary_csv,
                    file_name=f"cross_category_summary_{source_cat_display.replace(', ', '_')}_to_{target_cat_display.replace(', ', '_')}.csv",
                    mime="text/csv"
                )
        
        # Stop here - don't show Brand/Product Switch UI
        st.stop()

# =====================================================
# BRAND/PRODUCT SWITCH MODE (Original)
# =====================================================
if run_analysis or st.session_state.query_executed:
    if run_analysis:
        selected_category = selected_categories[0] if selected_categories else None
        
        # Validate required fields
        if not selected_category:
            st.error("⚠️ Please select at least one category to run the analysis.")
            st.stop()
        
        # Query at Product level (Brand/Product view toggle is post-query)
        # If brands selected in sidebar, filter at query level (saves data)
        # If no brands, get all and user can filter client-side later
        query_all_brands = query_builder.build_switching_query(
            period1_start.strftime("%Y-%m-%d"), 
            period1_end.strftime("%Y-%m-%d"), 
            period2_start.strftime("%Y-%m-%d"), 
            period2_end.strftime("%Y-%m-%d"), 
            selected_category, 
            selected_brands if selected_brands else None,  # Use sidebar brands if selected
            selected_subcategories if selected_subcategories else None,  # Use subcategories
            product_name_contains or None,
            product_name_not_contains or None,
            primary_threshold, 
            barcode_mapping_text if barcode_mapping_text and barcode_mapping_text.strip() else None,
            store_filter_type,
            store_opening_cutoff,
            include_sales=is_sales_mode  # Only include sales columns in Sales Analysis mode
        )
        
        utils.show_debug_query(query_all_brands)
        df, gb_processed = bigquery_client.execute_query(query_all_brands)
        st.session_state.results_df = df
        st.session_state.gb_processed = gb_processed
        st.session_state.query_executed = True
        
        # Track query with filter details
        try:
            if 'tracking_session_id' in st.session_state:
                query_details = {
                    'category': selected_category,
                    'subcategories': selected_subcategories[:3] if selected_subcategories else [],
                    'brands_count': len(selected_brands) if selected_brands else 0,
                    'period1': f"{period1_start} to {period1_end}",
                    'period2': f"{period2_start} to {period2_end}",
                    'gb_processed': round(gb_processed, 2) if gb_processed else 0
                }
                tracking.log_event(
                    st.session_state.tracking_session_id, 
                    'query', 
                    query_details,
                    duration_ms=None  # Could add timing later
                )
        except Exception:
            pass  # Tracking errors should not break the app
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
    
    # =====================================================
    # DETECT CUSTOM BARCODE MODE
    # When user provides barcode mapping, skip brand filter
    # =====================================================
    
    def parse_custom_mapping(mapping_text):
        """Parse barcode mapping text and return dict + list of types."""
        if not mapping_text or not mapping_text.strip():
            return {}, []
        
        mapping = {}
        types_set = set()
        lines = mapping_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Support tab, comma, space separated
            parts = line.replace('\t', ',').replace('  ', ',').split(',', 1)
            if len(parts) == 2:
                barcode = parts[0].strip()
                custom_type = parts[1].strip()
                if barcode and custom_type:
                    mapping[barcode] = custom_type
                    types_set.add(custom_type)
        
        return mapping, sorted(types_set)
    
    custom_barcode_map, custom_types = parse_custom_mapping(barcode_mapping_text)
    is_custom_mode = len(custom_barcode_map) > 0
    
    # =====================================================
    # CUSTOM BARCODE MODE - Shows custom type movement
    # =====================================================
    
    if is_custom_mode:
        # Show Custom Mode Banner instead of Analysis Scope
        st.markdown(f'''
        <div style="
            background: linear-gradient(135deg, #0f3d3e 0%, #1a5a5c 100%);
            border-radius: 8px;
            padding: 20px;
            margin: 12px 0 20px 0;
            color: #fff;
        ">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="white">
                    <path d="M17.63 5.84C17.27 5.33 16.67 5 16 5L5 5.01C3.9 5.01 3 5.9 3 7v10c0 1.1.9 1.99 2 1.99L16 19c.67 0 1.27-.33 1.63-.84L22 12l-4.37-6.16zM16 17H5V7h11l3.55 5L16 17z"/>
                </svg>
                <span style="font-size:18px;font-weight:700;">Custom Barcode Mode</span>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
        ''', unsafe_allow_html=True)
        
        # Show custom types as pills
        pills_html = ""
        for ct in custom_types[:10]:  # Limit to 10 for display
            pills_html += f'<span style="background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:4px;font-size:13px;font-weight:500;">{ct}</span>'
        if len(custom_types) > 10:
            pills_html += f'<span style="padding:4px 12px;font-size:13px;opacity:0.7;">+{len(custom_types)-10} more</span>'
        
        st.markdown(f'''
            {pills_html}
            </div>
            <div style="font-size:12px;opacity:0.8;">
                {len(custom_barcode_map)} barcodes mapped • Analysis shows movement between custom types
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Use custom types for analysis - skip brand selection
        # The df already has custom types instead of brand names (from query)
        selected_brands = custom_types  # Use custom types as "brands" for downstream logic
        is_product_switch_mode = False  # Custom mode works at type level
        product_to_brand_map = custom_barcode_map  # Map barcodes to types
        
        # Use df as-is, it already has custom types from SQL CASE statement
        df_working = df.copy()
    
    # =====================================================
    # ANALYSIS SCOPE - UNIFIED CONTROL PANEL (Normal Mode)
    # Only show when NOT in custom barcode mode
    # =====================================================
    
    if not is_custom_mode:
        st.markdown("""
        <style>
        /* Control Panel Container */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) {
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 8px;
            padding: 0 !important;
            margin: 12px 0 20px 0;
            overflow: hidden;
        }
    
        /* Panel Header - LARGER */
        .panel-header {
            background: #0f3d3e;
            padding: 14px 20px;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .panel-title {
            color: #fff;
            font-size: 15px;
            font-weight: 700;
            margin: 0;
        }
        .panel-subtitle {
            color: rgba(255,255,255,0.7);
            font-size: 12px;
            margin-left: auto;
        }
    
        /* Section styling - LARGER LABELS */
        .section-label {
            font-size: 12px;
            font-weight: 700;
            color: #57606a;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            padding: 16px 20px 0 20px;
        }
    
        /* Inline Status Badge */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 4px;
        }
        .status-badge.ready {
            background: #dafbe1;
            color: #1a7f37;
        }
        .status-badge.waiting {
            background: #fff8c5;
            color: #9a6700;
        }
    
        /* Radio as segmented control - FLUSH LEFT */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stRadio"] {
            padding: 0 20px 16px 20px;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stRadio"] > div {
            flex-direction: row !important;
            gap: 0 !important;
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 3px;
            display: inline-flex !important;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stRadio"] label {
            padding: 8px 24px !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            color: #57606a !important;
            background: transparent !important;
            border-radius: 4px !important;
            margin: 0 !important;
            border: none !important;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stRadio"] label[data-checked="true"] {
            background: #0f3d3e !important;
            color: #fff !important;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stRadio"] label span {
            display: none !important;
        }
    
        /* Multiselect - GLOBAL VISIBLE BORDER (dark gray) */
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 2px solid #475569 !important;
            border-radius: 6px !important;
            min-height: 44px !important;
        }
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div:hover {
            border-color: #334155 !important;
        }
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {
            border-color: #0f3d3e !important;
            box-shadow: 0 0 0 3px rgba(15,61,62,0.25) !important;
        }
    
        /* Expander styling */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stExpander"] {
            border-top: 1px solid #d0d7de !important;
            border-bottom: none !important;
            border-left: none !important;
            border-right: none !important;
            background: #f6f8fa !important;
            border-radius: 0 !important;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stExpander"] summary {
            font-size: 12px;
            font-weight: 600;
            color: #57606a;
            padding: 10px 16px;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stExpander"] [data-testid="stVerticalBlock"] {
            padding: 0 16px 12px 16px;
        }
    
        /* Text area inside expander */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stTextArea"] textarea {
            background: #ffffff !important;
            border: 1px solid #d0d7de !important;
            border-radius: 6px !important;
            font-size: 12px !important;
        }
    
        /* BUTTONS - smaller, not full teal block */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) button {
            font-size: 12px !important;
            padding: 6px 16px !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) button[kind="primary"],
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) button:first-of-type {
            background: #0f3d3e !important;
            color: white !important;
            border: none !important;
        }
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) button[kind="secondary"],
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) button:last-of-type {
            background: #f6f8fa !important;
            color: #24292f !important;
            border: 1px solid #d0d7de !important;
        }
    
        /* Caption styling */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stCaptionContainer"] {
            font-size: 12px;
            color: #57606a;
            margin-bottom: 8px;
        }
    
        /* Success message compact */
        [data-testid="stVerticalBlock"]:has(> div.control-panel-start) [data-testid="stAlert"] {
            padding: 8px 12px !important;
            font-size: 12px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
        # Start Control Panel Container
        with st.container():
            # Marker for CSS targeting
            st.markdown('<div class="control-panel-start"></div>', unsafe_allow_html=True)
        
            # PANEL HEADER
            st.markdown('''
            <div class="panel-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
                    <path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z"/>
                </svg>
                <span class="panel-title">Analysis Scope</span>
                <span class="panel-subtitle">Configure view and filters</span>
            </div>
            ''', unsafe_allow_html=True)
        
            # RESET BUTTON - Small, blue gradient at top left
            reset_btn_col, reset_spacer = st.columns([1, 4])
            with reset_btn_col:
                st.markdown("""
                <style>
                div[data-testid="stButton"] > button[kind="secondary"] {
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
                    color: white !important;
                    border: none !important;
                    font-size: 11px !important;
                    padding: 4px 12px !important;
                }
                </style>
                """, unsafe_allow_html=True)
                if st.button("Reset", key="reset_analysis_scope", type="secondary"):
                    # Clear all analysis scope settings using counter-based approach
                    # Increment reset counter to force new widget key
                    current_reset_count = st.session_state.get('_brand_reset_counter', 0)
                    st.session_state['_brand_reset_counter'] = current_reset_count + 1
                    st.session_state['select_all_brands'] = False
                    # Delete the old brand filter key (new key will be different)
                    for key in ['view_mode_toggle', 'top_n_items_slider', 'enable_top_n_filter']:
                        if key in st.session_state:
                            del st.session_state[key]
                    # Also delete any previous brand filter keys
                    keys_to_delete = [k for k in st.session_state.keys() if k.startswith('brand_filter_')]
                    for k in keys_to_delete:
                        del st.session_state[k]
                    st.rerun()
        
            # SECTION 1: VIEW LEVEL - Label and Radio on SAME LINE
            st.markdown('<div style="padding: 16px 20px 0 20px;"></div>', unsafe_allow_html=True)
            view_label_col, view_radio_col = st.columns([1, 3])
            with view_label_col:
                st.markdown('<div style="font-size:12px;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.5px;padding-top:8px;">View Level</div>', unsafe_allow_html=True)
            with view_radio_col:
                view_mode = st.radio(
                    "View",
                    options=["Brand", "Product"],
                    horizontal=True,
                    key="view_mode_toggle",
                    label_visibility="collapsed"
                )
            is_product_switch_mode = (view_mode == "Product")
        
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        
            # Prepare df_working
            df_working = df.copy()
            if not is_product_switch_mode:
                df_working = df_working.groupby(['brand_2024', 'brand_2025', 'move_type']).agg({
                    'customers': 'sum'
                }).reset_index()
                df_working = df_working.rename(columns={
                    'brand_2024': 'prod_2024',
                    'brand_2025': 'prod_2025'
                })
        
            # Brand data preparation
            special_categories = ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED']
        
            if is_product_switch_mode:
                brands_from_data = set()
                if 'brand_2024' in df.columns:
                    brands_from_data.update([b for b in df['brand_2024'].unique() if b not in special_categories and b is not None])
                if 'brand_2025' in df.columns:
                    brands_from_data.update([b for b in df['brand_2025'].unique() if b not in special_categories and b is not None])
                all_brands_in_data = sorted(brands_from_data)
            
                product_to_brand_map = {}
                for _, row in df.iterrows():
                    if row['prod_2024'] not in special_categories and 'brand_2024' in df.columns:
                        product_to_brand_map[row['prod_2024']] = row['brand_2024']
                    if row['prod_2025'] not in special_categories and 'brand_2025' in df.columns:
                        product_to_brand_map[row['prod_2025']] = row['brand_2025']
            else:
                all_brands_in_data = sorted([b for b in df_working['prod_2024'].unique() if b not in special_categories])
                product_to_brand_map = {}
        
            # SECTION 2: BRANDS - Label and Dropdown on SAME LINE
            st.markdown('<div style="padding: 8px 20px 0 20px;"></div>', unsafe_allow_html=True)
            brand_label_col, brand_select_col, status_col = st.columns([1, 2.5, 0.8])
        
            with brand_label_col:
                st.markdown('<div style="font-size:12px;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.5px;padding-top:8px;">Brands</div>', unsafe_allow_html=True)
        
            with brand_select_col:
                # Select All checkbox - when checked, update session state and rerun
                select_all = st.checkbox("Select All", key="select_all_brands")
                
                # Handle Select All toggle - update session state directly
                reset_counter = st.session_state.get('_brand_reset_counter', 0)
                brand_key = f"brand_filter_{reset_counter}"
                
                current_selection = st.session_state.get(brand_key, [])
                if select_all and len(current_selection) != len(all_brands_in_data):
                    # Select all brands
                    st.session_state[brand_key] = all_brands_in_data
                    st.rerun()
                elif not select_all and len(current_selection) == len(all_brands_in_data):
                    # User unchecked Select All, keep selection as is (don't clear)
                    pass
                
                selected_brands = st.multiselect(
                    "Brands",
                    options=all_brands_in_data,
                    key=brand_key,
                    label_visibility="collapsed",
                    placeholder="Select brands..."
                )
        
            with status_col:
                if selected_brands:
                    if is_product_switch_mode and product_to_brand_map:
                        selected_products = [p for p, b in product_to_brand_map.items() if b in selected_brands]
                        st.markdown(f'<div class="status-badge ready">✓ {len(selected_brands)}B · {len(selected_products)}P</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-badge ready">✓ {len(selected_brands)} brands</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-badge waiting">Select brands</div>', unsafe_allow_html=True)
        
            if not selected_brands:
                st.stop()
        
            # SECTION: TOP N FILTER (with enable checkbox)
            st.markdown('<div style="padding: 8px 20px 0 20px;"></div>', unsafe_allow_html=True)
            filter_item_name = "Product" if is_product_switch_mode else "Brand"
            enable_top_n = st.checkbox(
                f"Enable Top N Filter ({filter_item_name}s)", 
                key="enable_top_n_filter",
                help="เมื่อเปิดใช้งาน จะแสดงเฉพาะ Top N items ตามยอดขายปี 2024"
            )
            
            if enable_top_n:
                slider_label = "Show Top N Products" if is_product_switch_mode else "Show Top N Brands"
                top_n_items = st.slider(
                    slider_label,
                    min_value=5,
                    max_value=50,
                    value=20,
                    step=5,
                    key="top_n_items_slider"
                )
        
            # SECTION 3: ADVANCED FILTERS (collapsible)
            with st.expander("Advanced Filters", expanded=False):
                st.caption("Barcode Filter")
                barcode_filter_input = st.text_area(
                    "Barcodes",
                    height=60,
                    placeholder="Paste barcodes (one per line)",
                    key="barcode_filter_input",
                    label_visibility="collapsed"
                )
            
                c1, c2 = st.columns(2)
                with c1:
                    apply_barcode_filter = st.button("Apply", key="apply_bc_filter", use_container_width=True)
                with c2:
                    if st.button("Clear", key="clear_bc_filter", use_container_width=True):
                        st.session_state.active_barcode_filter = []
                        st.rerun()
            
                if apply_barcode_filter and barcode_filter_input.strip():
                    barcode_list = [b.strip() for b in barcode_filter_input.strip().split('\n') if b.strip()]
                    st.session_state.active_barcode_filter = barcode_list
                    st.rerun()
            
                active_barcodes_display = st.session_state.get('active_barcode_filter', [])
                if active_barcodes_display:
                    st.success(f"{len(active_barcodes_display)} barcodes active")
    
    # END OF CONTROL PANEL
    
    # =====================================================
    # DATA PROCESSING (after filter panel)
    # =====================================================
    
    # Apply Product Filtering for Product Switch Mode
    if is_product_switch_mode and selected_brands and product_to_brand_map:
        def is_product_in_brand(product_name, selected_brands, mapping):
            if product_name in special_categories:
                return True
            brand = mapping.get(product_name)
            if brand and brand in selected_brands:
                return True
            return False
        
        mask = (
            df['prod_2024'].apply(lambda x: is_product_in_brand(x, selected_brands, product_to_brand_map)) |
            df['prod_2025'].apply(lambda x: is_product_in_brand(x, selected_brands, product_to_brand_map))
        )
        df = df[mask].copy()
    
    # Get active barcodes for filtering logic
    active_barcodes = st.session_state.get('active_barcode_filter', [])
    
    # Section header
    st.markdown("### 📊 Customer Flow Analysis")
    
    # Apply brand filtering based on selection from sidebar
    # df_working already has barcode filter applied and is aggregated appropriately for view mode
    df_display = df_working.copy()  # Default to working data (with barcode filter and aggregation)
    
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
            df_display = brand_filter.filter_dataframe_by_brands(df_working, products_in_selected_brands, 'filtered')
        else:
            # Brand Switch mode: df already contains Brand names
            # Filter directly by selected brand names
            df_display = brand_filter.filter_dataframe_by_brands(df_working, selected_brands, 'filtered')
    
    # === Apply barcode filter (WORKS IN BOTH Brand AND Product modes) ===
    if active_barcodes:
        from modules import brand_filter
        
        # Always filter from ORIGINAL df (before any aggregation)
        if 'barcode_2024' in df.columns and 'barcode_2025' in df.columns:
            # Filter by barcodes first
            df_barcode_filtered = df[
                (df['barcode_2024'].isin(active_barcodes)) |
                (df['barcode_2025'].isin(active_barcodes))
            ]
            
            # Then apply brand filter on barcode-filtered data
            if selected_brands:
                if is_product_switch_mode and product_to_brand_map:
                    products_in_selected_brands = [
                        product for product, brand in product_to_brand_map.items() 
                        if brand in selected_brands
                    ]
                    df_display = brand_filter.filter_dataframe_by_brands(df_barcode_filtered, products_in_selected_brands, 'filtered')
                else:
                    # Brand mode: need to aggregate barcode-filtered data to brand level first
                    df_agg = df_barcode_filtered.groupby(['brand_2024', 'brand_2025', 'move_type']).agg({
                        'customers': 'sum'
                    }).reset_index()
                    df_agg = df_agg.rename(columns={'brand_2024': 'prod_2024', 'brand_2025': 'prod_2025'})
                    df_display = brand_filter.filter_dataframe_by_brands(df_agg, selected_brands, 'filtered')
            else:
                # No brand selected, use barcode filtered data
                if is_product_switch_mode:
                    df_display = df_barcode_filtered
                else:
                    df_display = df_barcode_filtered.groupby(['brand_2024', 'brand_2025', 'move_type']).agg({
                        'customers': 'sum'
                    }).reset_index()
                    df_display = df_display.rename(columns={'brand_2024': 'prod_2024', 'brand_2025': 'prod_2025'})
            
            if len(df_display) == 0:
                st.warning("⚠️ No products found matching the barcode filter")
    
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
    summary_df_display = summary_df.copy()
    
    # Apply Top N filter ONLY if checkbox is enabled and slider exists
    top_n_items_list = []  # List of top N brands/products to filter visualizations
    is_top_n_enabled = st.session_state.get('enable_top_n_filter', False)
    if is_top_n_enabled and 'top_n_items_slider' in st.session_state and len(summary_df_display) > 0:
        top_n = st.session_state.top_n_items_slider
        if '2024_Total' in summary_df_display.columns:
            summary_df_display = summary_df_display.nlargest(top_n, '2024_Total')
            # Get the list of top N items for filtering other visualizations
            if item_label in summary_df_display.columns:
                top_n_items_list = summary_df_display[item_label].tolist()
    
    # Filter df_display to only include flows involving top N items
    # This will affect Sankey, Heatmap, and other visualizations
    if top_n_items_list:
        special_cats = ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED', 'OTHERS']
        allowed_items = top_n_items_list + special_cats
        
        # Filter to include rows where BOTH prod_2024 AND prod_2025 are in allowed list
        # This prevents showing flows to/from brands outside top N
        df_display = df_display[
            (df_display['prod_2024'].isin(allowed_items)) & 
            (df_display['prod_2025'].isin(allowed_items))
        ].copy()
    
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
        # Calculate formatted values
        total_movement_fmt = utils.format_number(kpis['total_movement'])
        net_cat = kpis['net_category_movement']
        net_sign = "+" if net_cat >= 0 else ""
        net_cat_fmt = f"{net_sign}{net_cat:,}"
        net_color = "#16a34a" if net_cat >= 0 else "#dc2626"
        
        winner_val = kpis['winner_val']
        winner_sign = "+" if winner_val > 0 else ""
        winner_val_fmt = f"{winner_sign}{winner_val:,}"
        
        loser_val = kpis['loser_val']
        loser_sign = "+" if loser_val > 0 else ""
        loser_val_fmt = f"{loser_sign}{loser_val:,}"
        
        churn_rate_fmt = f"{kpis['churn_rate']:.1f}%"
        
        # Consistent KPI card styling
        k1, k2, k3, k4, k5 = st.columns(5)
        
        card_base = """
            background: white; 
            padding: 16px 20px; 
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            height: 100%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        """
        
        with k1:
            st.markdown(f"""
            <div style="{card_base}">
                <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Total Movement</div>
                <div style="font-size: 28px; font-weight: 500; color: #111827; letter-spacing: -0.02em;">{total_movement_fmt}</div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Customers</div>
            </div>
            """, unsafe_allow_html=True)
        
        with k2:
            st.markdown(f"""
            <div style="{card_base}">
                <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Net Movement</div>
                <div style="font-size: 28px; font-weight: 500; color: {net_color}; letter-spacing: -0.02em;">{net_cat_fmt}</div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Total In - Out</div>
            </div>
            """, unsafe_allow_html=True)
        
        with k3:
            st.markdown(f"""
            <div style="{card_base}">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 500; color: #6b7280;">Biggest Winner</span>
                    <span style="font-size: 12px; font-weight: 500; color: #16a34a;">{winner_val_fmt}</span>
                </div>
                <div style="font-size: 24px; font-weight: 500; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{kpis['winner_name']}">{kpis['winner_name']}</div>
                <div style="font-size: 12px; color: #16a34a; margin-top: 4px;">↑ {winner_val_fmt}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with k4:
            st.markdown(f"""
            <div style="{card_base}">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 500; color: #6b7280;">Biggest Loser</span>
                    <span style="font-size: 12px; font-weight: 500; color: #dc2626;">{loser_val_fmt}</span>
                </div>
                <div style="font-size: 24px; font-weight: 500; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{kpis['loser_name']}">{kpis['loser_name']}</div>
                <div style="font-size: 12px; color: #dc2626; margin-top: 4px;">{loser_val_fmt}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with k5:
            st.markdown(f"""
            <div style="{card_base}">
                <div style="font-size: 14px; font-weight: 500; color: #6b7280; margin-bottom: 8px;">Attrition Rate</div>
                <div style="font-size: 28px; font-weight: 500; color: #dc2626; letter-spacing: -0.02em;">{churn_rate_fmt}</div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Out / Total</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Sankey Title with margin separation
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; font-size: 16px; font-weight: 600; color: #374151; margin-bottom: 8px;">Customer Flow (Sankey)</div>', unsafe_allow_html=True)
    
    # Data source for Sankey - use filtered data with brand highlighting
    labels, sources, targets, values = data_processor.prepare_sankey_data(df_display)
    st.plotly_chart(visualizations.create_sankey_diagram(labels, sources, targets, values, selected_brands), use_container_width=True)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 2: Competitive Matrix</span>
    </div>
""", unsafe_allow_html=True)
    
    # Toggle for percentage view
    show_percentage = st.toggle("Show as Percentage (%)", value=False, key="heatmap_pct_toggle", help="Toggle to show percentages instead of raw customer counts")
    
    st.plotly_chart(visualizations.create_competitive_heatmap(data_processor.prepare_heatmap_data(df_display), show_percentage=show_percentage), use_container_width=True)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; margin-top: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
        <span style="font-size: 24px; font-weight: 800; color: #0f3d3e;">Section 3: Waterfall Customer Movement</span>
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
    switching_tab_label = f"{item_label} Switching"
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Summary", switching_tab_label, "Loyalty", "Charts", "📊 Sales Analysis", "Raw", "Export"])
    with tab1:
        st.markdown(f"### {item_label} Movement Summary")
        display_summary = visualizations.create_summary_table_display(summary_df_display)
        
        # Sort by 2024_Total descending as requested
        if '2024_Total' in display_summary.columns:
            display_summary = display_summary.sort_values(by='2024_Total', ascending=False)
            
        def make_table(df):
            # Detect item column dynamically (Brand or Product)
            item_col = df.columns[0] if len(df.columns) > 0 else 'Brand'
            
            # Define rich gradient colors for each column group
            gradient_colors = {
                item_col: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
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
                item_col: '7%',
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
        st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#0f3d3e"><path d="M6.99 11L3 15l3.99 4v-3H14v-2H6.99v-3zM21 9l-3.99-4v3H10v2h7.01v3L21 9z"/></svg>
        <span style="font-size: 20px; font-weight: 700; color: #0f3d3e;">{item_label} Switching Details</span>
    </div>
""", unsafe_allow_html=True)
        st.caption(f"Top {item_label.lower()}-to-{item_label.lower()} switching flows (sorted by From {item_label} A→Z, then Customers High→Low)")
        
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
                <th style="width: 30%;">From ''' + item_label + '''</th>
                <th style="width: 30%;">To ''' + item_label + '''</th>
                <th style="width: 20%;">Customers</th>
                <th style="width: 20%;">% of From ''' + item_label + '''</th>
            </tr>
        </thead>
        <tbody>''' + table_body + '''
        </tbody>
    </table>
</div>
'''
            
            st.markdown(html, unsafe_allow_html=True)
            st.info(f"💡 **คำอธิบาย:** % of From {item_label} = จำนวนลูกค้าที่ย้ายจาก {item_label} นั้น / ลูกค้าทั้งหมดของ {item_label} ในช่วง Before Period")
        else:
            st.warning(f"⚠️ ไม่พบข้อมูลการ switch ระหว่าง {item_label.lower()}")
    
    # Tab 3: Loyalty (moved from tab6)
    with tab3:
        st.markdown("### ◈ Cohort & Loyalty Analysis")
        st.caption("Analysis of customer retention and churn behavior between the two periods.")
        
        # Brand filter for Loyalty metrics
        brand_cohort_data = data_processor.calculate_cohort_metrics_by_brand(df_display)
        
        if brand_cohort_data['brands']:
            loyalty_brand_options = ["All Brands"] + brand_cohort_data['brands']
            selected_loyalty_brand = st.selectbox(
                "Select brand for analysis",
                options=loyalty_brand_options,
                key="loyalty_brand_filter"
            )
            
            if selected_loyalty_brand == "All Brands":
                # Calculate aggregated metrics
                cohort_metrics = data_processor.calculate_cohort_metrics(df_display)
            else:
                # Calculate metrics for selected brand only
                brand_idx = brand_cohort_data['brands'].index(selected_loyalty_brand)
                total = brand_cohort_data['totals'][brand_idx]
                stayed = brand_cohort_data['retained'][brand_idx]
                switched = brand_cohort_data['switched'][brand_idx]
                churned = brand_cohort_data['churned'][brand_idx]
                
                cohort_metrics = {
                    'retention_rate': (stayed / total * 100) if total > 0 else 0,
                    'switch_rate': (switched / total * 100) if total > 0 else 0,
                    'churn_rate': (churned / total * 100) if total > 0 else 0,
                    'stayed_customers': stayed,
                    'switch_out_customers': switched,
                    'gone_customers': churned,
                    'total_base': total
                }
        else:
            cohort_metrics = data_processor.calculate_cohort_metrics(df_display)
            selected_loyalty_brand = "All Brands"
        
        if cohort_metrics:
            # Show which brand is being analyzed
            brand_label = f" ({selected_loyalty_brand})" if selected_loyalty_brand != "All Brands" else ""
            
            retention_rate_fmt = f"{cohort_metrics['retention_rate']:.1f}%"
            switch_rate_fmt = f"{cohort_metrics['switch_rate']:.1f}%"
            churn_rate_fmt_2 = f"{cohort_metrics['churn_rate']:.1f}%"
            
            # Display customer counts for context
            stayed_count = f"{cohort_metrics['stayed_customers']:,}"
            switched_count = f"{cohort_metrics['switch_out_customers']:,}"
            churned_count = f"{cohort_metrics['gone_customers']:,}"
            
            card_style = """
                background: white; 
                padding: 16px 20px; 
                border-right: 1px solid #e5e7eb;
                height: 100%;
            """
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div style="{card_style} border-radius: 12px 0 0 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 14px; font-weight: 500; color: #6b7280;">Retention Rate{brand_label}</span>
                        <span style="font-size: 12px; font-weight: 500; color: #16a34a;">{stayed_count} customers</span>
                    </div>
                    <div style="font-size: 28px; font-weight: 500; color: #16a34a; letter-spacing: -0.02em;">{retention_rate_fmt}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Stayed with same brand</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="{card_style}">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 14px; font-weight: 500; color: #6b7280;">Switch Rate{brand_label}</span>
                        <span style="font-size: 12px; font-weight: 500; color: #f59e0b;">{switched_count} customers</span>
                    </div>
                    <div style="font-size: 28px; font-weight: 500; color: #f59e0b; letter-spacing: -0.02em;">{switch_rate_fmt}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Switched to other brands</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div style="{card_style} border-right: none; border-radius: 0 12px 12px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 14px; font-weight: 500; color: #6b7280;">Churn Rate{brand_label}</span>
                        <span style="font-size: 12px; font-weight: 500; color: #dc2626;">{churned_count} customers</span>
                    </div>
                    <div style="font-size: 28px; font-weight: 500; color: #dc2626; letter-spacing: -0.02em;">{churn_rate_fmt_2}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Lost from category</div>
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
        st.markdown("### ◆📈 Market Overview")
        
        # Metric selector at top level
        metric = st.selectbox("Metric", ['Stayed', 'Net_Movement','Total_In','Total_Out'], key="chart_metric")
        
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Movement Distribution")
            st.plotly_chart(visualizations.create_movement_type_pie(df_display), use_container_width=True)
        with c2:
            st.caption(f"Brand Comparison: {metric.replace('_', ' ')}")
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
                 except (ValueError, KeyError):
                     pass
                     
            target_brand = st.selectbox("Select Focus Brand", unique_items, index=default_brand_index, key="net_gain_loss_brand")
        
            # Create and display chart
            fig_net_flow = visualizations.create_net_gain_loss_chart(df_display, target_brand)
            st.plotly_chart(fig_net_flow, use_container_width=True)
        else:
            st.info("No brands available for competitive analysis.")
    
    # Tab 5: Sales Analysis (NEW)
    with tab5:
        st.markdown("### 📊 Sales Analysis (Testing)")
        st.caption("Compare customer movement with sales value to understand revenue impact.")
        
        # Check if sales columns exist in data
        has_sales = 'sales_2024' in df_display.columns and 'sales_2025' in df_display.columns
        
        if has_sales:
            # Sales summary by move type
            st.markdown("#### Sales by Movement Type")
            
            sales_summary = df_display.groupby('move_type').agg({
                'customers': 'sum',
                'sales_2024': 'sum',
                'sales_2025': 'sum',
                'total_sales': 'sum'
            }).reset_index()
            
            # Add calculated columns
            sales_summary['avg_sales_per_customer_2024'] = sales_summary['sales_2024'] / sales_summary['customers']
            sales_summary['avg_sales_per_customer_2025'] = sales_summary['sales_2025'] / sales_summary['customers']
            sales_summary['sales_change'] = sales_summary['sales_2025'] - sales_summary['sales_2024']
            sales_summary['sales_change_pct'] = (sales_summary['sales_2025'] / sales_summary['sales_2024'] - 1) * 100
            
            # Format for display
            display_sales = sales_summary.copy()
            display_sales['sales_2024'] = display_sales['sales_2024'].apply(lambda x: f"฿{x:,.0f}")
            display_sales['sales_2025'] = display_sales['sales_2025'].apply(lambda x: f"฿{x:,.0f}")
            display_sales['total_sales'] = display_sales['total_sales'].apply(lambda x: f"฿{x:,.0f}")
            display_sales['avg_sales_per_customer_2024'] = display_sales['avg_sales_per_customer_2024'].apply(lambda x: f"฿{x:,.0f}")
            display_sales['avg_sales_per_customer_2025'] = display_sales['avg_sales_per_customer_2025'].apply(lambda x: f"฿{x:,.0f}")
            display_sales['sales_change'] = sales_summary['sales_change'].apply(lambda x: f"+฿{x:,.0f}" if x >= 0 else f"-฿{abs(x):,.0f}")
            display_sales['sales_change_pct'] = sales_summary['sales_change_pct'].apply(lambda x: f"+{x:.1f}%" if x >= 0 else f"{x:.1f}%")
            display_sales['customers'] = display_sales['customers'].apply(lambda x: f"{x:,}")
            
            display_sales.columns = ['Move Type', 'Customers', 'Sales 2024', 'Sales 2025', 'Total Sales', 'Avg/Customer 2024', 'Avg/Customer 2025', 'Sales Change', 'Change %']
            st.dataframe(display_sales, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### Sales Flow Matrix (Brand to Brand)")
            
            # Aggregate by brand flow
            brand_sales = df_display.groupby(['brand_2024', 'brand_2025']).agg({
                'customers': 'sum',
                'sales_2024': 'sum',
                'sales_2025': 'sum'
            }).reset_index()
            
            # Filter out special categories for cleaner view
            special_cats = ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED']
            brand_sales_filtered = brand_sales[
                (~brand_sales['brand_2024'].isin(special_cats)) & 
                (~brand_sales['brand_2025'].isin(special_cats))
            ].copy()
            
            if len(brand_sales_filtered) > 0:
                brand_sales_filtered['sales_delta'] = brand_sales_filtered['sales_2025'] - brand_sales_filtered['sales_2024']
                brand_sales_filtered = brand_sales_filtered.sort_values('sales_delta', ascending=False).head(20)
                
                # Format display
                brand_sales_filtered['sales_2024'] = brand_sales_filtered['sales_2024'].apply(lambda x: f"฿{x:,.0f}")
                brand_sales_filtered['sales_2025'] = brand_sales_filtered['sales_2025'].apply(lambda x: f"฿{x:,.0f}")
                brand_sales_filtered['sales_delta'] = brand_sales_filtered['sales_delta'].apply(lambda x: f"+฿{x:,.0f}" if x >= 0 else f"-฿{abs(x):,.0f}")
                brand_sales_filtered.columns = ['From Brand', 'To Brand', 'Customers', 'Sales Before', 'Sales After', 'Sales Delta']
                
                st.dataframe(brand_sales_filtered, use_container_width=True, hide_index=True)
            else:
                st.info("No brand-to-brand flows available.")
                
            st.markdown("---")
            st.markdown("#### Raw Data with Sales")
            sales_cols = ['prod_2024', 'prod_2025', 'brand_2024', 'brand_2025', 'customers', 'sales_2024', 'sales_2025', 'total_sales', 'move_type']
            available_cols = [c for c in sales_cols if c in df_display.columns]
            st.dataframe(df_display[available_cols].head(100), use_container_width=True, height=300)
        else:
            st.warning("⚠️ Sales data not available in current query results.")
            st.info("กรุณา Run Query ใหม่เพื่อดึงข้อมูล Sales")
            st.caption("Expected columns: sales_2024, sales_2025, total_sales")
            st.markdown("**Available columns:**")
            st.write(df_display.columns.tolist())
    
    # Tab 6: Raw
    with tab6:
        st.markdown("### Raw Data")
        st.dataframe(df_display, use_container_width=True, height=400)
        st.markdown("### Top 10 Flows")
        st.dataframe(data_processor.get_top_flows(df_display, n=10), use_container_width=True)
    
    # Tab 7: Export
    with tab7:
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
        
        # Extract items for highlighting from summary_df (which has correct Brand or Product column)
        special_categories = {'NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED', 'OTHERS'}
        
        # Get items from summary_df (either Brand or Product column)
        if 'Product' in summary_df.columns:
            items_for_ai = summary_df['Product'].tolist()
        elif 'Brand' in summary_df.columns:
            items_for_ai = summary_df['Brand'].tolist()
        else:
            items_for_ai = []
        
        # Also add items from df_display for complete highlighting
        all_items_from_data = set()
        all_items_from_data.update(df_display['prod_2024'].unique())
        all_items_from_data.update(df_display['prod_2025'].unique())
        
        # Add all non-special items
        for item in all_items_from_data:
            if item not in special_categories and item not in items_for_ai:
                items_for_ai.append(item)
        
        # Remove special categories and duplicates
        items_for_ai = list(set([item for item in items_for_ai if item and item not in special_categories]))
        
        # Limit to top items by customer count if too many
        if len(items_for_ai) > 20:
            # Sort by 2024_Total from summary_df and take top 20
            if '2024_Total' in summary_df.columns:
                item_col = 'Product' if 'Product' in summary_df.columns else 'Brand'
                if item_col in summary_df.columns:
                    top_items = summary_df.nlargest(20, '2024_Total')[item_col].tolist()
                    items_for_ai = [item for item in items_for_ai if item in top_items]
        
        # Track AI generation
        try:
            if 'tracking_session_id' in st.session_state:
                tracking.log_ai_generation(st.session_state.tracking_session_id, view_mode, ai_category or "")
        except Exception:
            pass  # Tracking errors should not break the app
        
        insights = ai_analyzer.generate_insights(df_display, summary_df, ai_category, items_for_ai, view_mode, f"{period1_start} to {period1_end}", f"{period2_start} to {period2_end}")
        if insights:
            st.markdown(insights, unsafe_allow_html=True)
else:
    st.info("👈 Configure and click **Run Analysis**")

# Footer with Author Credit
st.markdown("---")
st.markdown('''
<div style="text-align: center; padding: 20px 0; color: #64748b;">
    <div style="font-size: 14px; margin-bottom: 4px;">
        <strong>Everything-Switching Analysis</strong> | Powered by BigQuery & OpenAI
    </div>
    <div style="font-size: 12px; color: #94a3b8;">
        Original by <strong>Kritin Kayaras</strong> • © 2025 All Rights Reserved
    </div>
</div>
''', unsafe_allow_html=True)
