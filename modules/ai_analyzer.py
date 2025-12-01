"""
AI Analyzer Module
OpenAI integration for generating insights from switching analysis
"""

import streamlit as st
from openai import OpenAI
import pandas as pd
from typing import Optional
import config


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
        
        # Build the prompt
        prompt = f"""You are a retail analytics expert analyzing customer brand/product switching patterns.

**Analysis Context:**
- Category: {category}
- Analysis Type: {analysis_mode}
- Brands Analyzed: {', '.join(brands) if brands else 'All'}
- Comparison: {period1_label} vs {period2_label}
- Total Customers: {total_customers:,}

**Movement Breakdown:**
{chr(10).join([f"- {k}: {v:,} customers ({v/total_customers*100:.1f}%)" for k, v in movement_breakdown.items()])}

**Top 3 Gainers (Net Movement):**
{top_gainers.to_string(index=False)}

**Top 3 Losers (Net Movement):**
{top_losers.to_string(index=False)}

**Top 5 Switching Flows:**
{top_flows.to_string(index=False)}

**Your Task:**
Provide a comprehensive analysis with the following sections:

1. Executive Summary (2-3 sentences highlighting the most important finding)

2. Key Findings (3-5 bullet points covering):
   - Major winners and losers
   - Significant switching patterns
   - Notable trends

3. Strategic Recommendations (3-4 actionable recommendations based on the data)

Format your response in clean markdown. Be specific with numbers. Focus on actionable insights.
"""

        # Call OpenAI API
        with st.spinner("🤖 Generating AI insights..."):
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a retail analytics expert specializing in customer behavior and brand switching analysis. Provide clear, actionable insights based on data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )
        
        insights = response.choices[0].message.content
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
                {"role": "system", "content": "You are a brand strategist analyzing customer movement patterns."},
                {"role": "user", "content": prompt}
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
                {"role": "system", "content": "You are a customer behavior analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=400
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"❌ Failed to generate Sankey insights: {str(e)}")
        return None
