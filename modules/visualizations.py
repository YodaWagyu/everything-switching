"""
Visualizations Module
Creates interactive Plotly visualizations for switching analysis
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict
import config


def create_sankey_diagram(labels: List[str], sources: List[int], targets: List[int], values: List[int], 
                          min_volume_pct: float = 0.0, highlight_brand: str = None) -> go.Figure:
    """
    Create Sankey diagram with filtering and highlighting options
    
    Args:
        labels: List of node labels
        sources: List of source indices
        targets: List of target indices
        values: List of flow values
        min_volume_pct: Minimum percentage of total flow to display (0-100)
        highlight_brand: Brand to highlight (others will be greyed out)
    """
    # Calculate total volume for percentage filtering
    total_volume = sum(values)
    
    # Filter data based on minimum volume percentage
    filtered_sources = []
    filtered_targets = []
    filtered_values = []
    
    for s, t, v in zip(sources, targets, values):
        if total_volume > 0 and (v / total_volume * 100) >= min_volume_pct:
            # If highlighting is active, check if this flow involves the highlighted brand
            if highlight_brand and highlight_brand != "All":
                source_label = labels[s]
                target_label = labels[t].replace('_2025', '') # Remove suffix for checking
                
                # Check if source or target matches the highlighted brand
                # Handle special categories mapping if needed, but usually brand name is in label
                if highlight_brand in source_label or highlight_brand in target_label:
                    filtered_sources.append(s)
                    filtered_targets.append(t)
                    filtered_values.append(v)
                else:
                    # Optional: Keep them but make them very transparent? 
                    # For now, let's just keep them but color them grey in the link color logic
                    # Or strictly filter them out? Executive said "Highlight brand -> show ONLY related flows"
                    # "แสดงเฉพาะสายที่เกี่ยวกับแบรนด์ที่เลือก" -> Filter out others
                    pass 
            else:
                filtered_sources.append(s)
                filtered_targets.append(t)
                filtered_values.append(v)
    
    # If highlight mode, we might have filtered everything if no matches (unlikely if logic is correct)
    # If NOT highlight mode, we just use the filtered lists based on volume
    
    # Update lists
    final_sources = filtered_sources
    final_targets = filtered_targets
    final_values = filtered_values
    
    # Define Node Colors
    node_colors = []
    for label in labels:
        clean_label = label.replace('_2025', '')
        
        # Determine color based on brand
        if 'New Customers' in clean_label:
            base_color = config.BRAND_COLORS.get('NEW_TO_CATEGORY', '#4CAF50')
        elif 'Gone' in clean_label:
            base_color = config.BRAND_COLORS.get('LOST_FROM_CATEGORY', '#9E9E9E')
        elif 'MIXED' in clean_label:
            base_color = config.BRAND_COLORS.get('MIXED', '#FFC107')
        else:
            brand_name = clean_label.split()[0] # First word assumption
            base_color = config.BRAND_COLORS.get(brand_name, '#2196F3')
            
        # Apply Highlight Logic to Nodes
        if highlight_brand and highlight_brand != "All":
            # If this node is NOT the highlighted brand and NOT a special category connected to it...
            # Actually, simpler: Is this node the highlighted brand?
            if highlight_brand in clean_label:
                node_colors.append(base_color)
            elif clean_label in ['New Customers', 'Gone']:
                 # Keep special categories colored if they are connected? 
                 # Let's keep them colored for context, or maybe grey them too?
                 # Let's keep them standard color but maybe lighter?
                 node_colors.append(base_color) 
            else:
                node_colors.append('#e0e0e0') # Grey out other brands
        else:
            node_colors.append(base_color)

    # Define Link Colors
    link_colors = []
    for s, t, v in zip(final_sources, final_targets, final_values):
        source_label = labels[s]
        target_label = labels[t]
        
        # Default link color (semi-transparent source color)
        # We need to find the color of the source node
        # This is complex to lookup back from the loop above without a map
        # Let's just use a default greyish for links unless highlighted
        
        if highlight_brand and highlight_brand != "All":
             link_colors.append('rgba(15, 61, 62, 0.4)') # Dark Teal transparent for highlighted flows
        else:
             link_colors.append('rgba(189, 189, 189, 0.3)') # Light grey for normal flows to reduce clutter

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20, 
            thickness=25, 
            line=dict(color="white", width=1), 
            label=[l.replace('_2025', '') for l in labels], # Clean labels for display
            color=node_colors,
            customdata=labels, 
            hovertemplate='%{label}<br>Total: %{value:,}<extra></extra>'
        ),
        link=dict(
            source=final_sources, 
            target=final_targets, 
            value=final_values,
            color=link_colors,
            hovertemplate='From %{source.label}<br>To %{target.label}<br>Flow: %{value:,}<br>%{percent} of total<extra></extra>'
        ),
        textfont=dict(family="Inter", size=12, color="#1a1a1a")
    )])
    
    fig.update_layout(
        title={'text': "Customer Flow (Sankey)", 'x': 0.5}, 
        plot_bgcolor='white', 
        height=600,
        margin=dict(l=10, r=10, t=40, b=10)
    )
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
        textfont={"size": 12}  # ไม่กำหนดสี ให้ plotly เลือกเอง
    ))
    fig.update_layout(
        title="Competitive Matrix",
        height=600,
        font=dict(family="Arial", size=13, color="#000000")
    )
    return fig


def create_net_gain_loss_chart(df: pd.DataFrame, target_brand: str) -> go.Figure:
    """
    Create a bar chart showing Net Gain/Loss against competitors for a specific brand
    
    Args:
        df: Switching dataframe
        target_brand: The brand to analyze
    """
    # Filter for flows involving the target brand
    # Gain: Competitor -> Target (Switch In)
    gains = df[(df['prod_2025'] == target_brand) & (df['prod_2024'] != target_brand) & (df['move_type'] == 'switched')]
    
    # Loss: Target -> Competitor (Switch Out)
    losses = df[(df['prod_2024'] == target_brand) & (df['prod_2025'] != target_brand) & (df['move_type'] == 'switched')]
    
    # Aggregate by competitor
    competitor_stats = {}
    
    for _, row in gains.iterrows():
        comp = row['prod_2024']
        if comp not in ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY']:
            if comp not in competitor_stats: competitor_stats[comp] = 0
            competitor_stats[comp] += row['customers']
            
    for _, row in losses.iterrows():
        comp = row['prod_2025']
        if comp not in ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY']:
            if comp not in competitor_stats: competitor_stats[comp] = 0
            competitor_stats[comp] -= row['customers']
            
    # Convert to DataFrame
    if not competitor_stats:
        return go.Figure()
        
    comp_df = pd.DataFrame(list(competitor_stats.items()), columns=['Competitor', 'Net_Flow'])
    comp_df = comp_df.sort_values('Net_Flow', ascending=True) # Losers first, Winners last
    
    colors = ['#c62828' if x < 0 else '#2e7d32' for x in comp_df['Net_Flow']]
    
    fig = go.Figure(go.Bar(
        y=comp_df['Competitor'],
        x=comp_df['Net_Flow'],
        orientation='h',
        marker_color=colors,
        text=comp_df['Net_Flow'],
        texttemplate='%{text:+,}',
        textposition='outside'
    ))
    
    fig.update_layout(
        title=f"Net Gain/Loss: {target_brand} vs Competitors",
        xaxis_title="Net Customers (In - Out)",
        yaxis_title="Competitor",
        height=max(400, len(comp_df) * 30),
        plot_bgcolor='white'
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
