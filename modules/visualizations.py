"""
Visualizations Module
Creates interactive Plotly visualizations for switching analysis
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict
import config


def create_sankey_diagram(labels: List[str], sources: List[int], targets: List[int], values: List[int]) -> go.Figure:
    """Create Sankey diagram"""
    node_colors = []
    for label in labels:
        if 'New Customers' in label:
            node_colors.append(config.BRAND_COLORS.get('NEW_TO_CATEGORY', '#4CAF50'))
        elif 'Gone' in label:
            node_colors.append(config.BRAND_COLORS.get('LOST_FROM_CATEGORY', '#9E9E9E'))
        elif 'MIXED' in label:
            node_colors.append(config.BRAND_COLORS.get('MIXED', '#FFC107'))
        else:
            brand_name = label.split('_')[0]
            node_colors.append(config.BRAND_COLORS.get(brand_name, '#2196F3'))
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=20, thickness=25, line=dict(color="white", width=3), label=labels, color=node_colors,
                 customdata=labels, hovertemplate='%{customdata}<br>Total: %{value:,}<extra></extra>'),
        link=dict(source=sources, target=targets, value=values,
                 hovertemplate='From %{source.customdata}<br>To %{target.customdata}<br>Flow: %{value:,}<extra></extra>'),
        textfont=dict(family="Arial", size=16, color="#1a1a1a")
    )])
    fig.update_layout(title={'text': "Customer Flow", 'x': 0.5}, plot_bgcolor='white', height=700)
    return fig


def create_competitive_heatmap(heatmap_df: pd.DataFrame) -> go.Figure:
    """Create heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_df.values, 
        x=heatmap_df.columns, 
        y=heatmap_df.index,
        colorscale='Blues', 
        text=heatmap_df.values, 
        texttemplate='%{text:,}',
        textfont={"size": 11, "color": "#1a1a1a"}
    ))
    fig.update_layout(
        title="Competitive Matrix",
        height=600,
        font=dict(family="Arial", size=12, color="#1a1a1a")
    )
    fig.update_xaxes(
        tickfont=dict(size=13, color="#000000", family="Arial"),
        titlefont=dict(size=14, color="#000000")
    )
    fig.update_yaxes(
        tickfont=dict(size=13, color="#000000", family="Arial"),
        titlefont=dict(size=14, color="#000000")
    )
    return fig


def create_waterfall_chart(waterfall_data: Dict, brand: str) -> go.Figure:
    """Create waterfall chart"""
    fig = go.Figure(go.Waterfall(measure=waterfall_data['measure'], x=waterfall_data['labels'],
                                  y=waterfall_data['values'], text=[f"{v:,}" for v in waterfall_data['values']],
                                  textposition="outside", increasing={"marker": {"color": "#4CAF50"}},
                                  decreasing={"marker": {"color": "#F44336"}}, totals={"marker": {"color": "#2196F3"}}))
    fig.update_layout(title=f"{brand} Movement", height=500)
    return fig


def create_summary_table_display(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Format summary table - keep % for outflows only"""
    display_df = summary_df.copy()
    column_order = ['Brand', '2024_Total', 'Stayed', 'Stayed_%', 'Switch_Out', 'Switch_Out_%', 
                    'Gone', 'Gone_%', 'Total_Out', 'Switch_In', 'New_Customer', 'Total_In', 
                    '2025_Total', 'Net_Movement']
    return display_df[[col for col in column_order if col in display_df.columns]]


def create_movement_type_pie(df: pd.DataFrame) -> go.Figure:
    """Create pie chart"""
    movement_summary = df.groupby('move_type')['customers'].sum().reset_index()
    colors = [config.MOVEMENT_COLORS.get(mt, '#999999') for mt in movement_summary['move_type']]
    fig = go.Figure(data=[go.Pie(labels=movement_summary['move_type'], values=movement_summary['customers'],
                                  marker=dict(colors=colors), textinfo='label+percent')])
    fig.update_layout(title="Movement Distribution", height=400)
    return fig


def create_brand_comparison_bar(summary_df: pd.DataFrame, metric: str = 'Net_Movement') -> go.Figure:
    """Create bar chart"""
    sorted_df = summary_df.sort_values(metric, ascending=False)
    colors = ['#4CAF50' if v >= 0 else '#F44336' for v in sorted_df[metric]]
    fig = go.Figure(data=[go.Bar(x=sorted_df['Brand'], y=sorted_df[metric], marker_color=colors,
                                  text=sorted_df[metric], texttemplate='%{text:,}')])
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(title=f"Brand Comparison: {metric.replace('_', ' ')}", height=450)
    return fig
