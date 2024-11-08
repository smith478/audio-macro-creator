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

First run the container:

```bash
sudo docker run --gpus all --name audio-macro-creator -it --rm -p 8888:8888 -p 8501:8501 -p 8000:8000 --entrypoint /bin/bash -w /audio-macro-creator -v $(pwd):/audio-macro-creator audio-macro-creator:latest
```

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

Seems to be an issue with cuDNN in the docker container. We will need to fix the dockerfile. For now we can add its location to the `LD_LIBRARY_PATH` environment variable.
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64
```

Or use:
```bash
sudo docker run --gpus all --name audio-macro-creator -it --rm \
  -p 8000:8000 -p 443:443 \
  -v $(pwd):/audio-macro-creator \
  -v $(pwd)/server.key:/audio-macro-creator/server.key \
  -v $(pwd)/server.crt:/audio-macro-creator/server.crt \
  -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu \
  -v /usr/local/cuda:/usr/local/cuda \
  --entrypoint /bin/bash -w /audio-macro-creator \
  audio-macro-creator:latest
```

To run the server there are two options, one for local development and one for remote access. First `cd` into `src/` then run:
```bash
# For local development
./run_server.sh local

# For remote access
./run_server.sh remote
```

And then on the network this application can be accessed at `https://123.456.789:8000/static/index.html` (assuming the IP address is 123.456.789).

## TODO

This is currently not working and seems worse than before. Look at old scripts and try to figure out what's going on/merge them with the ones here.