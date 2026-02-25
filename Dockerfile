FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for audio processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates bzip2 \
    &&apt-get install libsndfile1 \
    && apt-get install ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY pretrained_models /app/pretrained_models

