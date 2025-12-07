FROM python:3.11-slim

RUN apt-get update -y && apt-get install -y build-essential

WORKDIR /app-docker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render uses port 10000
ENV PORT=10000
EXPOSE 10000

# Start with Gunicorn
CMD ["gunicorn","-b", "0.0.0.0:10000","-w", "1", "--timeout", "120", "application:app"]
