FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_MODULE=app.worker:app

# Expose port (if applicable, though worker is usually a consumer)
EXPOSE 8000

# Command to run the worker/API
# We'll use uvicorn for the API or just run the worker directly
CMD ["uvicorn", "app.worker:app", "--host", "0.0.0.0", "--port", "8000"]
