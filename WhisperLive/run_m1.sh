#!/bin/bash

MODEL_NAME="Systran/faster-whisper-small"
MODEL_DIR="./models"
MODEL_PATH="$MODEL_DIR/$(basename $MODEL_NAME)"
MODEL_BIN="$MODEL_PATH/model.bin"

# Create the model directory if it doesn't exist
mkdir -p $MODEL_DIR

# Download the model if the directory doesn't exist or model.bin is missing
if [ ! -d "$MODEL_PATH" ] || [ ! -f "$MODEL_BIN" ]; then
    echo "Model directory or model.bin not found. Downloading model..."
    python download_model.py $MODEL_NAME $MODEL_PATH
fi

# Verify the model files exist
if [ ! -f "$MODEL_BIN" ]; then
    echo "Error: model.bin not found in $MODEL_PATH"
    echo "The download may have failed. Please check your internet connection and try again."
    exit 1
fi

echo "Model found at $MODEL_BIN"

# Build the Docker image
docker build -f docker/Dockerfile.m1 -t whisperlive-m1 --build-arg MODEL_NAME=$MODEL_NAME .

# Run the Docker container
docker run -it -p 9090:9090 -v $PWD/$MODEL_DIR:/app/model whisperlive-m1 \
    python run_server.py --faster_whisper_custom_model_path /app/model/$(basename $MODEL_NAME)