"""
Configuration file for Everything-Switching Analysis
"""

# BigQuery Configuration
BIGQUERY_PROJECT = "commercial-prod-375618"
BIGQUERY_DATASET = "pcb_data_prod"
BIGQUERY_TABLE_SALES = "PCB_DATABASE_NFKDB"
BIGQUERY_TABLE_PRODUCT_MASTER = "PCB_PRODUCT_MASTER"
BIGQUERY_TABLE_BRANCH = "PCB_BRANCH_NFKDB"

# Analysis Mode Configuration
ANALYSIS_MODES = {
    "Brand Switch": {
        "label": "Brand Switch",
        "description": "Analyze switching between brands",
        "target_field": "pm.Brand"
    },
    "Product Switch": {
        "label": "Product Switch",
        "description": "Analyze switching between products",
        "target_field": "pm.ProductName"
    },
    "Custom Type": {
        "label": "Custom Type",
        "description": "Define custom product groupings",
        "target_field": "custom"  # Will be replaced by CASE WHEN
    }
}

DEFAULT_ANALYSIS_MODE = "Brand Switch"

# Default Date Ranges
DEFAULT_PERIOD_1_START = "2024-01-01"
DEFAULT_PERIOD_1_END = "2024-03-31"
DEFAULT_PERIOD_2_START = "2025-01-01"
DEFAULT_PERIOD_2_END = "2025-03-31"

# Default Primary Threshold
DEFAULT_PRIMARY_THRESHOLD = 0.60  # 60%
MIN_PRIMARY_THRESHOLD = 0.0
MAX_PRIMARY_THRESHOLD = 1.0

# OpenAI Configuration
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 2000

# UI Configuration
PAGE_TITLE = "Everything-Switching Analysis"
PAGE_ICON = "🔄"
LAYOUT = "wide"

# Color Schemes for Visualizations
BRAND_COLORS = {
    "NIVEA": "#0051BA",
    "VASELINE": "#00A0DC",
    "CITRA": "#E91E63",
    "NEW_TO_CATEGORY": "#4CAF50",
    "LOST_FROM_CATEGORY": "#9E9E9E",
    "MIXED": "#FFC107",
}

# Movement Type Colors
MOVEMENT_COLORS = {
    "stayed": "#2196F3",
    "switched": "#FF9800",
    "new_to_category": "#4CAF50",
    "lost_from_category": "#F44336",
}

# Export Configuration
EXCEL_SHEET_NAMES = {
    "summary": "Movement Summary",
    "details": "Detailed Flow",
    "raw": "Raw Data"
}

# Limits
MAX_BARCODE_MAPPINGS = 1000  # Maximum number of custom barcode mappings
MAX_BRANDS_FILTER = 50  # Maximum brands to allow in multi-select

# Branch Filter
BRANCH_OPENING_DATE_CUTOFF = "2023-12-31"  # Only branches opened before this date
