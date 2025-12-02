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
        st.session_state.summary_df = data_processor.calculate_brand_summary(df)
    df = st.session_state.results_df
    summary_df = st.session_state.summary_df
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
    st.markdown("## 📊 Section 1: Customer Flow")
    labels, sources, targets, values = data_processor.prepare_sankey_data(df)
    st.plotly_chart(visualizations.create_sankey_diagram(labels, sources, targets, values), use_container_width=True)
    st.markdown("## 🔥 Section 2: Competitive Matrix")
    st.plotly_chart(visualizations.create_competitive_heatmap(data_processor.prepare_heatmap_data(df)), use_container_width=True)
    st.markdown("## 🎯 Section 3: Brand Deep Dive")
    available_brands_for_analysis = summary_df['Brand'].tolist()
    if available_brands_for_analysis:
        selected_focus_brand = st.selectbox("Select brand", available_brands_for_analysis, key="focus_brand")
        if selected_focus_brand:
            st.plotly_chart(visualizations.create_waterfall_chart(data_processor.prepare_waterfall_data(df, selected_focus_brand), selected_focus_brand), use_container_width=True)
    st.markdown("## 📋 Section 4: Summary Tables & Charts")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📈 Charts", "📄 Raw", "📥 Export"])
    with tab1:
        st.markdown("### Brand Movement Summary")
        display_summary = visualizations.create_summary_table_display(summary_df)
        def make_table(df):
            c = {'2024_Total':'#FF9800','Stayed':'#FFB74D','Stayed_%':'#FFB74D','Switch_Out':'#EF5350','Switch_Out_%':'#EF5350','Gone':'#E57373','Gone_%':'#E57373','Total_Out':'#D32F2F','Switch_In':'#66BB6A','New_Customer':'#81C784','Total_In':'#4CAF50','2025_Total':'#42A5F5','Net_Movement':'#1E88E5'}
            h = '<table style="width:100%; font-size:11px"><thead><tr>'
            for col in df.columns:
                h += f'<th style="background:{c.get(col,"#607D8B")}; color:white; padding:8px; vertical-align:middle; text-align:center">{col.replace("_"," ")}</th>'
            h += '</tr></thead><tbody>'
            for _, row in df.iterrows():
                h += '<tr>'
                for i, (col, v) in enumerate(row.items()):
                    fmt = f"{v:.1f}%" if isinstance(v,(int,float)) and '%' in col else f"{v:,.0f}" if isinstance(v,(int,float)) else str(v)
                    h += f'<td style="padding:6px; text-align:{"left" if i==0 else "right"}">{fmt}</td>'
                h += '</tr>'
            return h + '</tbody></table>'
        st.markdown(make_table(display_summary), unsafe_allow_html=True)
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(visualizations.create_movement_type_pie(df), use_container_width=True)
        with c2:
            metric = st.selectbox("Metric", ['Net_Movement','Total_In','Total_Out','Stayed'])
            st.plotly_chart(visualizations.create_brand_comparison_bar(summary_df, metric), use_container_width=True)
    with tab3:
        st.markdown("### Raw Data")
        st.dataframe(df, use_container_width=True, height=400)
        st.markdown("### Top 10 Flows")
        st.dataframe(data_processor.get_top_flows(df, n=10), use_container_width=True)
    with tab4:
        st.markdown("### Export")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📊 Excel", utils.create_excel_export(df, summary_df), f"switching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with c2:
            st.download_button("📄 CSV", df.to_csv(index=False), f"switching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
    st.markdown("## 🤖 AI-Powered Insights")
    if st.button("✨ Generate Complete Analysis"):
        ai_category = selected_categories[0] if selected_categories else None
        insights = ai_analyzer.generate_insights(df, summary_df, ai_category, selected_brands, analysis_mode, f"{period1_start} to {period1_end}", f"{period2_start} to {period2_end}")
        if insights:
            st.markdown(insights, unsafe_allow_html=True)
else:
    st.info("👈 Configure and click **Run Analysis**")
st.markdown("---")
st.markdown('<div style="text-align:center; color:#666">Everything-Switching | BigQuery & OpenAI</div>', unsafe_allow_html=True)
