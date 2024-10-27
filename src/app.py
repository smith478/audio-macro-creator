import asyncio
import json
import logging
import torch
import os
import uuid
from datetime import datetime
from RealtimeSTT import AudioToTextRecorder
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from macro_processor import process_text, MACROS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Environment configuration
IS_REMOTE = os.environ.get('DEPLOYMENT_MODE', 'local') == 'remote'
logger.info(f"Running in {'remote' if IS_REMOTE else 'local'} mode")

# Shared variables
latest_transcription = ""
recorder = None

def on_transcription(text):
    global latest_transcription
    logger.info(f"Transcribed text: {text}")
    latest_transcription = text

def initialize_recorder():
    """Initialize the recorder with appropriate model based on available hardware"""
    global recorder
    try:
        model_name = "distil-large-v3" if torch.cuda.is_available() else "deepdml/faster-whisper-large-v3-turbo-ct2"
        logger.info(f"Using model: {model_name}")

        recorder = AudioToTextRecorder(
            model=model_name,
            language="en",
            spinner=False,
            enable_realtime_transcription=True,
            on_realtime_transcription_stabilized=on_transcription,
            silero_sensitivity=0.2,
            webrtc_sensitivity=3,
            post_speech_silence_duration=0.4,
            min_length_of_recording=0.3,
            min_gap_between_recordings=0.01,
            realtime_processing_pause=0.01
        )
        return True
    except Exception as e:
        logger.error(f"Failed to initialize recorder: {e}")
        return False

def save_report(text):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_id = str(uuid.uuid4())
    filename = f"report_{timestamp}_{report_id}.json"
    with open(filename, 'w') as f:
        json.dump({"timestamp": timestamp, "id": report_id, "text": text}, f)
    return filename

def add_or_update_macro(name, text):
    MACROS[name] = text
    save_macros()

def delete_macro(name):
    if name in MACROS:
        del MACROS[name]
        save_macros()

def save_macros():
    with open('macros.json', 'w') as f:
        json.dump(MACROS, f)

# Initialize recorder
recorder_initialized = initialize_recorder()

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "remote" if IS_REMOTE else "local",
        "recorder_initialized": recorder_initialized,
        "gpu_available": torch.cuda.is_available(),
        "macros_loaded": len(MACROS) > 0
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    if not recorder_initialized:
        await websocket.send_json({"error": "Speech recognition model not initialized. Check server logs for details."})
        await websocket.close()
        return
        
    recording = False
    last_sent_transcription = ""
    
    try:
        while True:
            try:
                # Handle both text messages and binary (audio) data
                message = await asyncio.wait_for(websocket.receive(), timeout=0.5)
                
                if "text" in message:  # Control messages
                    action = json.loads(message["text"])
                    logger.info(f"Received action: {action}")

                    if action['action'] == 'start':
                        logger.debug("Starting audio processing")
                        recording = True
                        await websocket.send_json({"status": "Audio processing started"})
                        
                    elif action['action'] == 'stop':
                        logger.debug("Stopping audio processing")
                        recording = False
                        await websocket.send_json({"status": "Audio processing stopped"})
                        
                    # ... (rest of the control message handling remains the same) ...
                
                elif "bytes" in message and recording:  # Audio data
                    # Process the incoming audio data
                    audio_data = message["bytes"]
                    # Convert the bytes to the format expected by RealtimeSTT
                    # This depends on the specific format RealtimeSTT expects
                    if recorder:
                        recorder.process_audio(audio_data)
                
            except asyncio.TimeoutError:
                pass

            if recording:
                if latest_transcription and latest_transcription != last_sent_transcription:
                    logger.info(f"New transcription available: {latest_transcription}")
                    try:
                        processed_text = process_text(latest_transcription, MACROS)
                        logger.info(f"Processed text: {processed_text}")
                        await websocket.send_json({"text": processed_text, "action": "update"})
                        last_sent_transcription = latest_transcription
                    except Exception as e:
                        logger.error(f"Error in processing text: {e}", exc_info=True)
            
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}", exc_info=True)
    finally:
        if recording:
            recording = False
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=8000, 
                log_level="debug")