from whisper_live.client import TranscriptionClient

def print_callback(text):
    print(f"Transcription: {text}")

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

print("Starting transcription from microphone. Speak into your microphone.")
print("Press Ctrl+C to stop.")

try:
    client()
except KeyboardInterrupt:
    print("\nTranscription stopped.")