#!/usr/bin/env bash

export EDGAR_USER_AGENT="${EDGAR_USER_AGENT:-edgar-db $USER@localhost}"

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/show.sh TICKER [OPTIONS]"
    echo ""
    echo "Show financial statements for a company."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/show.sh AAPL                              # All statements (annual)"
    echo "  ./db/scripts/show.sh AAPL -s income                    # Income statement only"
    echo "  ./db/scripts/show.sh AAPL -s balance                   # Balance sheet only"
    echo "  ./db/scripts/show.sh AAPL -s cashflow                  # Cash flow statement only"
    echo "  ./db/scripts/show.sh AAPL -p quarterly                 # Quarterly data"
    echo "  ./db/scripts/show.sh AAPL -s income --format csv       # CSV output"
    exit 1
fi

python3 -m edgar_db show "$@"
