FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (rarely changes)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user before copying files
RUN useradd -m appuser

# Copy only requirements and install Python dependencies (rarely changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the Portuguese spaCy model for semantic segmentation
RUN python -m spacy download pt_core_news_sm

# Copy application code and files that change frequently
COPY app /app

# Set the user to non-root for security
USER appuser

# Default: run Uvicorn server in production mode with unbuffered output for real-time logs
CMD ["python", "-u", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]