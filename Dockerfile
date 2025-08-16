# Use an official Python base with system libs
FROM python:3.11-slim

# Install system build tools needed for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ git curl libffi-dev libssl-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Upgrade pip and install wheel first so binary wheels are preferred
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy app code
COPY . .

# Expose port (Render provides PORT env var)
ENV PORT 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]