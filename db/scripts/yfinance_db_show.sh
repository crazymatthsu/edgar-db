#!/usr/bin/env bash

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/yfinance_db_show.sh TICKER [OPTIONS]"
    echo ""
    echo "Show market data for a company."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/yfinance_db_show.sh AAPL                        # All data"
    echo "  ./db/scripts/yfinance_db_show.sh AAPL --data prices           # Prices only"
    echo "  ./db/scripts/yfinance_db_show.sh AAPL --data income           # Income statement"
    echo "  ./db/scripts/yfinance_db_show.sh AAPL --data stats            # Company stats"
    echo "  ./db/scripts/yfinance_db_show.sh AAPL -p quarterly            # Quarterly data"
    echo "  ./db/scripts/yfinance_db_show.sh AAPL --format csv            # CSV output"
    exit 1
fi

python3 -m yfinance_db show "$@"
