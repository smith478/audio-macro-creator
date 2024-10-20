import os
import argparse
from huggingface_hub import snapshot_download

def download_model(model_name, output_dir):
    print(f"Downloading model {model_name} to {output_dir}")
    snapshot_download(repo_id=model_name, local_dir=output_dir)
    print("Download complete")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a model from Hugging Face")
    parser.add_argument("model_name", type=str, help="Name of the model on Hugging Face")
    parser.add_argument("output_dir", type=str, help="Directory to save the model")
    args = parser.parse_args()

    download_model(args.model_name, args.output_dir)