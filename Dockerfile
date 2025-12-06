# Dockerfile at project root
FROM mybase

# 1. Workdir inside container
WORKDIR /app-docker

# 2. Copy and install dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your project
COPY . .

# 4. Flask config
ENV FLASK_APP=application
ENV FLASK_ENV=production

# 5. Expose port 5000
EXPOSE 5000

# 6. Run Flask app 
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
