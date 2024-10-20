import logging
from whisper_live.client import TranscriptionClient, Client
import websocket

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def print_callback(text):
    print(f"Transcription: {text}")

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")

def on_open(ws):
    logging.info("WebSocket connection opened")

client = TranscriptionClient(
    "localhost",
    9090,
    lang="en",
    translate=False,
    model="small",
    use_vad=True,
    save_output_recording=True,
    output_recording_filename="./output_recording.wav",
    callback=print_callback
)

# Override the default WebSocket handlers
client.client.client_socket.on_error = on_error
client.client.client_socket.on_close = on_close
client.client.client_socket.on_open = on_open

print("Starting transcription from microphone. Speak into your microphone.")
print("Press Ctrl+C to stop.")

try:
    client()
except KeyboardInterrupt:
    print("\nTranscription stopped.")
except Exception as e:
    logging.exception("An error occurred:")