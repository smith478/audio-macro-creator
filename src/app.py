import asyncio
from RealtimeSTT import AudioToTextRecorder
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from macro_processor import process_transcription, MACROS

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize AudioToTextRecorder
recorder = AudioToTextRecorder(
    model="large-v2",  # or whichever model you prefer
    language="en",
    spinner=False,
    verbose=False
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        recorder.start()
        while True:
            # Check for new transcriptions
            if recorder.text:
                processed_text = process_transcription(recorder.text, MACROS)
                await websocket.send_json({"text": processed_text})
                recorder.clear()  # Clear the transcription buffer
            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting
    finally:
        recorder.stop()
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)