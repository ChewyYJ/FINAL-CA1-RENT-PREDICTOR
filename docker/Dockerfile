# docker/Dockerfile  (base image)
FROM python:3.11-slim

# Update packages in the image
RUN apt-get update -y

# Needed for scikit-learn build & native libs
RUN apt-get install build-essential -y
