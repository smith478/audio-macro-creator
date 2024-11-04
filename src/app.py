import asyncio
import json
import logging
import torch
import uuid
import base64
import io
from datetime import datetime
from faster_whisper import WhisperModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import numpy as np
import soundfile as sf

from macro_processor import process_text, MACROS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Whisper model
model_name = "large-v3" if torch.cuda.is_available() else "base"
logger.info(f"Initializing Whisper model: {model_name}")
whisper = WhisperModel(model_name, device="cuda" if torch.cuda.is_available() else "cpu")
logger.info("Whisper model initialized")

def save_report(text):
    """Save transcribed text to a JSON file with timestamp and UUID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_id = str(uuid.uuid4())
    filename = f"report_{timestamp}_{report_id}.json"
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "id": report_id,
            "text": text
        }, f)
    return filename

def add_or_update_macro(name, text):
    """Add or update a macro in the MACROS dictionary and save to file."""
    MACROS[name] = text
    save_macros()

def delete_macro(name):
    """Delete a macro from the MACROS dictionary and save to file."""
    if name in MACROS:
        del MACROS[name]
        save_macros()

def save_macros():
    """Save the MACROS dictionary to a JSON file."""
    with open('macros.json', 'w') as f:
        json.dump(MACROS, f)

async def transcribe_audio(audio_data, sample_rate=16000):
    """
    Transcribe audio data using Whisper model.
    
    Args:
        audio_data (str): Base64 encoded audio data
        sample_rate (int): Sample rate of the audio
    
    Returns:
        str: Transcribed text or None if transcription fails
    """
    try:
        # Convert base64 to numpy array
        audio_bytes = base64.b64decode(audio_data)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Convert to float32 and normalize
        audio_array = audio_array.astype(np.float32) / 32768.0
        
        # Transcribe
        logger.debug("Starting transcription")
        segments, _ = whisper.transcribe(audio_array, language="en")
        
        # Combine all segments
        text = " ".join([segment.text for segment in segments])
        logger.debug(f"Transcription complete: {text}")
        
        return text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections and messages."""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                action = json.loads(data)
                logger.info(f"Received action: {action}")

                if action['action'] == 'process_audio':
                    audio_data = action['audio_data']
                    sample_rate = action.get('sample_rate', 16000)
                    text = await transcribe_audio(audio_data, sample_rate)
                    if text:
                        processed_text = process_text(text, MACROS)
                        await websocket.send_json({
                            "text": processed_text,
                            "action": "update"
                        })
                
                elif action['action'] == 'save_report':
                    filename = save_report(action['text'])
                    await websocket.send_json({
                        "status": f"Report saved as {filename}"
                    })
                
                elif action['action'] == 'add_macro':
                    add_or_update_macro(action['name'], action['text'])
                    await websocket.send_json({
                        "status": f"Macro '{action['name']}' added/updated",
                        "macros": MACROS
                    })
                
                elif action['action'] == 'delete_macro':
                    delete_macro(action['name'])
                    await websocket.send_json({
                        "status": f"Macro '{action['name']}' deleted",
                        "macros": MACROS
                    })
                
                elif action['action'] == 'get_macros':
                    await websocket.send_json({
                        "macros": MACROS
                    })

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_json({
                    "status": "Error: Invalid message format"
                })
            
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await websocket.send_json({
                    "status": "Error processing request"
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}", exc_info=True)
    finally:
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=8000, 
                ssl_keyfile="server.key", 
                ssl_certfile="server.crt", 
                log_level="debug")