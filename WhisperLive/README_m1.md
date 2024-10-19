## M1 macbook docker build

```bash
cd audio-macro-creator/WhisperLive
```

Make sure the script is executable
```bash
chmod +x run_m1.sh
```

Run the script
```bash
./run_m1.sh
```

This setup will:

Download the model to a local models directory if it doesn't exist.
Build the Docker image, including the downloaded model.
Run the Docker container, mounting the local model directory.

The models directory will be ignored by git due to the .gitignore file.
For the GPU version, you can make similar changes, just replacing Systran/faster-whisper-small with Systran/faster-whisper-large-v3 in the Dockerfile and run script.

## Install requirements for the client

```bash
conda create -n macro_client python=3.10
conda activate macro_client
cd requirements
pip install -r client.txt
cd ..
```

With this environment active the client can now be run. Be sure that the server (above) is running. 
```bash
python run_microphone_client.py
```