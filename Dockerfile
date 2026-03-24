# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed dependencies
RUN pip install --no-cache-dir prompt_toolkit>=3.0 rich>=13.0 httpx[http2]>=0.25 tiktoken>=0.5 urllib3<2.0

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Run freechat.py when the container launches
CMD ["python", "freechat.py"]
