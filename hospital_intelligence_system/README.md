# Hospital Intelligence System

A comprehensive data processing pipeline for hospital intelligence in Karnataka, India. This system ingests raw hospital data, cleans and validates it, removes duplicates, enriches with additional information, classifies hospitals, and validates addresses using web scraping and AI-powered search.

## Features

- **Data Ingestion**: Load hospital data from Excel files
- **Data Cleaning**: Standardize phone numbers, emails, and addresses
- **Deduplication**: Identify and merge duplicate hospital records
- **Enrichment**: Add additional metadata and information
- **Classification**: Categorize hospitals by type and services
- **Address Validation**: Verify addresses using web search and text matching
- **Database Integration**: Store processed data in a database

## Installation

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hospital-intelligence-system.git
   cd hospital-intelligence-system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   TAVILY_API_KEY=your_tavily_api_key_here
   ```
   Get your API key from [Tavily](https://tavily.com/).

## Usage

### Running the Main Pipeline

The main pipeline processes hospital data through cleaning and basic validation:

```bash
python main_pipeline.py
```

This will:
- Load data from `data/raw/Karnataka-All-data.xlsx`
- Clean phone numbers and emails
- Save processed data to `data/processed/clean_hospitals.csv`

### Address Validation

To validate hospital addresses using web search:

```python
from pipeline.validation import run_validation

# Validate first 10 hospitals
run_validation(
    input_file="data/raw/Karnataka-All-data.xlsx",
    output_file="data/processed/validated_addresses.xlsx",
    limit=10
)
```

Or run directly:
```bash
python pipeline/validation.py
```

### Individual Pipeline Components

You can run individual pipeline steps:

```python
from pipeline import ingestion, cleaning, deduplication, enrichment, classification

# Load data
df = ingestion.load_hospital_data("data/raw/Karnataka-All-data.xlsx")

# Clean data
df = cleaning.clean_phone_numbers(df)
df = cleaning.clean_email(df)

# Remove duplicates
df = deduplication.remove_duplicates(df)

# Enrich data
df = enrichment.add_metadata(df)

# Classify hospitals
df = classification.classify_hospitals(df)
```

## Project Structure

```
hospital_intelligence_system/
├── main_pipeline.py              # Main pipeline entry point
├── requirements.txt              # Python dependencies
├── data/
│   ├── raw/                      # Raw input data
│   └── processed/                # Processed output data
├── database/
│   └── db.py                     # Database connection and operations
├── pipeline/
│   ├── ingestion.py              # Data loading
│   ├── cleaning.py               # Data cleaning utilities
│   ├── deduplication.py          # Duplicate detection and removal
│   ├── enrichment.py             # Data enrichment
│   ├── classification.py         # Hospital classification
│   └── validation.py             # Address validation
└── utils/
    ├── address_utils.py          # Address processing utilities
    ├── email_utils.py            # Email validation utilities
    └── phone_utils.py            # Phone number formatting
```

## Dependencies

- pandas: Data manipulation
- numpy: Numerical operations
- rapidfuzz: Fuzzy string matching
- requests: HTTP requests for web scraping
- beautifulsoup4: HTML parsing
- email-validator: Email validation
- openpyxl: Excel file handling
- python-dotenv: Environment variable loading

## Address Validation Workflow

The validation pipeline verifies hospital addresses by comparing the original dataset address against address data scraped from the web using the Tavily search API.

1. Load `TAVILY_API_KEY` from `.env`
2. Read the input Excel file
3. Query Tavily for each hospital using: `<hospital name> hospital Karnataka address`
4. Extract address candidates from search result descriptions and page text
5. Score candidates against the original address
6. Select the best candidate and compare it to the original
7. Output verification status and the found web address to a new Excel file

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please open an issue on GitHub.