#!/usr/bin/env bash
# Download index components into the security master database.
#
# Usage:
#   ./secmaster_db_download_index.sh SPX        # Download S&P 500 components
#   ./secmaster_db_download_index.sh DJI        # Download Dow Jones 30 components
#   ./secmaster_db_download_index.sh NDX        # Download Nasdaq-100 components
#   ./secmaster_db_download_index.sh --all      # Download all supported indexes

set -euo pipefail
python3 -m secmaster_db download-index "$@"
