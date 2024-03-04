from transformers import WhisperProcessor, WhisperForConditionalGeneration

model_id = 'openai/whisper-large-v3'

def main():
    processor = WhisperProcessor.from_pretrained(model_id)
    model = WhisperForConditionalGeneration.from_pretrained(model_id)
    model.config.forced_decoder_ids = None

    processor.save_pretrained(f'./processors/{model_id}')
    model.save_pretrained(f'./models/{model_id}')


if __name__ == "__main__":
    main()