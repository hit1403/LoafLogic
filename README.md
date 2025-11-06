# Bread Price Comparison Tool

A comprehensive web scraping and data analysis tool that compares bread prices across multiple online grocery platforms in India. The tool scrapes product data, performs intelligent price analysis, and provides an interactive dashboard for insights.

## Features

- **Multi-Platform Scraping**: Automated data collection from Blinkit, Zepto, and BigBasket Now
- **Intelligent Product Matching**: Fuzzy matching algorithm to compare similar products across platforms
- **Price Analysis**: Identifies best deals, calculates savings opportunities, and generates insights
- **Interactive Dashboard**: Streamlit-based web interface for data visualization
- **Data Management**: Structured data storage with timestamp tracking and export capabilities

## Project Structure

```
PriceComparison_og/
├── src/
│   ├── scrapers/
│   │   ├── base_scraper.py      # Abstract base class for all scrapers
│   │   ├── blinkit_scraper.py   # Blinkit platform scraper
│   │   ├── zepto_scraper.py     # Zepto platform scraper
│   │   └── bbnow_scraper.py     # BigBasket Now scraper
│   ├── data_analyser.py         # Data analysis and matching algorithms
│   └── data_manager.py          # Data storage and management utilities
├── dashboard/
│   └── app.py                   # Streamlit dashboard application
├── data/
│   ├── raw/                     # Raw scraped data (JSON files)
│   └── processed/               # Processed analysis results (CSV/Excel)
├── config.py                    # Configuration settings
├── run_scrapers.py              # Main scraping orchestrator
├── run_analysis.py              # Data analysis pipeline
└── requirements.txt             # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser (for Playwright)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PriceComparison_og
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

### Usage

#### 1. Scrape Data
Run the web scrapers to collect fresh product data:
```bash
python run_scrapers.py
```

#### 2. Analyze Data and View Dashboard
Process the scraped data and generate insights in dashboard:
```bash
python run_analysis.py
```


## Data Flow

1. **Scraping Phase**: 
   - Scrapers collect product data from each platform
   - Data saved as timestamped JSON files in `data/raw/`

2. **Processing Phase**:
   - Products matched across platforms using fuzzy string matching
   - Price analysis performed to identify best deals
   - Results exported to Excel format in `data/processed/`

3. **Visualization Phase**:
   - Interactive dashboard displays insights and comparisons
   - Charts show price distributions, platform comparisons, and savings opportunities
<!--
## Configuration

### Scraping Settings (`config.py`)

- **REQUEST_DELAY**: Random delay between requests (2-5 seconds)
- **MAX_RETRIES**: Maximum retry attempts for failed requests
- **TIMEOUT**: Page load timeout (30 seconds)
- **NUMBER_OF_PRODUCTS**: Maximum products to scrape per platform (30)
- **FUZZY_MATCH_THRESHOLD**: Similarity threshold for product matching (95%)

### Platform URLs
Configure target URLs for each platform in `PLATFORM_URLS` dictionary.

### Browser Configuration
Playwright browser settings including headless mode, viewport size, and user agent.
-->
## Key Components

### Scrapers
- **BaseScraper**: Abstract base class providing common functionality
- **Platform-specific scrapers**: Handle unique website structures and anti-bot measures
- **Async operation**: Concurrent scraping for improved performance

### Data Analysis
- **Product matching**: Fuzzy string matching to identify similar products
- **Price normalization**: Standardizes prices per 100g for fair comparison
- **Deal identification**: Flags best deals and calculates savings

### Dashboard Features
- **Price comparison tables**: Side-by-side product comparisons
- **Interactive charts**: Price distributions and platform analysis
- **Filtering options**: Filter by brand, price range, or platform
- **Export functionality**: Download analysis results

## Output Files

### Raw Data (`data/raw/`)
- `{platform}_{timestamp}.json`: Individual platform data
- `combined_bread_data_{timestamp}.json`: Merged data from all platforms

### Processed Data (`data/processed/`)
- `bread_prices_analysis_{timestamp}.csv`: Cleaned and standardized data
- `price_comparison_analysis_{timestamp}.xlsx`: Complete analysis with multiple sheets:
  - Product Comparison: Best deals and recommendations
  - All Deals Analysis: Detailed analysis of all products
  - Raw Data: Original scraped data

## Technical Details

### Dependencies
- **Playwright**: Web automation and scraping
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **Streamlit**: Web dashboard framework
- **TheFuzz**: Fuzzy string matching
- **Jupyter**: Optional notebook support

### Anti-Bot Measures
- Random delays between requests
- Realistic browser headers and viewport
- Error handling and retry logic
- Screenshot capture for debugging

### Data Quality
- Duplicate removal
- Price validation (removes free/invalid products)
- Weight standardization (minimum 100g products)
- Brand name standardization
<!--
## 🔧 Customization

### Adding New Platforms
1. Create new scraper class inheriting from `BaseScraper`
2. Implement `scrape_products()` method
3. Add platform URL to `config.py`
4. Update `run_scrapers.py` to include new scraper

### Modifying Analysis
- Adjust fuzzy matching threshold in `config.py`
- Customize product key generation in `data_analyser.py`
- Add new metrics or insights in analysis pipeline

### Dashboard Customization
- Modify CSS styling in `dashboard/app.py`
- Add new chart types or filters
- Customize layout and color schemes

## Important Notes

- **Rate Limiting**: Scrapers include delays to respect website resources
- **Legal Compliance**: Ensure scraping activities comply with platform terms of service
- **Data Freshness**: Scraped data includes timestamps for tracking freshness
- **Error Handling**: Robust error handling prevents crashes from individual platform failures

## Troubleshooting

### Common Issues
1. **Scraping Failures**: Check internet connection and platform accessibility
2. **Empty Results**: Verify platform URLs are current and accessible
3. **Analysis Errors**: Ensure scraped data exists in `data/raw/` directory
4. **Dashboard Issues**: Confirm all dependencies are installed correctly

### Debug Features
- Screenshot capture during scraping failures
- Detailed logging for all operations
- Intermediate data files for troubleshooting
-->


