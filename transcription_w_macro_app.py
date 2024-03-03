from fuzzywuzzy import fuzz, process
import io
import json
import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import resample
import soundfile as sf
import streamlit as st
from st_audiorec import st_audiorec
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from word2number import w2n

st.set_page_config(layout='wide')

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

with open('macros.json', 'r') as f:
    MACROS = json.load(f)

def main():
    global TARGET_SAMPLE_RATE, model, processor, MACROS

    st.title('Audio-based Macro Creator')
    st.write('This app uses the OpenAI Whisper model to generate a macro from an audio recording.')

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

    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        input_audio_data, loaded_sample_rate = sf.read(io.BytesIO(wav_audio_data), dtype='float32', always_2d=True)
        resampling_factor = TARGET_SAMPLE_RATE / loaded_sample_rate
        resampled_audio_data = resample(input_audio_data, int(len(input_audio_data) * resampling_factor))

        with sf.SoundFile('output_audio.wav', 'w', samplerate=TARGET_SAMPLE_RATE, channels=2) as audio_file:
            audio_file.write(np.int16(resampled_audio_data))

        st.audio(wav_audio_data, format='audio/wav')

        samples_per_chunk = int(TARGET_SAMPLE_RATE * 30)  # Use TARGET_SAMPLE_RATE instead of loaded_sample_rate
        chunks = np.array_split(resampled_audio_data, np.ceil(len(resampled_audio_data) / samples_per_chunk))

        transcriptions = []

        for chunk in chunks:
            input_features = processor(chunk.T, sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt").input_features 
            predicted_ids = model.generate(input_features)
            transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            transcriptions.append(transcription[0])

        transcription = ' '.join(transcriptions)
        st.write(f"Raw Transcription: {transcription}")

        if transcription:
            # Define the phrases to replace and their replacements
            replace_phrases = {
                "period": ".",
                "new line": "  \n",
                "newline": "  \n",
                "slash": "/",
                "comma": ",",
                "open paren": "(",
                "closed paren": ")"
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
                    best_match = process.extractOne(word_lower, replace_phrases.keys())
                    if best_match and best_match[1] > 80:  # if the match confidence is above 80
                        final_line.append(replace_phrases.get(best_match[0]))
                        continue

                    # Check if the word is a number followed by "period"
                    if i < len(words) - 2 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period."):
                        try:
                            number = w2n.word_to_num(word_lower.replace(",", ""))
                            final_line.append("\n" + str(number) + ".")
                            skip = 2  # skip the next two words ("period" and the number)
                            continue
                        except ValueError:
                            pass  # not a number, continue to the next check
                    elif i < len(words) - 1 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period."):
                        try:
                            number = w2n.word_to_num(word_lower.replace(",", ""))
                            final_line.append("\n" + str(number) + ".")
                            skip = 1  # skip the next word ("period")
                            continue
                        except ValueError:
                            pass  # not a number, continue to the next check

                    if i < len(words) - 2 and fuzz.ratio(word_lower, "insert") > 80 and words[i+1].lower() == "macro":
                        macro_key = words[i+2]  # take the next word as the macro key
                        best_match = process.extractOne(macro_key.lower(), MACROS.keys())  # Convert to lowercase for comparison

                        # Concatenate the next two words and check if the concatenated string matches any macro
                        concatenated_macro_key = words[i+2] + words[i+3] if i < len(words) - 3 else None
                        concatenated_best_match = process.extractOne(concatenated_macro_key.lower(), MACROS.keys()) if concatenated_macro_key else None

                        if best_match and best_match[1] > 80:  # if the match confidence is above 80
                            final_line.append(MACROS.get(best_match[0]))
                            skip = 2  # skip the next two words ("macro" and macro_key)
                        elif concatenated_best_match and concatenated_best_match[1] > 80:  # if the match confidence is above 80
                            final_line.append(MACROS.get(concatenated_best_match[0]))
                            skip = 3  # skip the next three words ("macro", word1, and word2)
                        else:
                            final_line.append(word)  # Use the original word
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
            st.markdown(f"Final Transcription (with macros):\n\n{final_transcription}")

if __name__ == "__main__":
    main()