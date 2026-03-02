FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for audio processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates bzip2 libsndfile1 wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Download pretrained models for Spleeter
RUN mkdir -p pretrained_models/2stems \
    && wget -O 2stems.tar.gz "https://github.com/deezer/spleeter/releases/download/v1.4.0/2stems.tar.gz" \
    && tar -xzvf 2stems.tar.gz -C ./pretrained_models/2stems \
    && rm 2stems.tar.gz
    
COPY app /app/app
