#!/usr/bin/env bash

if [ $# -eq 0 ]; then
    echo "Usage: ./db/scripts/secmaster_db_search.sh [OPTIONS]"
    echo ""
    echo "Search securities by criteria."
    echo ""
    echo "Examples:"
    echo "  ./db/scripts/secmaster_db_search.sh --sector Technology"
    echo "  ./db/scripts/secmaster_db_search.sh --style-box large_cap"
    echo "  ./db/scripts/secmaster_db_search.sh --country 'United States'"
    echo "  ./db/scripts/secmaster_db_search.sh --sector Healthcare --country Canada"
    exit 1
fi

python3 -m secmaster_db search "$@"
