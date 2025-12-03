"""
AI Analyzer Module
OpenAI integration for generating insights from switching analysis
"""

import streamlit as st
from openai import OpenAI
import pandas as pd
from typing import Optional
import config
import re


def get_openai_client() -> OpenAI:
    """
    Initialize and return OpenAI client
    
    Returns:
        OpenAI: Authenticated OpenAI client
    """
    try:
        api_key = st.secrets["openai"]["api_key"]
        client = OpenAI(api_key=api_key)
        return client
    except KeyError:
        st.error("❌ OpenAI API key not found in secrets. Please add it to Streamlit Cloud secrets.")
        st.info("Add `[openai]` section with `api_key = \"sk-...\"` to your secrets")
        return None
    except Exception as e:
        st.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
        return None


def highlight_brands_in_text(text: str, brands: list) -> str:
    """
    Highlight brand and product names with distinct colors in markdown text
    
    Args:
        text (str): AI-generated text
        brands (list): List of brands to highlight
    
    Returns:
        str: Text with HTML color highlights
    """
    if not brands or not text:
        return text
    
    # Define color palette for brands
    brand_colors = [
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Sky Blue
        '#FFA07A',  # Light Salmon
        '#98D8C8',  # Mint
        '#F7DC6F',  # Yellow
        '#BB8FCE',  # Purple
        '#85C1E2',  # Light Blue
        '#F8B88B',  # Peach
        '#92DCE5',  # Aqua
    ]
    
    highlighted_text = text
    
    # Create brand to color mapping
    brand_color_map = {}
    for i, brand in enumerate(brands):
        color = brand_colors[i % len(brand_colors)]
        brand_color_map[brand] = color
    
    # Sort brands by length (longest first) to avoid partial matches
    sorted_brands = sorted(brands, key=len, reverse=True)
    
    # Highlight each brand
    for brand in sorted_brands:
        if not brand:
            continue
        color = brand_color_map[brand]
        # Use case-insensitive replacement
        # Escape the brand name for regex but be more flexible with matching
        escaped_brand = re.escape(brand)
        # Match brand name surrounded by word boundaries or start/end of line
        pattern = re.compile(rf'(?<![a-zA-Z0-9])({escaped_brand})(?![a-zA-Z0-9])', re.IGNORECASE)
        highlighted_text = pattern.sub(
            rf'<span style="background-color: {color}; color: #000; padding: 2px 6px; border-radius: 3px; font-weight: 600;">\1</span>',
            highlighted_text
        )
    
    return highlighted_text


def generate_insights(
    df: pd.DataFrame,
    summary_df: pd.DataFrame,
    category: str,
    brands: list,
    analysis_mode: str,
    period1_label: str = "Period 1",
    period2_label: str = "Period 2"
) -> Optional[str]:
    """
    Generate AI-powered insights from switching analysis results
    
    Args:
        df (pd.DataFrame): Raw query results
        summary_df (pd.DataFrame): Brand summary data
        category (str): Category analyzed
        brands (list): Brands included in analysis
        analysis_mode (str): Analysis mode used
        period1_label (str): Label for period 1
        period2_label (str): Label for period 2
    
    Returns:
        Optional[str]: AI-generated insights in markdown format
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Prepare data summary for the prompt
        total_customers = df['customers'].sum()
        
        # Movement type breakdown
        movement_breakdown = df.groupby('move_type')['customers'].sum().to_dict()
        
        # Top gainers and losers
        top_gainers = summary_df.nlargest(3, 'Net_Movement')[['Brand', 'Net_Movement', '2024_Total', '2025_Total']]
        top_losers = summary_df.nsmallest(3, 'Net_Movement')[['Brand', 'Net_Movement', '2024_Total', '2025_Total']]
        
        # Top switching flows
        top_flows = df[df['move_type'] == 'switched'].nlargest(5, 'customers')[
            ['prod_2024', 'prod_2025', 'customers']
        ]
        
        # Build the prompt with CLEAR brand-by-brand breakdown
        prompt = f"""You are a retail analytics expert analyzing customer switching patterns in a casual, friendly tone.

**Analysis Context:**
- Category: {category}
- Analysis Type: {analysis_mode}
- Items Analyzed: {', '.join(brands) if brands else 'All'}
- Comparison: {period1_label} vs {period2_label}
- Total Customers: {total_customers:,}

**Movement Breakdown:**
{chr(10).join([f"- {k}: {v:,} customers ({v/total_customers*100:.1f}%)" for k, v in movement_breakdown.items()])}

**Brand-by-Brand Summary:**
{summary_df.to_string(index=False)}

**IMPORTANT:** The table above shows EACH BRAND separately. Each row is ONE brand with its OWN metrics.

⚠️ **THE NUMBERS BELOW ARE EXAMPLES ONLY - NOT REAL DATA. USE THE ACTUAL DATA FROM THE TABLE ABOVE.**

For example, if a hypothetical BRAND_X row shows:
- 2024_Total: N1
- Gone: N2
- Switch_Out: N3

This means BRAND_X specifically (NOT all brands combined) had N1 customers in Before Period, N2 went "Gone", and N3 switched to other brands.

DO NOT sum up the "Gone" column or any other column across all brands unless you're explicitly talking about total market movement.

**TEMPORAL CONTEXT - READ CAREFULLY:**
This is a COHORT analysis comparing TWO time periods:
- **Before Period ({period1_label})**: Our BASELINE - customers who purchased in this period
- **After Period ({period2_label})**: Where did those baseline customers go?

Column meanings:
- **2024_Total**: Customers in Before Period (BASELINE)
- **Stayed**: Customers from Before Period who came back in After Period
- **Switch_Out**: Customers from Before Period who switched to other brands in After Period
- **Gone**: Customers from Before Period who did NOT purchase in After Period (left category)
- **Switch_In**: NEW customers in After Period who came from other brands
- **New_Customer**: NEW customers in After Period who were not in the category during Before Period
- **2025_Total**: Total customers in After Period

**CRITICAL - How to describe movements:**

⚠️ **ALL EXAMPLES BELOW USE PLACEHOLDER NUMBERS (X, Y, N) - YOU MUST USE ACTUAL NUMBERS FROM THE TABLE**

❌ WRONG: "BRAND_X เสียลูกค้าไป X คน ในปี 2024" (implies loss happened IN 2024)
✅ CORRECT: "ลูกค้าเก่าของ BRAND_X จำนวน X คน (Y%) ไม่กลับมาในช่วง After Period"
✅ CORRECT: "BRAND_X สูญเสียลูกค้าเก่า X คน (Y%)"

**Percentage Guidelines:**
- The table ALREADY contains pre-calculated percentages in columns ending with "_%"
- **ALWAYS use these pre-calculated percentages** - DO NOT calculate your own
- Column meanings:
  - **Gone_%**, **Switch_Out_%**, **Stayed_%**: Calculated from 2024_Total (Before Period baseline)
  - **Switch_In_%**, **New_Customer_%**: Calculated as share of Total_In
- ⚠️ Example format (X and Y are placeholders - use real values): "Gone X คน (Y%)" - use Y from the table's "Gone_%" column
- NEVER calculate percentages yourself - always use the values from "_%"columns

**Top 3 Gainers (Net Movement):**
{top_gainers.to_string(index=False)}

**Top 3 Losers (Net Movement):**
{top_losers.to_string(index=False)}

**Top 5 Switching Flows:**
{top_flows.to_string(index=False)}

**Your Task:**
Write your analysis in Thai language with a casual, friendly tone. Structure your response EXACTLY like this:

## Executive Summary

[2-3 ประโยคสรุปสิ่งที่น่าสนใจที่สุด พูดแบบสบายๆ เหมือนคุยกับเพื่อน ใส่ตัวเลขและเปอร์เซ็นต์เสมอ]

## Key Findings

- [ข้อค้นพบที่ 1: ใครได้/เสียลูกค้าไปเยอะ **ต้องมีตัวเลขจริง + เปอร์เซ็นต์ในวงเล็บ** เช่น "NIVEA ได้ลูกค้าเพิ่ม 1,500 คน (+20%)"]
- [ข้อค้นพบที่ 2: รูปแบบการย้ายที่เด่นชัด **ระบุจำนวนลูกค้าและเปอร์เซ็นต์** เช่น "ลูกค้าย้ายจาก X ไป Y 800 คน (15% ของ X)"]
- [ข้อค้นพบที่ 3: เทรนด์หรือ composition **ใส่ breakdown** เช่น "สินค้าประเภท AHA คิดเป็น 65% ของลูกค้าทั้งหมด ส่วนอื่นๆ 35%"]
- [ข้อค้นพบเพิ่มเติม 2-3 ข้อ **ทุกข้อต้องมีตัวเลข และ composition ถ้าเป็นไปได้**]

## Strategic Recommendations

- [คำแนะนำที่ 1: เฉพาะเจาะจง **อ้างอิงตัวเลขจากข้อมูล** เช่น "เน้นรักษา X เพราะมีลูกค้าเยอะที่สุด 5,000 คน (40% ของตลาด)"]
- [คำแนะนำที่ 2: **มีตัวเลขประกอบ**]
- [คำแนะนำที่ 3: **มีตัวเลขประกอบ**]
- [คำแนะนำที่ 4 (ถ้ามี)]

**Critical Rules:**
- Section headers MUST be in English: "## Executive Summary", "## Key Findings", "## Strategic Recommendations"
- Content MUST be in Thai with a casual, conversational tone
- DO NOT use "แบรนด์" or "สินค้า" before product/brand names
- **⚠️ USE ONLY ACTUAL DATA FROM THE TABLE - NOT EXAMPLE NUMBERS**
- **ALWAYS use pre-calculated percentages from "_%" columns** - DO NOT calculate your own
- **When describing Gone/Switch_Out**, use CORRECT temporal phrasing:
  ⚠️ Examples use placeholders (X, Y, BRAND_X) - replace with real data from table:
  ❌ WRONG: "BRAND_X เสียลูกค้าไป X คน ในปี 2024" or "ในช่วงปี 2024"
  ✅ CORRECT: "ลูกค้าเก่าของ BRAND_X X คน (Y%) ไม่กลับมาในช่วง After Period"
  ✅ CORRECT: "BRAND_X สูญเสียลูกค้าเก่า X คน (Y%)"
- **When describing New_Customer**, use the pre-calculated percentage:
  ⚠️ The numbers X and Y below are placeholders - use actual values from the table:
  ❌ WRONG: "ได้ลูกค้าใหม่ X คน (+Y%)" (Don't calculate new percentages)
  ✅ CORRECT: "มีลูกค้าใหม่เข้ามา X คน (Y% ของลูกค้าทั้งหมดใน After Period)" (Use New_Customer_% from table)
- **When discussing trends or patterns, include composition/breakdown** (e.g., "สินค้า AHA คิดเป็น 65%, ส่วนอื่นๆ 35%")
- NEVER use vague terms like "เล็กน้อย", "เยอะ", "พอสมควร" - use actual numbers instead
- Use format: "[number with comma] คน ([percentage]%)" - Example: "2,500 คน (15%)" or "1,200 คน (10%)"
- When mentioning any gain/loss, ALWAYS backup with specific customer count and percentage FROM THE TABLE
- **READ VALUES FROM THE CORRECT BRAND ROW** - Don't sum columns across brands unless explicitly describing total market
- Calculate compositions from the data provided - DO NOT make up numbers
- **VERIFY EVERY NUMBER YOU USE EXISTS IN THE PROVIDED DATA** - Do not use numbers from examples

"""

        # Call OpenAI API
        with st.spinner("🤖 Generating AI insights..."):
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a retail analytics expert specializing in customer behavior and brand switching analysis. Provide clear, actionable insights based on data. Always respond in Thai language (ภาษาไทย)."},
                    {"role": "user", "content": prompt + "\n\n**IMPORTANT: Please respond in Thai language (ภาษาไทย) only.**"}
                ],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )

        insights = response.choices[0].message.content
        
        # Highlight brands in the response
        if brands:
            insights = highlight_brands_in_text(insights, brands)
        
        return insights
        
    except Exception as e:
        st.error(f"❌ Failed to generate AI insights: {str(e)}")
        return None


def generate_brand_specific_insights(
    df: pd.DataFrame,
    brand: str,
    waterfall_data: dict,
    period1_label: str = "Period 1",
    period2_label: str = "Period 2"
) -> Optional[str]:
    """
    Generate brand-specific insights for waterfall analysis
    
    Args:
        df (pd.DataFrame): Raw query results
        brand (str): Brand to analyze
        waterfall_data (dict): Waterfall data for the brand
        period1_label (str): Label for period 1
        period2_label (str): Label for period 2
    
    Returns:
        Optional[str]: AI-generated brand insights
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Find where customers are coming from and going to
        inflow_from = df[
            (df['prod_2025'] == brand) & 
            (df['prod_2024'] != brand)
        ].nlargest(3, 'customers')[['prod_2024', 'customers']]
        
        outflow_to = df[
            (df['prod_2024'] == brand) & 
            (df['prod_2025'] != brand)
        ].nlargest(3, 'customers')[['prod_2025', 'customers']]
        
        # Extract waterfall values
        period1_total = waterfall_data['values'][0]
        new_customers = waterfall_data['values'][1]
        switch_in = waterfall_data['values'][2]
        switch_out = abs(waterfall_data['values'][3])
        gone = abs(waterfall_data['values'][4])
        period2_total = waterfall_data['values'][5]
        
        net_change = period2_total - period1_total
        pct_change = (net_change / period1_total * 100) if period1_total > 0 else 0
        
        prompt = f"""Analyze the customer movement for brand: {brand}

**Overall Change:**
- {period1_label}: {period1_total:,} customers
- {period2_label}: {period2_total:,} customers
- Net Change: {net_change:+,} ({pct_change:+.1f}%)

**Customer Gains:**
- New to Category: {new_customers:,}
- Switched In from competitors: {switch_in:,}

**Customer Losses:**
- Switched Out to competitors: {switch_out:,}
- Lost from Category: {gone:,}

**Top Inflow Sources:**
{inflow_from.to_string(index=False) if not inflow_from.empty else 'None'}

**Top Outflow Destinations:**
{outflow_to.to_string(index=False) if not outflow_to.empty else 'None'}

Provide a brief analysis (3-4 sentences) focusing on:
1. Whether the brand is growing or declining
2. Main sources of gain/loss
3. One key recommendation
"""

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a brand strategist analyzing customer movement patterns. Always respond in Thai language (ภาษาไทย)."},
                {"role": "user", "content": prompt + "\n\n**IMPORTANT: Please respond in Thai language (ภาษาไทย) only.**"}
            ],
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"❌ Failed to generate brand insights: {str(e)}")
        return None


def generate_sankey_insights(
    df: pd.DataFrame,
    category: str,
    period1_label: str = "Period 1",
    period2_label: str = "Period 2"
) -> Optional[str]:
    """
    Generate insights focused on overall flow patterns
    
    Args:
        df (pd.DataFrame): Raw query results
        category (str): Category analyzed
        period1_label (str): Label for period 1
        period2_label (str): Label for period 2
    
    Returns:
        Optional[str]: AI-generated Sankey-focused insights
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Analyze flow patterns
        stayed = df[df['move_type'] == 'stayed']['customers'].sum()
        switched = df[df['move_type'] == 'switched']['customers'].sum()
        new_customers = df[df['move_type'] == 'new']['customers'].sum()
        gone = df[df['move_type'] == 'gone']['customers'].sum()
        total = stayed + switched + new_customers + gone
        
        # Top switching flows
        top_switches = df[df['move_type'] == 'switched'].nlargest(5, 'customers')[
            ['prod_2024', 'prod_2025', 'customers']
        ]
        
        prompt = f"""Analyze customer flow patterns for {category}:

**Overall Flow:**
- Stayed Loyal: {stayed:,} ({stayed/total*100:.1f}%)
- Switched Brands: {switched:,} ({switched/total*100:.1f}%)
- New to Category: {new_customers:,} ({new_customers/total*100:.1f}%)
- Left Category: {gone:,} ({gone/total*100:.1f}%)

**Top 5 Switching Paths:**
{top_switches.to_string(index=False)}

Provide 2-3 key insights about:
1. Customer loyalty vs mobility
2. Most significant switching patterns
3. Strategic implications
"""

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a customer behavior analyst. Always respond in Thai language (ภาษาไทย)."},
                {"role": "user", "content": prompt + "\n\n**IMPORTANT: Please respond in Thai language (ภาษาไทย) only.**"}
            ],
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=400
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"❌ Failed to generate Sankey insights: {str(e)}")
        return None
