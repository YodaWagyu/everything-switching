"""
Query Builder Module
Builds dynamic SQL queries based on user selections
"""

from typing import Optional, Dict, Any
import config


def build_case_statement(barcode_mapping: str) -> str:
    """
    Build SQL CASE WHEN statement from user's barcode mapping
    
    Args:
        barcode_mapping (str): User-provided barcode-to-description mapping
                              Format: "barcode,description" (one per line)
    
    Returns:
        str: SQL CASE WHEN statement
    """
    if not barcode_mapping or not barcode_mapping.strip():
        return "pm.Brand"  # Default fallback
    
    lines = barcode_mapping.strip().split('\n')
    case_parts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Support both comma and tab separated
        parts = line.replace('\t', ',').split(',', 1)
        
        if len(parts) == 2:
            barcode = parts[0].strip()
            description = parts[1].strip()
            
            # Escape single quotes to prevent SQL injection
            description = description.replace("'", "''")
            barcode = barcode.replace("'", "''")
            
            case_parts.append(f"      WHEN a.Barcode = '{barcode}' THEN '{description}'")
    
    if not case_parts:
        return "pm.Brand"  # Default if no valid mappings
    
    # Build complete CASE statement
    case_statement = "CASE\n" + "\n".join(case_parts) + "\n      ELSE 'Other'\n    END"
    return case_statement


def build_switching_query(
    analysis_mode: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    category: str,
    brands: list,
    product_name_contains: Optional[str] = None,
    primary_threshold: float = 0.60,
    barcode_mapping: Optional[str] = None,
    store_filter_type: str = "All Store",
    store_opening_cutoff: Optional[str] = None
) -> str:
    """
    Build the complete switching analysis SQL query
    
    Args:
        analysis_mode (str): Analysis mode ('Brand Switch', 'Product Switch', 'Custom Type')
        period1_start (str): Start date for period 1 (YYYY-MM-DD)
        period1_end (str): End date for period 1 (YYYY-MM-DD)
        period2_start (str): Start date for period 2 (YYYY-MM-DD)
        period2_end (str): End date for period 2 (YYYY-MM-DD)
        category (str): Category name to filter
        brands (list): List of brand names to filter
        product_name_contains (str, optional): Text to search in product names
        primary_threshold (float): Threshold for primary item (0.0 to 1.0)
        barcode_mapping (str, optional): Custom barcode mapping for Custom Type mode
        store_filter_type (str): "All Store" or "Same Store"
        store_opening_cutoff (str, optional): Date cutoff for Same Store (YYYY-MM-DD)
    
    Returns:
        str: Complete SQL query
    """
    
    # Determine TargetItem expression based on analysis mode
    if analysis_mode == "Custom Type" and barcode_mapping:
        target_item_expr = build_case_statement(barcode_mapping)
    elif analysis_mode == "Product Switch":
        target_item_expr = "pm.ProductName"
    else:  # Brand Switch (default)
        target_item_expr = "pm.Brand"
    
    # Build brand filter
    if brands:
        # Escape single quotes in brand names
        escaped_brands = []
        for b in brands:
            escaped_b = b.replace("'", "''")
            escaped_brands.append(f"'{escaped_b}'")
        brand_filter = f"AND pm.Brand IN ({', '.join(escaped_brands)})"
    else:
        brand_filter = ""
    
    # Build product name filter - supports multiple keywords with comma separation
    if product_name_contains and product_name_contains.strip():
        # Split by comma and clean up each term
        keywords = [k.strip() for k in product_name_contains.split(',') if k.strip()]
        
        if keywords:
            # Build OR conditions for multiple keywords
            conditions = []
            for keyword in keywords:
                escaped_keyword = keyword.replace("'", "''")
                conditions.append(f"pm.ProductName LIKE '%{escaped_keyword}%'")
            
            # Combine with OR
            product_filter = f"AND ({' OR '.join(conditions)})"
        else:
            product_filter = ""
    else:
        product_filter = ""
    
    # Build store opening date filter
    if store_filter_type == "Same Store" and store_opening_cutoff:
        store_filter = f"AND br.openingdate <= '{store_opening_cutoff}'"
    else:
        # All Store - no filter on opening date
        store_filter = ""
    
    # Escape category name
    category_escaped = category.replace("'", "''")
    
    # Build the complete query
    query = f"""
DECLARE start_2024 DATE DEFAULT '{period1_start}';
DECLARE end_2024   DATE DEFAULT '{period1_end}';
DECLARE start_2025 DATE DEFAULT '{period2_start}';
DECLARE end_2025   DATE DEFAULT '{period2_end}';
DECLARE PRIMARY_THRESHOLD FLOAT64 DEFAULT {primary_threshold};

WITH base AS (
  SELECT
    a.Date,
    -- Create Year flag for easy grouping
    CASE
      WHEN a.Date BETWEEN start_2024 AND end_2024 THEN 2024
      WHEN a.Date BETWEEN start_2025 AND end_2025 THEN 2025
    END AS Year,
    a.CustomerCode,
    a.DocNo,
    COALESCE(a.TotalSales, 0) AS TotalSales,
    -- Dynamic TargetItem based on analysis mode
    {target_item_expr} AS TargetItem
  FROM `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_SALES}` a
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_PRODUCT_MASTER}` pm
    ON a.Barcode = pm.Barcode
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_BRANCH}` br
    ON a.BranchCode = br.BranchCode
  WHERE pm.CategoryName = '{category_escaped}'
    {brand_filter}
    {product_filter}
    {store_filter}
    AND (
      a.Date BETWEEN start_2024 AND end_2024 OR
      a.Date BETWEEN start_2025 AND end_2025
    )
    AND CustomerCode != '0'
),

cust_item_stats AS (
  SELECT
    Year,
    CustomerCode,
    TargetItem,
    SUM(TotalSales) AS sales_item,
    MAX(Date) AS last_tx,
    -- Calculate % Share using Window Function
    SAFE_DIVIDE(SUM(TotalSales), SUM(SUM(TotalSales)) OVER(PARTITION BY Year, CustomerCode)) AS share_item
  FROM base
  WHERE Year IS NOT NULL -- Filter out dates outside the periods
  GROUP BY 1, 2, 3
),

primary_identification AS (
  SELECT
    Year,
    CustomerCode,
    -- Logic: If Share >= threshold, assign item name, otherwise 'MIXED'
    CASE
      WHEN share_item >= PRIMARY_THRESHOLD THEN TargetItem
      ELSE 'MIXED'
    END AS primary_item
  FROM cust_item_stats
  -- Use QUALIFY to get only the #1 item for each customer in each year
  QUALIFY ROW_NUMBER() OVER(
    PARTITION BY Year, CustomerCode
    ORDER BY
      CASE WHEN share_item >= PRIMARY_THRESHOLD THEN 1 ELSE 0 END DESC,
      share_item DESC,
      sales_item DESC,
      last_tx DESC
  ) = 1
),

customer_flow AS (
  SELECT
    CustomerCode,
    -- Pivot data so each customer is on one row
    MAX( CASE WHEN Year = 2024 THEN primary_item END) AS item_2024,
    MAX(CASE WHEN Year = 2025 THEN primary_item END) AS item_2025
  FROM primary_identification
  GROUP BY CustomerCode
),

classify AS (
  SELECT
    COALESCE(item_2024, 'NEW_TO_CATEGORY') AS prod_2024,
    COALESCE(item_2025, 'LOST_FROM_CATEGORY') AS prod_2025,
    COUNT(*) AS customers,
    CASE
      WHEN item_2024 IS NULL AND item_2025 IS NOT NULL THEN 'new_to_category'
      WHEN item_2024 IS NOT NULL AND item_2025 IS NULL THEN 'lost_from_category'
      WHEN item_2024 = item_2025 THEN 'stayed'
      WHEN item_2024 != item_2025 THEN 'switched' -- Includes Mixed -> Brand or Brand A -> Brand B
      ELSE 'unknown'
    END AS move_type
  FROM customer_flow
  GROUP BY 1, 2, 4
)

SELECT * FROM classify
ORDER BY move_type, prod_2024, prod_2025;
"""
    
    return query
