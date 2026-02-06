# edgar-db

Download SEC EDGAR financial data (income statement, balance sheet, cash flow) into a local SQLite database. Query it from Python as pandas DataFrames or via the command line.

**Data source**: [SEC EDGAR](https://www.sec.gov/edgar) REST APIs (free, no API key, 10 req/sec rate limit)

## Installation

```bash
pip install -e .
```

### Requirements

- Python 3.10+
- Set the `EDGAR_USER_AGENT` environment variable (required by SEC):

```bash
export EDGAR_USER_AGENT="YourAppName your@email.com"
```

## Quick Start

### 1. Download data

```bash
# Single company
python3 -m edgar_db download --ticker AAPL

# Multiple companies
python3 -m edgar_db download --ticker AAPL MSFT GOOGL

# All S&P 500
python3 -m edgar_db download --sp500

# Force re-download (skips if downloaded within 24h)
python3 -m edgar_db download --ticker AAPL --force
```

### 2. View data from the command line

```bash
python3 -m edgar_db show AAPL                        # all statements
python3 -m edgar_db show AAPL --statement income      # income statement only
python3 -m edgar_db show AAPL --statement balance     # balance sheet
python3 -m edgar_db show AAPL --statement cashflow    # cash flow
python3 -m edgar_db show AAPL --period quarterly      # quarterly (10-Q)
python3 -m edgar_db show AAPL --format csv            # CSV output

python3 -m edgar_db info                              # database stats
```

If `edgar-db` is on your PATH (check `pip show edgar-db` for the install location), you can use `edgar-db` directly instead of `python3 -m edgar_db`.

## Using from Another Python Project

### Install edgar-db into your project

```bash
# From the edgar-db directory
pip install -e /path/to/edgar-db

# Or add to your requirements.txt / pyproject.toml
```

### Basic usage

```python
import edgar_db

# Connect to the database (default: ~/.edgar-db/edgar.db)
db = edgar_db.connect()

# Or specify a custom path
db = edgar_db.connect("/path/to/my-data.db")
```

### Get financial statements

Each method returns a pandas DataFrame with rows sorted by period (most recent first).

```python
# Income statement
income = db.get_income_statement("AAPL")
print(income.columns.tolist())
# ['fiscal_year', 'fiscal_period', 'period_end', 'revenue', 'cost_of_revenue',
#  'gross_profit', 'operating_expenses', 'research_and_development',
#  'selling_general_admin', 'operating_income', 'interest_expense',
#  'income_before_tax', 'income_tax', 'net_income', 'eps_basic',
#  'eps_diluted', 'shares_basic', 'shares_diluted']

# Balance sheet
balance = db.get_balance_sheet("AAPL")

# Cash flow (includes computed free_cash_flow = operating - capex)
cashflow = db.get_cash_flow("AAPL")

# Quarterly data instead of annual
income_q = db.get_income_statement("AAPL", period="quarterly")
```

### Get a single metric over time

```python
revenue = db.get_metric("AAPL", "revenue")
# Returns: fiscal_year, fiscal_period, period_end, value
```

### Compare companies

```python
df = db.compare(["AAPL", "MSFT", "GOOGL"], "net_income")
# Returns a DataFrame with period_end as index and one column per ticker
print(df)
#                      AAPL          MSFT          GOOGL
# period_end
# 2024-12-31           NaN           NaN   100118000000
# 2024-09-28  93736000000           NaN           NaN
# 2024-06-30          NaN  88136000000           NaN
```

### Example: plot revenue trends

```python
import edgar_db
import matplotlib.pyplot as plt

db = edgar_db.connect()
df = db.compare(["AAPL", "GOOGL", "MSFT"], "revenue")
df.sort_index().plot(kind="bar", figsize=(12, 6), title="Revenue Comparison")
plt.ylabel("USD")
plt.tight_layout()
plt.savefig("revenue.png")
```

### Example: screening stocks

```python
import edgar_db

db = edgar_db.connect()
for ticker in ["AAPL", "MSFT", "GOOGL", "AMZN"]:
    income = db.get_income_statement(ticker)
    if income.empty:
        continue
    latest = income.iloc[0]
    print(f"{ticker}: Revenue={latest.get('revenue', 'N/A'):.0f}, "
          f"Net Income={latest.get('net_income', 'N/A'):.0f}")
```

### Context manager

```python
with edgar_db.connect() as db:
    df = db.get_income_statement("AAPL")
    # connection closes automatically
```

## Available Metrics

| Income Statement | Balance Sheet | Cash Flow |
|---|---|---|
| revenue | total_assets | operating_cash_flow |
| cost_of_revenue | current_assets | depreciation_amortization |
| gross_profit | cash_and_equivalents | capital_expenditure |
| operating_expenses | short_term_investments | investing_cash_flow |
| research_and_development | accounts_receivable | financing_cash_flow |
| selling_general_admin | inventory | dividends_paid |
| operating_income | total_liabilities | share_repurchase |
| interest_expense | current_liabilities | stock_based_compensation |
| income_before_tax | accounts_payable | dividends_per_share |
| income_tax | long_term_debt | free_cash_flow (computed) |
| net_income | short_term_debt | |
| eps_basic | total_debt | |
| eps_diluted | stockholders_equity | |
| shares_basic | retained_earnings | |
| shares_diluted | common_stock_shares | |

## Browsing with DBeaver

The database is standard SQLite and can be opened directly in [DBeaver](https://dbeaver.io/) or any SQLite-compatible tool.

1. **File** → **New Database Connection** → select **SQLite**
2. Browse to `~/.edgar-db/edgar.db`
3. Click **Finish**

### Tables

| Table | Description |
|---|---|
| `companies` | Company info (cik, name, ticker, last_downloaded) |
| `ticker_map` | Ticker → CIK lookup |
| `facts` | All financial data (one row per XBRL fact) |
| `metadata` | Schema version |

### Example queries

```sql
-- All Google annual revenue
SELECT fiscal_year, value
FROM facts
WHERE canonical_name = 'revenue' AND form = '10-K'
  AND cik = (SELECT cik FROM ticker_map WHERE ticker = 'GOOGL')
ORDER BY fiscal_year DESC;

-- Latest income statement metrics for a company
SELECT canonical_name, value, period_end
FROM facts
WHERE statement = 'income' AND form = '10-K'
  AND cik = (SELECT cik FROM ticker_map WHERE ticker = 'GOOGL')
  AND period_end = (
    SELECT MAX(period_end) FROM facts
    WHERE cik = (SELECT cik FROM ticker_map WHERE ticker = 'GOOGL')
      AND form = '10-K'
  );

-- List all companies in the database
SELECT * FROM companies;
```

## Storage

Data is stored in a single SQLite file at `~/.edgar-db/edgar.db` by default. Override with:

```bash
export EDGAR_DB_PATH="/custom/path/data.db"
```

## Development

```bash
pip install -e ".[dev]"
pytest db/tests/
```
