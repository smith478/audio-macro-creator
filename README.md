# Audio Macro Creator

Tool to create audio to text macro. 

## Getting started

### Docker

The docker image can be built using `./Dockerfile`. You can build it using the following command, run from the root directory

```bash
docker build --build-arg WB_API_KEY=<your_api_key> . -f Dockerfile --rm -t llm-finetuning:latest
```

### Run docker container

First navigate to this repo on your local machine. Then run the container:

```bash
docker run --gpus all --name audio-macro-creator -it --rm -p 8888:8888 -p 8501:8501 -p 8000:8000 --entrypoint /bin/bash -w /audio-macro-creator -v $(pwd):/audio-macro-creator llm-finetuning:latest
```

### Run jupyter from the container
Inside the Container:
```bash
jupyter lab --ip 0.0.0.0 --no-browser --allow-root --NotebookApp.token=''
```

Host machine access this url:
```bash
localhost:8888/<YOUR TREE HERE>
```

### Run streamlit from the container
Inside the container:
```bash
streamlit run app.py
```

Host machine:
```bash
localhost:8501
```

### Create endpoint with ngrok
Once the streamlit service is up and running 
```
ngrok http https://localhost:8501
```

## TODO

We need a automatic speech recognition model with low latency inference. Try the following models:
- distil-whisper/distil-large-v2
- X openai/whisper-large-v3
- X facebook/wav2vec2-base-960h
- X srujan00123/wav2vec2-large-medical-speed
- X save model to disk 
----------------------------------------------------------------
- Look into real-time transcription
- Useful resources:
    - https://huggingface.co/learn/audio-course/chapter7/voice-assistant#speech-transcription
    - https://github.com/alesaccoia/VoiceStreamAI?tab=readme-ov-file
    - https://github.com/SYSTRAN/faster-whisper
    - https://github.com/gaborvecsei/whisper-live-transcription
----------------------------------------------------------------
- X Use session states to allow saving without needing to rerun the entire script
- If macro key phrase is longer than 4 words, just check that the first 4 words match. Or throw an error if there are any macros with more than 4 words.
- X Add notebooks to experiment with models
- Add dropdown for different model options
----------------------------------------------------------------
For transcription with macro application: 
- add fuzzywuzzy, st_audiorec, and word2number to docker image
- add dockerfile
- X add instructions for ngrok hosting
- X save the raw transcriptions along with the final (macro inserted) transcription
- X add ability to edit the final transcriptions, save the raw-final pair for training data
    - X we should save the asr model, timestamp, raw, final, id, raw audio with id

## Streamlit service

When running the streamlit service on a VM, using the microphone of the host machine you may get a "Component Error
Cannot read properties of null (reading 'getAudioTracks')". This is likely related to the browser's security settings and the fact that streamlit runs on http.

Here is how to solve the issue:

1. Open a terminal on your Ubuntu VM.
2. Run the following commands to generate a private key:
```bash
openssl genrsa 2048 > host.key
chmod 400 host.key
```
3. Run the following command to generate a self-signed certificate. You'll be prompted for some information - you can just hit Enter to accept the defaults:
```bash
openssl req -new -x509 -nodes -sha256 -days 365 -key host.key -out host.cert
```
4. Run your Streamlit app over HTTPS with the following command:
```bash
streamlit run transcription_w_macro_app.py --server.sslCertFile host.cert --server.sslKeyFile=host.key
```
Now, you should be able to access your Streamlit app over HTTPS, and your browser should allow access to the microphone. Note that because the certificate is self-signed, your browser will warn you that the connection is not secure. You'll need to manually accept the risk and proceed to the site.