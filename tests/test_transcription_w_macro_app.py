import unittest
import json
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock
from transcription_w_macro_app import add_macros_sidebar, process_audio, transcribe_audio, insert_macro, process_transcription

class TestTranscriptionApp(unittest.TestCase):
    @patch('transcription_w_macro_app.st')
    def test_add_macros_sidebar(self, mock_st):
        MACROS = {"test_macro": "test_value"}
        add_macros_sidebar(MACROS)
        mock_st.sidebar.selectbox.assert_called_once_with('Available Macros', list(MACROS.keys()))
        mock_st.sidebar.text_input.assert_any_call('New Macro Key')
        mock_st.sidebar.text_input.assert_any_call('New Macro Value')
        mock_st.sidebar.button.assert_called_once_with('Add New Macro')

    @patch('transcription_w_macro_app.sf')
    @patch('transcription_w_macro_app.io')
    @patch('transcription_w_macro_app.st')
    def test_process_audio(self, mock_st, mock_io, mock_sf):
        wav_audio_data = b"test_audio_data"
        TARGET_SAMPLE_RATE = 16000
        mock_sf.read.return_value = (np.array([1, 2, 3]), TARGET_SAMPLE_RATE)
        resampled_audio_data, loaded_sample_rate = process_audio(wav_audio_data, TARGET_SAMPLE_RATE)
        mock_sf.read.assert_called_once()
        mock_st.audio.assert_called_once_with(wav_audio_data, format='audio/wav')

    @patch('transcription_w_macro_app.np')
    @patch('transcription_w_macro_app.processor')
    @patch('transcription_w_macro_app.model')
    def test_transcribe_audio(self, mock_model, mock_processor, mock_np):
        resampled_audio_data = np.array([1, 2, 3])
        TARGET_SAMPLE_RATE = 16000
        mock_model.generate.return_value = "test_transcription"
        mock_processor.batch_decode.return_value = ["test_transcription"]
        transcription = transcribe_audio(resampled_audio_data, TARGET_SAMPLE_RATE, mock_model, mock_processor)
        self.assertEqual(transcription, "test_transcription")

    def test_insert_macro(self):
        words = ["insert", "macro", "test_macro"]
        i = 0
        MACROS = {"test_macro": "test_value"}
        word, skip = insert_macro(words, i, MACROS)
        self.assertEqual(word, "test_value")
        self.assertEqual(skip, 2)

    def test_process_transcription(self):
        transcription = "test_transcription"
        MACROS = {"test_macro": "test_value"}
        final_transcription = process_transcription(transcription, MACROS)
        self.assertIsInstance(final_transcription, str)

if __name__ == '__main__':
    unittest.main()