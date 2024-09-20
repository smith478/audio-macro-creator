import argparse
import asyncio
import json
from typing import List

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from src.asr.asr_factory import ASRFactory
from src.vad.vad_factory import VADFactory

from macro_processor import process_transcription, MACROS

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def create_pipelines(vad_type, vad_args, asr_type, asr_args):
    vad_pipeline = VADFactory.create_vad_pipeline(vad_type, **vad_args)
    asr_pipeline = ASRFactory.create_asr_pipeline(asr_type, **asr_args)
    return vad_pipeline, asr_pipeline

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_bytes()
            # Process audio data with VAD and ASR pipelines
            vad_result = vad_pipeline.process(data)
            if vad_result.is_speech:
                asr_result = asr_pipeline.transcribe(data)
                processed_text = process_transcription(asr_result.text, MACROS)
                await manager.broadcast(json.dumps({"text": processed_text}))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time ASR Macro Application")
    parser.add_argument("--vad-type", type=str, default="pyannote")
    parser.add_argument("--vad-args", type=str, default='{"auth_token": "huggingface_token"}')
    parser.add_argument("--asr-type", type=str, default="faster_whisper")
    parser.add_argument("--asr-args", type=str, default='{"model_size": "large-v3"}')
    args = parser.parse_args()

    vad_args = json.loads(args.vad_args)
    asr_args = json.loads(args.asr_args)
    vad_pipeline, asr_pipeline = create_pipelines(args.vad_type, vad_args, args.asr_type, asr_args)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)