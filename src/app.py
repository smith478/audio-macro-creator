import asyncio
import json
import logging
from RealtimeSTT import AudioToTextRecorder
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from macro_processor import process_text, MACROS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared variable to store the latest transcription
latest_transcription = ""

def on_transcription(text):
    global latest_transcription
    logger.info(f"Transcribed text: {text}")
    latest_transcription = text

# Initialize AudioToTextRecorder with more parameters
recorder = AudioToTextRecorder(
    model="tiny",
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    recording = False
    last_sent_transcription = ""
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                action = json.loads(data).get('action')
                logger.info(f"Received action: {action}")

                if action == 'start':
                    logger.debug("About to start recorder")
                    recorder.start()
                    logger.debug(f"Recorder started, is_recording: {recorder.is_recording}")
                    recording = True
                    await websocket.send_json({"status": "Recording started"})
                    logger.info("Recording started")
                elif action == 'stop':
                    logger.debug("About to stop recorder")
                    recorder.stop()
                    logger.debug(f"Recorder stopped, is_recording: {recorder.is_recording}")
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
                global latest_transcription
                if latest_transcription and latest_transcription != last_sent_transcription:
                    logger.info(f"New transcription available: {latest_transcription}")
                    try:
                        processed_text = process_text(latest_transcription, MACROS)
                        logger.info(f"Processed text: {processed_text}")
                        await websocket.send_json({"text": processed_text, "action": "update"})
                        last_sent_transcription = latest_transcription
                    except Exception as e:
                        logger.error(f"Error in processing text: {e}", exc_info=True)
                else:
                    logger.debug("No new transcription available")
            
            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}", exc_info=True)
    finally:
        if recording:
            recorder.stop()
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")