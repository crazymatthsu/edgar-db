#!/usr/bin/env bash

export EDGAR_USER_AGENT="${EDGAR_USER_AGENT:-edgar-db $USER@localhost}"

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/download.sh [OPTIONS]"
    echo ""
    echo "Download company financial data from SEC EDGAR."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/download.sh -t AAPL                # Single ticker"
    echo "  ./db/scripts/download.sh -t AAPL -t MSFT        # Multiple tickers"
    echo "  ./db/scripts/download.sh --sp500                 # All S&P 500 companies"
    echo "  ./db/scripts/download.sh -t AAPL --force         # Force re-download"
    exit 1
fi

python3 -m edgar_db download "$@"
