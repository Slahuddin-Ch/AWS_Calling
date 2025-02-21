# Use Python 3.12 base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching benefits)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /app

RUN mkdir transcripts

# Expose port 5000 for FastAPI
EXPOSE 5000

# Run Uvicorn server for FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]