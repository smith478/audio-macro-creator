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

## TODO

We need a automatic speech recognition model with low latency inference. Try the following models:
- distil-whisper/distil-large-v2
- openai/whisper-large-v3
- facebook/wav2vec2-base-960h
----------------------------------------------------------------
- Add ability to create new macros (and save them)
- Load macros from json file rather than hard coded
- Add drop down for all available macros