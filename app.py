import io
import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import resample
import soundfile as sf
import streamlit as st
from st_audiorec import st_audiorec
from transformers import WhisperProcessor, WhisperForConditionalGeneration

TARGET_SAMPLE_RATE = 16000
MODEL_PATH = 'openai/whisper-large-v3'

@st.cache_resource 
def load_model():
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH)
    model.config.forced_decoder_ids = None
    return model

@st.cache_resource 
def load_processor():
    processor = WhisperProcessor.from_pretrained(MODEL_PATH)
    return processor

model = load_model()
processor = load_processor()

MACROS = {
    "open email": "Opening email application...",
    "start meeting": "Starting the meeting...",
    # Define more macros here
}

def main():
    global TARGET_SAMPLE_RATE, model, processor, MACROS

    st.title('Audio-based Macro Creator')
    st.write('This app uses the OpenAI Whisper model to generate a macro from an audio recording.')

    wav_audio_data = st.sidebar.audiorec()

    audio_player = st.empty()
    action_text = st.empty()

    if wav_audio_data is not None:
        input_audio_data, loaded_sample_rate = sf.read(io.BytesIO(wav_audio_data), dtype='float32', always_2d=True)
        resampling_factor = TARGET_SAMPLE_RATE / loaded_sample_rate
        resampled_audio_data = resample(input_audio_data, int(len(input_audio_data) * resampling_factor))

        with sf.SoundFile('output_audio.wav', 'w', samplerate=TARGET_SAMPLE_RATE) as audio_file:
            audio_file.write(np.int16(resampled_audio_data))

        audio_player.audio(wav_audio_data, format='audio/wav')

        samples_per_chunk = int(loaded_sample_rate * 30)
        chunks = np.array_split(resampled_audio_data, np.ceil(len(resampled_audio_data) / samples_per_chunk))

        transcriptions = []

        for chunk in chunks:
            input_features = processor(chunk.T, sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt").input_features 
            predicted_ids = model.generate(input_features)
            transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            transcriptions.append(transcription[0])

        transcription = ' '.join(transcriptions)

        if transcription:
            action = MACROS.get(transcription.lower(), "No macro defined for this phrase.")
            action_text.write(action)

if __name__ == "__main__":
    st.set_page_config(layout='wide')
    main()