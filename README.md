# Everything-Switching Analysis

🔄 **Customer Switching Analysis Dashboard** - Analyze customer movement patterns across brands and categories using BigQuery and AI-powered insights.

## Features

- 📊 **Interactive Visualizations**: Sankey diagrams, heatmaps, waterfall charts
- 🎯 **Multiple Analysis Modes**: Product Switch, Brand Switch, Category Switch, Custom Type
- 🤖 **AI-Powered Insights**: OpenAI integration for automated analysis
- 📈 **Comprehensive Metrics**: Track stayed, switched, new, and lost customers
- 💾 **Export Capabilities**: Export análysis to Excel or CSV
- 🏷️ **Flexible Filtering**: Multi-category, subcategory, and brand selection

## Tech Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Data Source**: Google BigQuery
- **AI**: OpenAI GPT
- **Export**: OpenPyXL

## Local Setup

### Prerequisites

- Python 3.8+
- Google Cloud Project with BigQuery enabled
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/everything-switching.git
   cd everything-switching
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure secrets**
   ```bash
   mkdir .streamlit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   
   Edit `.streamlit/secrets.toml` with your:
   - BigQuery service account credentials
   - OpenAI API key
   - Cost per GB settings

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Streamlit Cloud Deployment

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/everything-switching.git
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository: `<YOUR_GITHUB_USERNAME>/everything-switching`
4. Set main file path: `app.py`
5. Click "Deploy"

### Step 3: Configure Secrets

In Streamlit Cloud dashboard:

1. Go to your app settings ⚙️
2. Click "Secrets"
3. Paste the contents from your `.streamlit/secrets.toml` file
4. Save

The app will automatically redeploy with the secrets!

## Configuration

### Analysis Modes

- **Product Switch**: Track switching at SKU level
- **Brand Switch**: Analyze brand-level movements
- **Category Switch**: Category-level analysis
- **Custom Type**: Define custom groupings via barcode mapping

### Filters

- **Category**: Select one or more categories (multiselect)
- **SubCategory**: Auto-populated based on selected categories
- **Brands**: Enter brand names (comma-separated)
- **Product Contains**: Filter by product name keywords
- **Primary Threshold**: Minimum % to classify as "primary brand"

## Project Structure

```
everything-switching/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration constants
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── secrets.toml.example   # Secrets template
├── modules/
│   ├── ai_analyzer.py         # OpenAI integration
│   ├── bigquery_client.py     # BigQuery connector
│   ├── data_processor.py      # Data calculations
│   ├── mock_data.py           # Test data generator
│   ├── query_builder.py       # SQL query builder
│   ├── utils.py               # Helper functions
│   └── visualizations.py      # Plotly charts
└── README.md
```

## Usage

### Quick Start with Mock Data

1. Check "🧪 Use Mock Data" in sidebar
2. Select Analysis Mode
3. Choose date ranges (Before/After periods)
4. Select filters (Category, SubCategory, Brands)
5. Click "🚀 Run Analysis"

### Using Real BigQuery Data

1. Uncheck "Use Mock Data"
2. Configure your BigQuery connection in secrets
3. Select filters and run analysis
4. View cost information (THB per GB processed)

### Exporting Results

Navigate to **Section 4: Summary Tables & Charts** → **Export tab**:
- 📊 Download as Excel
- 📄 Download as CSV

### AI Insights

After running analysis, scroll to bottom and click:
- **"✨ Generate Complete Analysis"** for AI-powered insights

## Cost Management

BigQuery costs are displayed automatically:
- Shows GB processed per query
- Calculates cost in THB (configurable rate)
- Set cost threshold in `secrets.toml`

## Categories & SubCategories

The app supports **37 product categories** including:
- Beauty accessories, Blades, Body scrub, Cologne, Conditioner
- Deodorant, Facial cleansing, Food supplement, Fragrance
- Hair coloring, Hair styling, Herbal products, Liquid soap
- Make-up (base, colour, eyes, lips, nails, powder)
- Masks, Medicine cabinet, Moisturizers (body & face)
- Mouthwash, Razors, Sanitary protection, Shampoo
- Suncare, Talcum powder, Toilet soap, Toothbrush, Toothpaste

Each category has multiple subcategories auto-populated on selection.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - feel free to use this project for your own analysis needs!

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation

---

**Built with ❤️ using Streamlit, BigQuery & OpenAI**
