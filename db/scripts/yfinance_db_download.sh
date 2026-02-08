#!/usr/bin/env bash

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/yfinance_db_download.sh [OPTIONS]"
    echo ""
    echo "Download market data from Yahoo Finance."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/yfinance_db_download.sh -t AAPL                # Single ticker"
    echo "  ./db/scripts/yfinance_db_download.sh -t AAPL -t MSFT        # Multiple tickers"
    echo "  ./db/scripts/yfinance_db_download.sh --sp500                 # All S&P 500 companies"
    echo "  ./db/scripts/yfinance_db_download.sh -t AAPL --force         # Force re-download"
    echo "  ./db/scripts/yfinance_db_download.sh -t AAPL -p 10y          # 10 years of history"
    exit 1
fi

python3 -m yfinance_db download "$@"
