# Production Dockerfile for NewsTube 24/7 Live Stream Engine on AWS EC2
FROM python:3.11-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install System Dependencies, FFmpeg, and Essential Fonts (including Devanagari Hindi support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-noto-core \
    fonts-noto-extra \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-gargi \
    fonts-indic \
    libgl1 \
    libglib2.0-0 \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . /app

# Ensure directories exist
RUN mkdir -p /app/videos /app/voice /app/logs /app/assets /app/thumbnails

# Default command to run the 24/7 continuous YouTube live stream
CMD ["python", "scripts/continuous_live_stream.py"]
