This application is built using [WhisperLive](https://github.com/collabora/WhisperLive).

## Running locally (m1 macbook)

The easiest way to run and test WhisperLive is using docker. We first need to build the docker image using

```bash
docker build -t whisperlive-cpu:latest -f Dockerfile.cpu .
```
Next run the container using
```bash
docker run -it -p 9090:9090 whisperlive-cpu:latest
```
or
```bash
docker build --platform linux/arm64 -t whisperlive-cpu:latest -f Dockerfile.cpu .
```
and 
```bash
docker run --platform linux/arm64 -it -p 9090:9090 whisperlive-cpu:latest
```

## Running remotely from linux desktop
Use docker on linux desktop with GPU
```bash
docker run -it --gpus all -p 9090:9090 ghcr.io/collabora/whisperlive-gpu:latest
```
On your laptop, connect to the service using the provided client. First install the WhisperLive client:
```bash
pip install whisper-live
```
Use it in the following way
```python
from whisper_live.client import TranscriptionClient
client = TranscriptionClient(
  "192.168.7.97",  # Replace with your Linux desktop's IP
  9090,
  lang="en",
  translate=False,
  model="small",
  use_vad=False
)

# To transcribe from microphone:
client()
```
