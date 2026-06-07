FROM python:3.11-slim

WORKDIR /app

# Ensure Python prints directly to stdout without buffering
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Install CPU-only PyTorch to avoid downloading 3GB of GPU drivers on Render Free Tier
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
