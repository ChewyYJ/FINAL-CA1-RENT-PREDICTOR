# Base image (same as mybase)
FROM python:3.11-slim

# Install system packages
RUN apt-get update -y && apt-get install -y build-essential

# Set working directory
WORKDIR /app-docker

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . .

# Expose Render’s required port
EXPOSE 10000

# Start the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "wsgi:app"]
