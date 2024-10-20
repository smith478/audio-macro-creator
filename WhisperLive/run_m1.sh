#!/bin/bash

MODEL_NAME="Systran/faster-whisper-small"
MODEL_DIR="./models"

# Create the model directory if it doesn't exist
mkdir -p $MODEL_DIR

# Download the model if it doesn't exist
if [ ! -d "$MODEL_DIR/$(basename $MODEL_NAME)" ]; then
    python download_model.py $MODEL_NAME $MODEL_DIR/$(basename $MODEL_NAME)
fi

# Verify the model files exist
if [ ! -f "$MODEL_DIR/$(basename $MODEL_NAME)/model.bin" ]; then
    echo "Error: model.bin not found in $MODEL_DIR/$(basename $MODEL_NAME)"
    exit 1
fi

# Build the Docker image
docker build -f docker/Dockerfile.m1 -t whisperlive-m1 --build-arg MODEL_NAME=$MODEL_NAME .

# Run the Docker container
docker run -it -p 9090:9090 -v $PWD/$MODEL_DIR:/app/model whisperlive-m1 \
    --faster_whisper_custom_model_path /app/model/$(basename $MODEL_NAME)