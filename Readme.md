# American Indian Entrepreneurs - Company Data Scraper

A comprehensive, object-oriented web scraping tool designed to gather company information from various financial websites. This refactored version implements modern Python best practices, improved error handling, and a more maintainable architecture.

## 🚀 Features

- **Object-Oriented Design**: Clean, modular architecture with proper separation of concerns
- **Multi-Source Scraping**: Extracts data from Google Finance, CNBC, CNN Money, MarketWatch, and Yahoo Finance
- **Robust Error Handling**: Comprehensive retry logic and graceful failure handling
- **ThreadPoolExecutor**: Efficient multi-threading using Python's concurrent.futures
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Multiple Export Formats**: CSV and Excel output with customizable columns
- **Configurable Processing**: Adjustable batch sizes and worker counts
- **Data Validation**: Built-in data quality checks and validation

## 📋 Requirements

- Python 3.11+
- uv (Python package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Modern web scraping libraries (installed via uv)
- Progress tracking utilities (installed via uv)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd american_indian_entrepreneurs
   ```

2. **Install dependencies** (using uv):
   ```bash
   # Quick setup (recommended)
   python setup.py
   
   # Or manual installation
   uv sync  # Install core dependencies
   
   # Optional: Install additional dependencies
   uv sync --extra dev  # For development tools
   uv sync --extra ml   # For machine learning features
   uv sync --extra async # For async support
   uv sync --extra browser # For browser automation
   ```

3. **Verify installation**:
   ```bash
   # Test the installation
   python -c "import src.fetch_company_details; print('Installation successful!')"
   
   # Or run the test suite (from tests/ folder)
   uv run pytest
   ```

## 🎯 Usage

### Basic Usage

Run the main script to process stock data (writes a single output file):
```bash
# Default (CSV)
python src/run.py

# Excel instead of CSV
OUTPUT_FORMAT=excel python src/run.py
```

### Development Setup

For development work, you can use the provided Makefile for common tasks:

```bash
# Show all available commands
make help

# Quick setup
make setup

# Install development dependencies
make install-dev

# Run tests
make test

# Format and lint code
make check

# Clean up generated files
make clean

# Run the main script
make run
```

Or use uv commands directly:
```bash
# Install development tools
uv sync --extra dev

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Advanced Usage

```python
from src.fetch_company_details import CompanyDetailsFetcher, DataProcessor, DataExporter

# Initialize components
fetcher = CompanyDetailsFetcher(max_workers=8)
processor = DataProcessor(max_workers=8, batch_size=25)
exporter = DataExporter(output_dir="custom_output")

# Process data
df = processor.process_stock_data(limit=100)  # Process first 100 companies

# Export results
csv_file = exporter.export_to_csv(df)
excel_file = exporter.export_to_excel(df)
```

### Configuration

The system is highly configurable through class parameters:

- **max_workers**: Number of concurrent threads (default: CPU count + 4)
- **batch_size**: Companies processed per batch (default: 50)
- **output_dir**: Directory for exported files (default: "output")

## 🏗️ Architecture

### Core Components

1. **CompanyDetailsFetcher**: Main orchestrator for fetching company data
2. **HTTPClient**: Handles HTTP requests with retry logic and rate limiting
3. **BaseScraper**: Abstract base class for all scrapers
4. **DataProcessor**: Manages batch processing and DataFrame operations
5. **DataExporter**: Handles data export to various formats

### Scraper Classes

- `GoogleFinanceScraper`: Scrapes Google Finance pages
- `CNBCScraper`: Extracts data from CNBC
- `CNNScraper`: Processes CNN Money pages
- `MarketWatchScraper`: Handles MarketWatch data
- `YahooFinanceScraper`: Scrapes Yahoo Finance profiles

### Data Flow

```
Nasdaq API → DataProcessor → CompanyDetailsFetcher → Scrapers → DataExporter → Output Files
```

## 📊 Data Sources

The tool extracts company information from:

| Source | URL Pattern | Data Extracted |
|--------|-------------|----------------|
| Google Finance | `finance.google.com/quote/{ticker}` | CEO, Employees, HQ, Founded |
| CNBC | `cnbc.com/quotes/{ticker}` | CEO, Headquarters |
| CNN Money | `money.cnn.com/quote/profile/{ticker}` | CEO, HQ, Industry |
| MarketWatch | `marketwatch.com/investing/stock/{ticker}` | CEO, HQ, Industry, Employees |
| Yahoo Finance | `finance.yahoo.com/quote/{ticker}/profile` | CEO, Industry, Employees, HQ |

## 📈 Output Format

Generated files include the following columns:

| Column | Description | Source |
|--------|-------------|---------|
| Symbol | Stock ticker symbol | Nasdaq API |
| Name | Company name | Nasdaq API |
| Market Capital | Market capitalization | Nasdaq API |
| CEO | Chief Executive Officer | Scraped |
| Employees | Employee count | Scraped |
| Headquarters | Company headquarters | Scraped |
| Founded | Founding year | Scraped |
| Industry | Industry classification | Scraped |
| Source | Data source(s) | Internal |
| Source Link | URL(s) where data was found | Internal |

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Set custom output directory
export OUTPUT_DIR="custom_output"

# Optional: Set log level
export LOG_LEVEL="INFO"
```

### Performance Tuning

```python
# For high-performance systems
processor = DataProcessor(max_workers=16, batch_size=100)

# For conservative systems
processor = DataProcessor(max_workers=4, batch_size=25)
```

## 🛡️ Error Handling

The system includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Built-in delays between requests
- **Data Validation**: Checks for missing or invalid data
- **Graceful Degradation**: Continues processing even if some sources fail

## 📝 Logging

Detailed logging is provided at multiple levels:

```python
import logging

# Set log level
logging.basicConfig(level=logging.INFO)

# View detailed progress
logging.getLogger('src.fetch_company_details').setLevel(logging.DEBUG)
```

## 🧪 Testing

Run basic functionality tests:

```bash
# Test individual components
python -c "
from src.fetch_company_details import CompanyDetailsFetcher
fetcher = CompanyDetailsFetcher()
details = fetcher.fetch_company_details('AAPL')
print(f'Apple CEO: {details.ceo}')
"
```

## 🔄 Migration from Legacy Code

The refactored version maintains backward compatibility:

```python
# Old way (still works)
from src.fetch_company_details import get_from_yahoo_finance
details = get_from_yahoo_finance('AAPL', {})

# New way (recommended)
from src.fetch_company_details import CompanyDetailsFetcher
fetcher = CompanyDetailsFetcher()
details = fetcher.fetch_company_details('AAPL')
```

## 📚 Best Practices Implemented

1. **SOLID Principles**: Single responsibility, open/closed, dependency inversion
2. **DRY Principle**: No code duplication
3. **Type Hints**: Full type annotation for better IDE support
4. **Documentation**: Comprehensive docstrings and comments
5. **Error Handling**: Robust exception handling and recovery
6. **Logging**: Structured logging for debugging and monitoring
7. **Configuration**: Externalized configuration management
8. **Testing**: Unit testable architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with proper tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the logging output for error details
2. Review the configuration settings
3. Ensure all dependencies are installed
4. Create an issue with detailed error information

## 🔮 Future Enhancements

- [ ] Async/await support for improved performance
- [ ] Database integration for data persistence
- [ ] Web interface for data visualization
- [ ] API endpoints for programmatic access
- [ ] Machine learning integration for data validation
- [ ] Additional data sources and formats

## 📋 Legacy Information

### ML Model Integration (Deprecated)

The original project included ML model integration for CEO name identification. This has been deprecated in favor of direct web scraping, but the architecture supports future ML integration:

1. **Ollama API**: Fast, scalable, parallel processing
2. **Hugging Face Transformers**: High flexibility, native Python
3. **llama.cpp**: CPU/GPU optimized for performance

### Previous Findings

- VPN usage for Google apps (mixed success)
- API-based approaches recommended
- SEC EDGAR data exploration (large files, limited CEO data)
- Name matching approaches (deprecated)