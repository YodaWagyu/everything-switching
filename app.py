"""Everything-Switching Analysis Application"""
import streamlit as st
from datetime import datetime, timedelta
from modules import bigquery_client, data_processor, visualizations, utils, query_builder, ai_analyzer
import config

st.set_page_config(page_title="Everything-Switching", page_icon="🔄", layout="wide")
st.title("🔄 Everything-Switching Analysis")
if 'query_executed' not in st.session_state:
    st.session_state.query_executed = False

st.sidebar.header("⚙️ Configuration")

st.sidebar.markdown("### 🎯 Analysis Mode")
analysis_mode = st.sidebar.radio("Select mode", config.ANALYSIS_MODES, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Before Period")
col1, col2 = st.sidebar.columns(2)
with col1:
    period1_start = st.date_input("Start", datetime(2024, 1, 1), key="before_start")
with col2:
    period1_end = st.date_input("End", datetime(2024, 1, 31), key="before_end")

st.sidebar.markdown("### 📅 After Period")
col3, col4 = st.sidebar.columns(2)
with col3:
    period2_start = st.date_input("Start", datetime(2025, 1, 1), key="after_start")
with col4:
    period2_end = st.date_input("End", datetime(2025, 1, 31), key="after_end")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏪 Store Filter")
store_filter_type = st.sidebar.radio("Store Type", ["All Store", "Same Store"], label_visibility="collapsed")

store_opening_cutoff = None
if store_filter_type == "Same Store":
    default_cutoff = datetime(2023, 12, 31)
    store_opening_cutoff = st.sidebar.date_input(
        "Opened before", 
        default_cutoff,
        help="Only include stores that opened before this date",
        key="store_cutoff"
    ).strftime("%Y-%m-%d")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")
available_categories = bigquery_client.get_categories()
selected_categories = st.sidebar.multiselect("📂 Category", available_categories, default=[available_categories[0]] if available_categories else [])

selected_subcategories = []
if selected_categories:
    all_subcategories = []
    for cat in selected_categories:
        subcats = bigquery_client.get_subcategories(cat)
        all_subcategories.extend(subcats)
    all_subcategories = list(set(all_subcategories))
    selected_subcategories = st.sidebar.multiselect("📁 SubCategory", all_subcategories)

brands_text = st.sidebar.text_input("🏷️ Brands", placeholder="เช่น NIVEA, VASELINE, CITRA", help="Enter brand names separated by commas")
selected_brands = [b.strip() for b in brands_text.split(',') if b.strip()] if brands_text else []

product_name_contains = st.sidebar.text_input("🔎 Product Contains", placeholder="เช่น โลชั่น, ครีม, นม", help="ใส่คำค้นหาได้หลายคำคั่นด้วยคอมม่า (OR condition)")

product_name_not_contains = st.sidebar.text_input("🚫 Product NOT Contains", placeholder="เช่น PM_, PROMO", help="กรองสินค้าที่มีคำนี้ออก (AND NOT condition)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Threshold")
primary_threshold = st.sidebar.slider("Primary %", float(config.MIN_PRIMARY_THRESHOLD*100), float(config.MAX_PRIMARY_THRESHOLD*100), float(config.DEFAULT_PRIMARY_THRESHOLD*100), step=5.0) / 100.0

barcode_mapping_text = ""
if analysis_mode == "Custom Type":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗂️ Barcode Mapping")
    barcode_mapping_text = st.sidebar.text_area("Paste barcode mapping", barcode_mapping_text, height=150, placeholder="barcode,product_type", help="Format: barcode,product_type (one per line)")

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
        
        st.markdown("---")
    display_category = selected_categories[0] if selected_categories else None
    utils.display_filter_summary(analysis_mode, period1_start.strftime("%Y-%m-%d"), period1_end.strftime("%Y-%m-%d"), period2_start.strftime("%Y-%m-%d"), period2_end.strftime("%Y-%m-%d"), display_category, selected_brands, product_name_contains, primary_threshold, len(utils.parse_barcode_mapping(barcode_mapping_text)) if analysis_mode == "Custom Type" else 0)
    
    st.markdown("---")
    
    st.markdown("## 📊 Section 1: Customer Flow")
    
    # Apply brand filtering based on view mode toggle (only shown when brands are filtered)
    df_display = df  # Default to full data
    
    if selected_brands:
        from modules import brand_filter
        
        # Show view mode toggle
        col_toggle, col_spacer = st.columns([4, 6])
        with col_toggle:
            view_mode = st.radio(
                "🔍 View Mode",
                options=['🔒 Filtered View', '🔓 Full View'],
                index=0,  # Default to Filtered (backward compatible)
                horizontal=True,
                help="🔒 Filtered: Same-brand comparison (e.g., COLGATE ↔ COLGATE) | 🔓 Full: See where filtered brands went (e.g., COLGATE → All Brands)",
                key="view_mode_toggle"
            )
        
        # Determine filter mode from selection
        filter_mode = 'filtered' if '🔒' in view_mode else 'full'
        
        # Apply client-side filter
        df_display = brand_filter.filter_dataframe_by_brands(df, selected_brands, filter_mode)
        
        # Show filter description
        if filter_mode == 'full':
            st.info(f"💡 **Full View**: Showing where **{', '.join(selected_brands)}** customers went (all destination brands visible)")
    
    # Calculate summary AFTER determining df_display (this ensures AI gets correct data)
    summary_df = data_processor.calculate_brand_summary(df_display)
    
    # Use df_display for all visualizations
    labels, sources, targets, values = data_processor.prepare_sankey_data(df_display)
    st.plotly_chart(visualizations.create_sankey_diagram(labels, sources, targets, values), use_container_width=True)
    st.markdown("## 🔥 Section 2: Competitive Matrix")
    st.plotly_chart(visualizations.create_competitive_heatmap(data_processor.prepare_heatmap_data(df_display)), use_container_width=True)
    st.markdown("## 🎯 Section 3: Brand Deep Dive")
    available_brands_for_analysis = summary_df['Brand'].tolist()
    if available_brands_for_analysis:
        selected_focus_brand = st.selectbox("Select brand", available_brands_for_analysis, key="focus_brand")
        if selected_focus_brand:
            st.plotly_chart(visualizations.create_waterfall_chart(data_processor.prepare_waterfall_data(df_display, selected_focus_brand), selected_focus_brand), use_container_width=True)
    st.markdown("## 📋 Section 4: Summary Tables & Charts")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Summary", "🔄 Brand Switching", "📈 Charts", "📄 Raw", "📥 Export"])
    with tab1:
        st.markdown("### Brand Movement Summary")
        display_summary = visualizations.create_summary_table_display(summary_df)
        def make_table(df):
            # Define colors and column widths for better balance
            c = {
                '2024_Total':'#FF9800','Stayed':'#FFB74D','Stayed_%':'#FFB74D',
                'Switch_Out':'#EF5350','Switch_Out_%':'#EF5350',
                'Gone':'#E57373','Gone_%':'#E57373','Total_Out':'#D32F2F',
                'Switch_In':'#66BB6A','New_Customer':'#81C784','Total_In':'#4CAF50',
                '2025_Total':'#42A5F5','Net_Movement':'#1E88E5'
            }
            
            # Define balanced column widths (% based)
            col_widths = {
                'Brand': '10%',
                '2024_Total': '6%', 'Stayed': '5%', 'Stayed_%': '5%',
                'Switch_Out': '6%', 'Switch_Out_%': '6%',
                'Gone': '5%', 'Gone_%': '5%', 'Total_Out': '6%',
                'Switch_In': '6%', 'New_Customer': '8%', 'Total_In': '6%',
                '2025_Total': '6%', 'Net_Movement': '8%'
            }
            
            h = '<table style="width:100%; font-size:12px; border-collapse: collapse;"><thead><tr>'
            for col in df.columns:
                width = col_widths.get(col, '6%')
                h += f'<th style="background:{c.get(col,"#607D8B")}; color:white; padding:10px; vertical-align:middle; text-align:center; width:{width}; white-space:nowrap;">{col.replace("_"," ")}</th>'
            h += '</tr></thead><tbody>'
            for _, row in df.iterrows():
                h += '<tr style="border-bottom: 1px solid #e0e0e0;">'
                for i, (col, v) in enumerate(row.items()):
                    fmt = f"{v:.1f}%" if isinstance(v,(int,float)) and '%' in col else f"{v:,.0f}" if isinstance(v,(int,float)) else str(v)
                    align = "left" if i == 0 else "center"
                    h += f'<td style="padding:8px; text-align:{align}; vertical-align:middle;">{fmt}</td>'
                h += '</tr>'
            return h + '</tbody></table>'
        st.markdown(make_table(display_summary), unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 🔄 Brand Switching Details")
        st.caption("Top brand-to-brand switching flows (excluding New/Gone customers)")
        
        switching_summary = data_processor.get_brand_switching_summary(df_display, top_n=20)
        
        if len(switching_summary) > 0:
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
            
            # Use single quotes for outer string, double quotes for HTML attributes
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
    
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(visualizations.create_movement_type_pie(df_display), use_container_width=True)
        with c2:
            metric = st.selectbox("Metric", ['Net_Movement','Total_In','Total_Out','Stayed'])
            st.plotly_chart(visualizations.create_brand_comparison_bar(summary_df, metric), use_container_width=True)
    with tab4:
        st.markdown("### Raw Data")
        st.dataframe(df_display, use_container_width=True, height=400)
        st.markdown("### Top 10 Flows")
        st.dataframe(data_processor.get_top_flows(df_display, n=10), use_container_width=True)
    with tab5:
        st.markdown("### Export")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📊 Excel", utils.create_excel_export(df_display, summary_df), f"switching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with c2:
            st.download_button("📄 CSV", df_display.to_csv(index=False), f"switching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
    st.markdown("## 🤖 AI-Powered Insights")
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
