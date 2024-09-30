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

The `distil-medium.en` works well on a mac book with a little bit of latency.

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