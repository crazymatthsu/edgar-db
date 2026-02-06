#!/usr/bin/env bash

export EDGAR_USER_AGENT="${EDGAR_USER_AGENT:-edgar-db $USER@localhost}"

python3 -m edgar_db info
