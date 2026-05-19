FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir \
    fastapi uvicorn sqlalchemy aiomysql pydantic pydantic-settings \
    python-dotenv pyjwt bcrypt redis httpx

# Copy application code
COPY backend/ ./backend/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "backend.src.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
