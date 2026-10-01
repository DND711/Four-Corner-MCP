# Four Corner MCP & REST Server for AI Websites (Claude, ChatGPT, Cursor)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY four_corner ./four_corner

# Install package in editable/local mode
RUN pip install --no-cache-dir -e .

# Pre-seed the SQLite database
RUN python -m four_corner.db.seed_data

# Expose port (Render, Railway, Fly.io provide $PORT dynamically)
ENV PORT=8000
EXPOSE 8000

# Start Starlette ASGI server supporting both Claude MCP (SSE) and ChatGPT Actions (REST)
CMD ["python", "-m", "four_corner.server", "--sse"]
