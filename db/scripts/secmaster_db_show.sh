#!/usr/bin/env bash

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/secmaster_db_show.sh TICKER"
    echo ""
    echo "Show security details for a ticker."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/secmaster_db_show.sh AAPL"
    echo "  ./db/scripts/secmaster_db_show.sh MSFT"
    exit 1
fi

python3 -m secmaster_db show "$@"
