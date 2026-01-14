#!/usr/bin/env bash
set -euo pipefail

# Install Python requirements (best-effort)
if [ -f "scrapper/requirements.txt" ]; then
  python3 -m pip install --user -r scrapper/requirements.txt || true
fi

# Run the scraper to populate webshop/data and scrapped_data
python3 scrapper/app.py

# Prepare the data for the webshop
python3 scrapper/prepare.py

# Serve the webshop directory
exec python3 -m http.server 8000 --directory webshop
