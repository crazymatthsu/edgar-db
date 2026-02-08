#!/usr/bin/env bash

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/secmaster_db_download.sh [OPTIONS]"
    echo ""
    echo "Download security reference data."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/secmaster_db_download.sh -t AAPL                # Single ticker"
    echo "  ./db/scripts/secmaster_db_download.sh -t AAPL -t MSFT        # Multiple tickers"
    echo "  ./db/scripts/secmaster_db_download.sh --sp500                 # All S&P 500 companies"
    echo "  ./db/scripts/secmaster_db_download.sh -t AAPL --force         # Force re-download"
    echo "  ./db/scripts/secmaster_db_download.sh -t AAPL --no-figi       # Skip OpenFIGI lookup"
    exit 1
fi

python3 -m secmaster_db download "$@"
