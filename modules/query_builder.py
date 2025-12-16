"""
Query Builder Module
Builds dynamic SQL queries based on user selections
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Original by Kritin Kayaras
© 2025 All Rights Reserved
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
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    category: str,
    brands: list,
    subcategories: list = None,
    product_name_contains: Optional[str] = None,
    product_name_not_contains: Optional[str] = None,
    primary_threshold: float = 0.60,
    barcode_mapping: Optional[str] = None,
    store_filter_type: str = "All Store",
    store_opening_cutoff: Optional[str] = None
) -> str:
    """
    Build the complete switching analysis SQL query
    
    Always runs at Product level with ProductName, Barcode, and Brand.
    View toggle (Brand/Product) is handled post-query in the UI.
    
    Args:
        period1_start (str): Start date for period 1 (YYYY-MM-DD)
        period1_end (str): End date for period 1 (YYYY-MM-DD)
        period2_start (str): Start date for period 2 (YYYY-MM-DD)
        period2_end (str): End date for period 2 (YYYY-MM-DD)
        category (str): Category name to filter
        brands (list): List of brand names to filter (optional, filter at query level)
        subcategories (list): List of subcategory names to filter (optional)
        product_name_contains (str, optional): Text to search in product names (OR condition)
        product_name_not_contains (str, optional): Text to exclude from product names (AND NOT condition)
        primary_threshold (float): Threshold for primary item (0.0 to 1.0)
        barcode_mapping (str, optional): Custom barcode mapping for Custom Type mode
        store_filter_type (str): "All Store" or "Same Store"
        store_opening_cutoff (str, optional): Date cutoff for Same Store (YYYY-MM-DD)
    
    Returns:
        str: Complete SQL query
    """
    
    # Always use ProductName as TargetItem (unless custom mapping provided)
    if barcode_mapping:
        target_item_expr = build_case_statement(barcode_mapping)
    else:
        target_item_expr = "pm.ProductName"
    
    # Build brand filter - ASYMMETRIC: Period 1 filtered, Period 2 unfiltered
    if brands:
        # Escape single quotes in brand names
        escaped_brands = []
        for b in brands:
            escaped_b = b.replace("'", "''")
            escaped_brands.append(f"'{escaped_b}'")
        brand_filter_period1 = f"pm.Brand IN ({', '.join(escaped_brands)})"
    else:
        brand_filter_period1 = ""
    
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
    
    # Build product name NOT filter - exclude products containing these keywords
    if product_name_not_contains and product_name_not_contains.strip():
        # Split by comma and clean up each term
        exclude_keywords = [k.strip() for k in product_name_not_contains.split(',') if k.strip()]
        
        if exclude_keywords:
            # Build AND NOT conditions for multiple keywords
            not_conditions = []
            for keyword in exclude_keywords:
                # Escape single quotes for SQL
                escaped_keyword = keyword.replace("'", "''")
                # Escape SQL LIKE wildcards: _ and % with double backslash
                escaped_keyword = escaped_keyword.replace('_', '\\\\_').replace('%', '\\\\%')
                not_conditions.append(f"pm.ProductName NOT LIKE '%{escaped_keyword}%'")
            
            # Combine with AND
            product_not_filter = f"AND {' AND '.join(not_conditions)}"
        else:
            product_not_filter = ""
    else:
        product_not_filter = ""
    
    # Build store opening date filter
    if store_filter_type == "Same Store" and store_opening_cutoff:
        store_filter = f"AND br.openingdate <= '{store_opening_cutoff}'"
    else:
        # All Store - no filter on opening date
        store_filter = ""
    
    # Escape category name
    category_escaped = category.replace("'", "''")
    
    # Build subcategory filter
    if subcategories and len(subcategories) > 0:
        escaped_subcats = [s.replace("'", "''") for s in subcategories]
        subcat_list = ", ".join([f"'{s}'" for s in escaped_subcats])
        subcategory_filter = f"AND pm.SubCategoryName IN ({subcat_list})"
    else:
        subcategory_filter = ""
    
    # Build the complete query with period-conditional brand filtering
    # When brands are filtered: Period 1 applies filter, Period 2 gets all brands
    # This enables "Gone vs Switch to Other Brands" analysis
    if brand_filter_period1:
        # Asymmetric filtering: Period 1 filtered, Period 2 unfiltered
        date_filter = f"""AND (
      (a.Date BETWEEN period1_start_date AND period1_end_date AND {brand_filter_period1})
      OR
      (a.Date BETWEEN period2_start_date AND period2_end_date)
    )"""
    else:
        # No brand filter: symmetric behavior
        date_filter = f"""AND (
      a.Date BETWEEN period1_start_date AND period1_end_date OR
      a.Date BETWEEN period2_start_date AND period2_end_date
    )"""
    
    query = f"""
DECLARE period1_start_date DATE DEFAULT '{period1_start}';
DECLARE period1_end_date   DATE DEFAULT '{period1_end}';
DECLARE period2_start_date DATE DEFAULT '{period2_start}';
DECLARE period2_end_date   DATE DEFAULT '{period2_end}';
DECLARE PRIMARY_THRESHOLD FLOAT64 DEFAULT {primary_threshold};

WITH base AS (
  SELECT
    a.Date,
    CASE
      WHEN a.Date BETWEEN period1_start_date AND period1_end_date THEN 2024
      WHEN a.Date BETWEEN period2_start_date AND period2_end_date THEN 2025
    END AS Year,
    a.CustomerCode,
    a.DocNo,
    COALESCE(a.TotalSales, 0) AS TotalSales,
    -- Always capture all 3 identifiers
    {target_item_expr} AS TargetItem,
    a.Barcode AS Barcode,
    pm.Brand AS Brand
  FROM `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_SALES}` a
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_PRODUCT_MASTER}` pm
    ON a.Barcode = pm.Barcode
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_BRANCH}` br
    ON a.BranchCode = br.BranchCode
  WHERE pm.CategoryName = '{category_escaped}'
    {subcategory_filter}
    {product_filter}
    {product_not_filter}
    {store_filter}
    {date_filter}
    AND CustomerCode != '0'
),

cust_item_stats AS (
  SELECT
    Year,
    CustomerCode,
    TargetItem,
    Brand,
    -- Get any barcode for this product (for filtering purposes)
    ANY_VALUE(Barcode) AS Barcode,
    SUM(TotalSales) AS sales_item,
    MAX(Date) AS last_tx,
    SAFE_DIVIDE(SUM(TotalSales), SUM(SUM(TotalSales)) OVER(PARTITION BY Year, CustomerCode)) AS share_item
  FROM base
  WHERE Year IS NOT NULL
  GROUP BY 1, 2, 3, 4
),

primary_identification AS (
  SELECT
    Year,
    CustomerCode,
    CASE
      WHEN share_item >= PRIMARY_THRESHOLD THEN TargetItem
      ELSE 'MIXED'
    END AS primary_item,
    CASE
      WHEN share_item >= PRIMARY_THRESHOLD THEN Barcode
      ELSE NULL
    END AS primary_barcode,
    CASE
      WHEN share_item >= PRIMARY_THRESHOLD THEN Brand
      ELSE 'MIXED'
    END AS primary_brand
  FROM cust_item_stats
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
    -- Period 1 (2024)
    MAX(CASE WHEN Year = 2024 THEN primary_item END) AS item_2024,
    MAX(CASE WHEN Year = 2024 THEN primary_barcode END) AS barcode_2024,
    MAX(CASE WHEN Year = 2024 THEN primary_brand END) AS brand_2024,
    -- Period 2 (2025)
    MAX(CASE WHEN Year = 2025 THEN primary_item END) AS item_2025,
    MAX(CASE WHEN Year = 2025 THEN primary_barcode END) AS barcode_2025,
    MAX(CASE WHEN Year = 2025 THEN primary_brand END) AS brand_2025
  FROM primary_identification
  GROUP BY CustomerCode
),

classify AS (
  SELECT
    -- Product columns
    COALESCE(item_2024, 'NEW_TO_CATEGORY') AS prod_2024,
    COALESCE(item_2025, 'LOST_FROM_CATEGORY') AS prod_2025,
    -- Barcode columns
    barcode_2024,
    barcode_2025,
    -- Brand columns
    COALESCE(brand_2024, 'NEW_TO_CATEGORY') AS brand_2024,
    COALESCE(brand_2025, 'LOST_FROM_CATEGORY') AS brand_2025,
    -- Counts and move type
    COUNT(*) AS customers,
    CASE
      WHEN item_2024 IS NULL AND item_2025 IS NOT NULL THEN 'new_to_category'
      WHEN item_2024 IS NOT NULL AND item_2025 IS NULL THEN 'lost_from_category'
      WHEN item_2024 = item_2025 THEN 'stayed'
      WHEN item_2024 != item_2025 THEN 'switched'
      ELSE 'unknown'
    END AS move_type
  FROM customer_flow
  GROUP BY 1, 2, 3, 4, 5, 6, 8
)

SELECT * FROM classify
ORDER BY move_type, prod_2024, prod_2025;
"""
    
    return query


def build_cross_category_query(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    source_categories: list,
    source_subcategories: list = None,
    target_categories: list = None,
    target_subcategories: list = None,
    primary_threshold: float = 0.60,
    store_filter_type: str = "All Store",
    store_opening_cutoff: str = None
) -> str:
    """
    Build query for cross-category switching analysis.
    
    Tracks customers from Source Category/SubCategory in First Period
    to Target Category/SubCategory in After Period.
    
    Args:
        period1_start (str): Start date for period 1 (YYYY-MM-DD)
        period1_end (str): End date for period 1 (YYYY-MM-DD)
        period2_start (str): Start date for period 2 (YYYY-MM-DD)
        period2_end (str): End date for period 2 (YYYY-MM-DD)
        source_categories (list): List of source category names
        source_subcategories (list): List of source subcategory names (optional)
        target_categories (list): List of target category names
        target_subcategories (list): List of target subcategory names (optional)
        primary_threshold (float): Threshold for primary category (0.0 to 1.0)
        store_filter_type (str): "All Store" or "Same Store"
        store_opening_cutoff (str): Date cutoff for Same Store (YYYY-MM-DD)
    
    Returns:
        str: Complete SQL query
    """
    
    # Build source category filter
    escaped_source_cats = [c.replace("'", "''") for c in source_categories]
    source_cat_list = ", ".join([f"'{c}'" for c in escaped_source_cats])
    source_cat_filter = f"pm.CategoryName IN ({source_cat_list})"
    
    # Build source subcategory filter (optional)
    if source_subcategories and len(source_subcategories) > 0:
        escaped_source_subcats = [s.replace("'", "''") for s in source_subcategories]
        source_subcat_list = ", ".join([f"'{s}'" for s in escaped_source_subcats])
        source_subcat_filter = f"AND pm.SubCategoryName IN ({source_subcat_list})"
    else:
        source_subcat_filter = ""
    
    # Build target category filter - MUST include source categories to capture Stayed customers
    # In target_period, we look at BOTH source and target categories
    all_target_cats = list(source_categories)  # Start with source categories (for Stayed)
    if target_categories and len(target_categories) > 0:
        for cat in target_categories:
            if cat not in all_target_cats:
                all_target_cats.append(cat)
    
    escaped_all_cats = [c.replace("'", "''") for c in all_target_cats]
    all_cat_list = ", ".join([f"'{c}'" for c in escaped_all_cats])
    target_cat_filter = f"pm.CategoryName IN ({all_cat_list})"
    
    # Keep track of which are specifically target categories (for switched detection)
    if target_categories and len(target_categories) > 0:
        escaped_target_only = [c.replace("'", "''") for c in target_categories]
        target_only_list = ", ".join([f"'{c}'" for c in escaped_target_only])
    else:
        # If no target specified, everything except source is "switched"
        target_only_list = ""
    
    # Build target subcategory filter - include BOTH source and target subcategories
    # Source subcats needed to detect "Stayed", target subcats to detect "Switched"
    all_target_subcats = []
    if source_subcategories and len(source_subcategories) > 0:
        all_target_subcats.extend(source_subcategories)
    if target_subcategories and len(target_subcategories) > 0:
        for subcat in target_subcategories:
            if subcat not in all_target_subcats:
                all_target_subcats.append(subcat)
    
    if all_target_subcats and len(all_target_subcats) > 0:
        escaped_all_subcats = [s.replace("'", "''") for s in all_target_subcats]
        all_subcat_list = ", ".join([f"'{s}'" for s in escaped_all_subcats])
        target_subcat_filter = f"AND pm.SubCategoryName IN ({all_subcat_list})"
    else:
        target_subcat_filter = ""
    
    # Keep source subcats list for Stayed detection
    if source_subcategories and len(source_subcategories) > 0:
        escaped_source_subcats_for_stayed = [s.replace("'", "''") for s in source_subcategories]
        source_subcat_list_for_stayed = ", ".join([f"'{s}'" for s in escaped_source_subcats_for_stayed])
    else:
        source_subcat_list_for_stayed = ""
    
    # Keep target subcats list for Switched detection
    if target_subcategories and len(target_subcategories) > 0:
        escaped_target_subcats_for_switched = [s.replace("'", "''") for s in target_subcategories]
        target_subcat_list_for_switched = ", ".join([f"'{s}'" for s in escaped_target_subcats_for_switched])
    else:
        target_subcat_list_for_switched = ""
    
    # Build store opening date filter
    if store_filter_type == "Same Store" and store_opening_cutoff:
        store_filter = f"AND br.openingdate <= '{store_opening_cutoff}'"
    else:
        store_filter = ""
    
    query = f"""
DECLARE period1_start_date DATE DEFAULT '{period1_start}';
DECLARE period1_end_date   DATE DEFAULT '{period1_end}';
DECLARE period2_start_date DATE DEFAULT '{period2_start}';
DECLARE period2_end_date   DATE DEFAULT '{period2_end}';
DECLARE PRIMARY_THRESHOLD FLOAT64 DEFAULT {primary_threshold};

-- Step 1: Get all transactions for source categories in First Period
WITH source_period AS (
  SELECT
    a.CustomerCode,
    pm.CategoryName,
    pm.SubCategoryName,
    pm.Brand,
    SUM(COALESCE(a.TotalSales, 0)) AS sales
  FROM `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_SALES}` a
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_PRODUCT_MASTER}` pm
    ON a.Barcode = pm.Barcode
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_BRANCH}` br
    ON a.BranchCode = br.BranchCode
  WHERE a.Date BETWEEN period1_start_date AND period1_end_date
    AND {source_cat_filter}
    {source_subcat_filter}
    {store_filter}
    AND a.CustomerCode != '0'
  GROUP BY 1, 2, 3, 4
),

-- Calculate share per customer in source period
source_with_share AS (
  SELECT
    CustomerCode,
    CategoryName,
    SubCategoryName,
    Brand,
    sales,
    SAFE_DIVIDE(sales, SUM(sales) OVER(PARTITION BY CustomerCode)) AS share
  FROM source_period
),

-- Identify primary category-subcat per customer in First Period
source_primary AS (
  SELECT
    CustomerCode,
    CategoryName AS source_cat,
    SubCategoryName AS source_subcat,
    Brand AS source_brand,
    sales,
    share
  FROM source_with_share
  QUALIFY ROW_NUMBER() OVER(
    PARTITION BY CustomerCode
    ORDER BY 
      CASE WHEN share >= PRIMARY_THRESHOLD THEN 1 ELSE 0 END DESC,
      sales DESC
  ) = 1
),

-- Get list of source customers (who bought from source categories in First Period)
source_customers AS (
  SELECT DISTINCT CustomerCode
  FROM source_primary
),

-- Step 2: Get all transactions for target categories in After Period (only for source customers)
target_period AS (
  SELECT
    a.CustomerCode,
    pm.CategoryName,
    pm.SubCategoryName,
    pm.Brand,
    SUM(COALESCE(a.TotalSales, 0)) AS sales
  FROM `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_SALES}` a
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_PRODUCT_MASTER}` pm
    ON a.Barcode = pm.Barcode
  JOIN `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE_BRANCH}` br
    ON a.BranchCode = br.BranchCode
  WHERE a.Date BETWEEN period2_start_date AND period2_end_date
    AND {target_cat_filter}
    {target_subcat_filter}
    {store_filter}
    AND a.CustomerCode IN (SELECT CustomerCode FROM source_customers)
    AND a.CustomerCode != '0'
  GROUP BY 1, 2, 3, 4
),

-- Calculate share per customer in target period
target_with_share AS (
  SELECT
    CustomerCode,
    CategoryName,
    SubCategoryName,
    Brand,
    sales,
    SAFE_DIVIDE(sales, SUM(sales) OVER(PARTITION BY CustomerCode)) AS share
  FROM target_period
),

-- Identify primary category-subcat-brand per customer in After Period
target_primary AS (
  SELECT
    CustomerCode,
    CategoryName AS target_cat,
    SubCategoryName AS target_subcat,
    Brand AS target_brand,
    sales,
    share
  FROM target_with_share
  QUALIFY ROW_NUMBER() OVER(
    PARTITION BY CustomerCode
    ORDER BY 
      CASE WHEN share >= PRIMARY_THRESHOLD THEN 1 ELSE 0 END DESC,
      sales DESC
  ) = 1
),

-- Step 3: Join source and target to create customer flow
customer_flow AS (
  SELECT
    s.CustomerCode,
    s.source_cat,
    s.source_subcat,
    s.source_brand,
    COALESCE(t.target_cat, 'GONE') AS target_cat,
    COALESCE(t.target_subcat, '') AS target_subcat,
    COALESCE(t.target_brand, '') AS target_brand,
    CASE
      WHEN t.CustomerCode IS NULL THEN 'gone'
      WHEN s.source_subcat = t.target_subcat THEN 'stayed'
      ELSE 'switched'
    END AS move_type
  FROM source_primary s
  LEFT JOIN target_primary t ON s.CustomerCode = t.CustomerCode
),

-- Step 4: Aggregate results
flow_summary AS (
  SELECT
    source_cat,
    source_subcat,
    target_cat,
    target_subcat,
    target_brand,
    move_type,
    COUNT(DISTINCT CustomerCode) AS customers
  FROM customer_flow
  GROUP BY 1, 2, 3, 4, 5, 6
)

SELECT 
  source_cat,
  source_subcat,
  CONCAT(source_cat, CASE WHEN source_subcat IS NOT NULL AND source_subcat != '' THEN CONCAT('-', source_subcat) ELSE '' END) AS source_label,
  target_cat,
  target_subcat,
  target_brand,
  CASE 
    WHEN move_type = 'stayed' THEN CONCAT('STAYED (', source_cat, CASE WHEN source_subcat IS NOT NULL AND source_subcat != '' THEN CONCAT('-', source_subcat) ELSE '' END, ')')
    WHEN move_type = 'gone' THEN 'GONE'
    ELSE CONCAT(target_cat, CASE WHEN target_subcat IS NOT NULL AND target_subcat != '' THEN CONCAT('-', target_subcat) ELSE '' END)
  END AS target_label,
  move_type,
  customers
FROM flow_summary
ORDER BY source_cat, source_subcat, move_type, customers DESC;
"""
    
    return query

