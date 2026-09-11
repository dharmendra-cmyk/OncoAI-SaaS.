# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for optimal caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application source code into container
COPY . .

# Expose port for Render web service
EXPOSE 10000

# Start Streamlit application
CMD ["streamlit", "run", "victoria_rose_app.py", "--server.port=10000", "--server.address=0.0.0.0"]
