import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from whisper_live.client import TranscriptionClient, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variables
transcription_client = None
latest_transcription = ""

def on_transcription(text):
    global latest_transcription
    logger.info(f"Transcribed text: {text}")
    latest_transcription = text

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    global transcription_client
    global latest_transcription
    recording = False
    last_sent_transcription = ""

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                action = json.loads(data)
                logger.info(f"Received action: {action}")

                if action['action'] == 'start':
                    if not transcription_client:
                        transcription_client = TranscriptionClient(
                            host="localhost",  # Replace with your server details
                            port=9090,
                            lang="en",
                            translate=False,
                            model="small",
                            use_vad=True,
                            output_transcription_path="./output.srt",
                            log_transcription=False,
                            callback=on_transcription
                        )
                    asyncio.create_task(start_transcription(transcription_client))
                    recording = True
                    await websocket.send_json({"status": "Recording started"})
                    logger.info("Recording started")
                elif action['action'] == 'stop':
                    if transcription_client:
                        transcription_client.client.recording = False
                    recording = False
                    await websocket.send_json({"status": "Recording stopped"})
                    logger.info("Recording stopped")

            except asyncio.TimeoutError:
                pass  # No message received, continue to check status

            if recording:
                if latest_transcription and latest_transcription != last_sent_transcription:
                    logger.info(f"New transcription available: {latest_transcription}")
                    try:
                        await websocket.send_json({"text": latest_transcription, "action": "update"})
                        last_sent_transcription = latest_transcription
                    except Exception as e:
                        logger.error(f"Error in sending transcription: {e}", exc_info=True)
                else:
                    logger.debug("No new transcription available")
            
            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}", exc_info=True)
    finally:
        if transcription_client:
            transcription_client.client.recording = False
        logger.info("WebSocket connection closed")

async def start_transcription(client):
    # Run the transcription client in a separate thread
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, client)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")