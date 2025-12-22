"""
Test script to verify SQL query with sales columns is generated correctly
"""
import sys
sys.path.insert(0, '.')

from modules import query_builder

# Test: Generate query WITH sales columns
print("="*80)
print("TESTING: build_switching_query with include_sales=True")
print("="*80)

query = query_builder.build_switching_query(
    period1_start="2024-01-01",
    period1_end="2024-01-31",
    period2_start="2025-01-01",
    period2_end="2025-01-31",
    category="TOOTHPASTE",
    brands=None,
    subcategories=None,
    product_name_contains=None,
    product_name_not_contains=None,
    primary_threshold=0.60,
    barcode_mapping=None,
    store_filter_type="All Store",
    store_opening_cutoff=None,
    include_sales=True  # <<<--- KEY PARAMETER
)

# Check if sales columns are in query
print("\n--- Checking for sales columns in generated SQL ---")
sales_columns = ['primary_sales', 'sales_2024', 'sales_2025', 'total_sales']
for col in sales_columns:
    if col in query:
        print(f"[OK] FOUND: {col}")
    else:
        print(f"[X] MISSING: {col}")

# Print relevant portions of query
print("\n--- Classify CTE (should have sales columns) ---")
lines = query.split('\n')
for i, line in enumerate(lines):
    if 'classify AS' in line or 'sales' in line.lower() or 'COUNT(*)' in line or 'GROUP BY' in line:
        print(f"{i}: {line}")

print("\n--- Full Query (last 30 lines) ---")
for line in lines[-30:]:
    print(line)
