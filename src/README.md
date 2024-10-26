## Setup

Here we will build our audio macro on top of [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT/tree/master). 

1. From `src/` Clone the RealtimeSTT repository into a subdirectory: 
```bash
git clone https://github.com/KoljaB/RealtimeSTT.git external/RealtimeSTT
```
2. Install as an editable package
```bash
pip install -e external/RealtimeSTT
```

Available models can be found in the documentation for `WhisperModel` in `faster-whisper/faster_whisper/transcribe.py`. Here is the current list:

- tiny 
- tiny.en 
- base
- base.en
- small 
- small.en
- distil-small.en
- medium
- medium.en
- distil-medium.en
- large-v1
- large-v2
- large-v3
- large
- distil-large-v2
- distil-large-v3

The `distil-medium.en` works well on a mac book with a little bit of latency. Additionally, from the documentation: a path to a converted model directory, or a CTranslate2-converted Whisper model ID from the HF Hub. When a size or a model ID is configured, the converted model is downloaded from the Hugging Face Hub. One to try is: deepdml/faster-whisper-large-v3-turbo-ct2

## Running the app locally
1. Navigate to `src/` which contains `app.py`.
2. Run the FastAPI application using uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```
Or for debugging:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```
3. Open a web browser
4. Go to: `http://localhost:8000/static/index.html`

## Running the app remotely from a docker container
To run the application remotely from docker, we will need to set up HTTPS for the FastAPI application to capture audio through the local machine. 
First, we'll need to generate a self-signed SSL certificate with `generate_ssl_cert.sh` 
Next, make it executable with `chmod +x generate_ssl_cert.sh`, then run it with `./generate_ssl_cert.sh`. Follow the prompts to generate the self-signed certificate.

We also need to modify the Docker run command to copy the SSL certificate files into the container and expose port 443 (the standard HTTPS port):
```bash
sudo docker run --gpus all --name audio-macro-creator -it --rm \
  -p 8000:8000 -p 443:443 \
  -v $(pwd):/audio-macro-creator \
  -v $(pwd)/server.key:/audio-macro-creator/server.key \
  -v $(pwd)/server.crt:/audio-macro-creator/server.crt \
  --entrypoint /bin/bash -w /audio-macro-creator \
  audio-macro-creator:latest
```

In the container we also need to run the following:
```bash
apt-get update
apt-get install -y portaudio19-dev python3-dev
pip install torch==2.3.1+cu121 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
pip install uvicorn RealtimeSTT fastapi
```

Similar to above

1. Navigate to `src/` which contains `app.py`.
2. Run the FastAPI application using uvicorn:
```bash
uvicorn app_gpu:app --host 0.0.0.0 --port 8000
```
Or for debugging:
```bash
uvicorn app_gpu:app --host 0.0.0.0 --port 8000 --log-level debug
```

## TODO
- Get `app_gpu.py` working properly