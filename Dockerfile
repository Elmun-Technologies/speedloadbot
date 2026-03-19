FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg for yt-dlp to process media
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set python path to allow imports from root
ENV PYTHONPATH=/app
