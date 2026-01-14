## Builder stage: install Python deps and run scraper
FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps (only in builder)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY scrapper/requirements.txt /app/scrapper/requirements.txt
RUN if [ -f "/app/scrapper/requirements.txt" ]; then pip install --no-cache-dir -r /app/scrapper/requirements.txt || true; fi

# Copy project and run scraper + prepare to generate static files
COPY . /app
RUN python3 scrapper/app.py && python3 scrapper/prepare.py

## Final stage: lightweight nginx image that serves generated `webshop`
FROM nginx:stable-alpine

# Remove default html and copy generated webshop from builder
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/webshop /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
