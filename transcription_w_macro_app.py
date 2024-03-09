from datetime import datetime
from fuzzywuzzy import fuzz, process
import io
import json
import numpy as np
import pandas as pd
import scipy.io.wavfile as wavfile
from scipy.signal import resample
import soundfile as sf
import streamlit as st
from st_audiorec import st_audiorec
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import uuid
from word2number import w2n

st.set_page_config(layout='wide')

TARGET_SAMPLE_RATE = 16000
MODEL_PATH = 'openai/whisper-large-v3'

@st.cache_resource 
def load_model():
    model = WhisperForConditionalGeneration.from_pretrained(f'./models/{MODEL_PATH}')
    model.config.forced_decoder_ids = None
    return model

@st.cache_resource 
def load_processor():
    processor = WhisperProcessor.from_pretrained(MODEL_PATH)
    return processor

model = load_model()
processor = load_processor()

with open('macros.json', 'r') as f:
    MACROS = json.load(f)

def add_macros_sidebar(MACROS):
    # Add a dropdown in the sidebar that shows all the available macros
    st.sidebar.selectbox('Available Macros', list(MACROS.keys()))

    # Add text input fields in the sidebar for the user to add new macros
    new_macro_key = st.sidebar.text_input('New Macro Key')
    new_macro_value = st.sidebar.text_input('New Macro Value')

    # Write the new macro to macros.json when the user clicks a button
    if st.sidebar.button('Add New Macro'):
        if new_macro_key and new_macro_value:
            MACROS[new_macro_key] = new_macro_value
            with open('macros.json', 'w') as f:
                json.dump(MACROS, f)

def process_audio(wav_audio_data, TARGET_SAMPLE_RATE):
    input_audio_data, loaded_sample_rate = sf.read(io.BytesIO(wav_audio_data), dtype='float32', always_2d=True)
    resampling_factor = TARGET_SAMPLE_RATE / loaded_sample_rate
    resampled_audio_data = resample(input_audio_data, int(len(input_audio_data) * resampling_factor))

    with sf.SoundFile('output_audio.wav', 'w', samplerate=TARGET_SAMPLE_RATE, channels=2) as audio_file:
        audio_file.write(np.int16(resampled_audio_data))

    st.audio(wav_audio_data, format='audio/wav')

    return resampled_audio_data, loaded_sample_rate

def transcribe_audio(resampled_audio_data, TARGET_SAMPLE_RATE, model, processor):
    samples_per_chunk = int(TARGET_SAMPLE_RATE * 30)  # Use TARGET_SAMPLE_RATE instead of loaded_sample_rate
    chunks = np.array_split(resampled_audio_data, np.ceil(len(resampled_audio_data) / samples_per_chunk))

    transcriptions = []

    for chunk in chunks:
        input_features = processor(chunk.T, sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt").input_features 
        predicted_ids = model.generate(input_features)
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
        transcriptions.append(transcription[0])

    return ' '.join(transcriptions)

def insert_macro(words, i, MACROS):
    # Try different lengths of macro keys
    for length in range(4, 0, -1):
        if i + 2 + length <= len(words):
            macro_key = ' '.join(words[i+2:i+2+length])  # take the next 'length' words as the macro key
            # Filter MACROS.keys() to only include keys of the same length as macro_key
            same_length_keys = [key for key in MACROS.keys() if len(key.split()) == length]
            best_match = process.extractOne(macro_key.lower(), same_length_keys)  # Convert to lowercase for comparison

            if best_match and best_match[1] > 80:  # if the match confidence is above 80
                return MACROS.get(best_match[0]), 1 + length  # skip the next 'length' words ("macro" and macro_key)

    return words[i], 0  # Use the original word if no match found
    
def process_transcription(transcription, MACROS):
    # Define the phrases to replace and their replacements
    replace_phrases = {
        "period": ".",
        "new line": "  \n",
        "newline": "  \n",
        "slash": "/",
        "comma": ",",
        "open paren": "(",
        "closed paren": ")",
        "close paren": ")",
        "open paren.": "(",
        "closed paren.": ")",
        "close paren.": ")",
    }

    lines = transcription.split('\n')
    final_transcription = []
    skip = 0

    for line in lines:
        words = line.split()
        final_line = []

        for i in range(len(words)):
            word = words[i]  # Save the original word
            word_lower = word.lower()  # Convert the word to lowercase for comparison

            if skip > 0:
                skip -= 1
                continue

            # Fuzzy match for replace phrases
            phrase = ' '.join(words[i:i+2]).lower()  # Join the current word and the next word into a phrase
            best_match = process.extractOne(phrase, replace_phrases.keys())
            if best_match and best_match[1] > 95:  # if the match confidence is above 95
                final_line.append(replace_phrases.get(best_match[0]))
                skip = 1  # Skip the next word
                continue
            else:
                best_match = process.extractOne(word_lower, replace_phrases.keys())
                if best_match and best_match[1] > 95:  # if the match confidence is above 95
                    final_line.append(replace_phrases.get(best_match[0]))
                    continue

            # Check if the word is a number followed by "period"
            if i < len(words) - 2 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period." or words[i+1].lower() == "period,"):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1  # skip the next word ("period")
                    continue
                except ValueError:
                    pass  # not a number, continue to the next check
            elif i < len(words) - 1 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period." or words[i+1].lower() == "period,"):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1  # skip the next word ("period")
                    continue
                except ValueError:
                    pass  # not a number, continue to the next check

            # Check if the word is "insert macro"
            if i < len(words) - 2 and fuzz.ratio(word_lower, "insert") > 80 and words[i+1].lower() == "macro":
                word, skip = insert_macro(words, i, MACROS)
                final_line.append(word)
            else:
                final_line.append(word)  # Use the original word

        final_transcription.append(' '.join(final_line))

    final_transcription = '  \n'.join(final_transcription)
    final_transcription = final_transcription.replace(" .", ".")  # remove space before periods
    final_transcription = final_transcription.replace(" /", "/")  # remove space before slashes
    final_transcription = final_transcription.replace("/ ", "/")  # remove space after slashes
    final_transcription = final_transcription.replace(" ,", ",")  # remove space before slashes
    final_transcription = final_transcription.replace(".,", ".")
    final_transcription = final_transcription.replace(",.", ".")
    final_transcription = final_transcription.replace("..", ".")
    final_transcription = final_transcription.replace("( ", "(")  # remove space after "("
    final_transcription = final_transcription.replace(" )", ")")  # remove space before ")"

    return final_transcription

def update_inference_required():
    st.session_state['inference_required'] = True

def main():
    global TARGET_SAMPLE_RATE, model, processor, MACROS

    st.title('Audio Transcription with Macros')
    st.write('This app uses the OpenAI Whisper model to generate transcriptions with customizable macros.')

    if 'inference_required' not in st.session_state:
        st.session_state['inference_required'] = True
    if 'previous_audio_data' not in st.session_state:
        st.session_state['previous_audio_data'] = None
    if 'transcription' not in st.session_state:
        st.session_state['transcription'] = ''

    add_macros_sidebar(MACROS)

    current_audio_data = st_audiorec()
    if current_audio_data is not None and current_audio_data != st.session_state['previous_audio_data']:
        st.session_state['inference_required'] = True
        st.session_state['previous_audio_data'] = current_audio_data
        wav_audio_data = current_audio_data
    else:
        wav_audio_data = st.session_state['previous_audio_data']

    if wav_audio_data is not None and st.session_state['inference_required']:
        resampled_audio_data, loaded_sample_rate = process_audio(wav_audio_data, TARGET_SAMPLE_RATE)
        transcription = transcribe_audio(resampled_audio_data, TARGET_SAMPLE_RATE, model, processor)
        st.session_state['inference_required'] = False
        st.session_state['transcription'] = transcription
    st.write(f"Raw Transcription: {st.session_state['transcription']}")

    if st.session_state['transcription']:
        final_transcription = process_transcription(st.session_state['transcription'], MACROS)
        st.markdown(f"Final Transcription (with macros):\n\n{final_transcription}")

        # Add a text area for the user to edit the final transcription
        edited_transcription = st.text_area("Edit Transcription", final_transcription, height=500)

        # Add a save button
        if st.button('Save Transcription'):
            # Generate a UUID
            id = uuid.uuid4()

            # Save the transcriptions, model, and timestamp to a CSV file
            df = pd.DataFrame({
                'UUID': [str(id)],
                'Raw Transcription': [st.session_state['transcription']],
                'Final Transcription': [final_transcription],
                'User Edited Transcription': [edited_transcription],
                'Model': [MODEL_PATH],
                'Timestamp': [datetime.now()]
            })
            df.to_csv('./artifacts/transcriptions.tsv', mode='a', header=False, sep='\t')

            # Save the audio file with a filename that matches the UUID
            with open(f'./artifacts/audio/{id}.wav', 'wb') as f:
                f.write(wav_audio_data)

if __name__ == "__main__":
    main()