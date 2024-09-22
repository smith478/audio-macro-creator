import asyncio
import json
import logging
from RealtimeSTT import AudioToTextRecorder
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from macro_processor import process_text, MACROS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize AudioToTextRecorder
recorder = AudioToTextRecorder(
    model="tiny",
    language="en",
    spinner=False,
    # energy_threshold=1000,  # Adjust this value to change sensitivity
    # pause_threshold=0.8,    # Adjust this value to change the pause detection
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    recording = False
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                action = json.loads(data).get('action')
                logger.info(f"Received action: {action}")

                if action == 'start':
                    recorder.start()
                    recording = True
                    await websocket.send_json({"status": "Recording started"})
                    logger.info("Recording started")
                elif action == 'stop':
                    recorder.stop()
                    recording = False
                    await websocket.send_json({"status": "Recording stopped"})
                    logger.info("Recording stopped")
            except asyncio.TimeoutError:
                pass  # No message received, continue to check status

            if recording:
                # Check recorder status
                logger.debug(f"Recorder running: {recorder.is_recording}")
                if hasattr(recorder.audio, 'energy'):
                    logger.debug(f"Current energy: {recorder.audio.energy}")

                # Check for new transcriptions
                transcribed_text = recorder.text
                if transcribed_text and isinstance(transcribed_text, str):
                    logger.info(f"Transcribed text: {transcribed_text}")
                    processed_text = process_text(transcribed_text, MACROS)
                    logger.info(f"Processed text: {processed_text}")
                    await websocket.send_json({"text": processed_text})
                    recorder.clear()  # Clear the transcription buffer
                else:
                    logger.debug(f"No transcription available or invalid type: {type(transcribed_text)}")
            
            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}", exc_info=True)
    finally:
        if recording:
            recorder.stop()
        await websocket.close()
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")