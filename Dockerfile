# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
# If you have external libraries beyond PIL, list them here
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Command to run the application
# Use the -u flag for unbuffered output with Python in containers
# This ensures logs appear immediately
CMD ["python", "-u", "main.py"]