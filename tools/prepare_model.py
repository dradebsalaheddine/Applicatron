"""Download models explicitly at setup; inference itself stays offline."""
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download
from model_backends import MODELS,FOLDERS
p=argparse.ArgumentParser();p.add_argument('model',choices=[*MODELS,'all']);args=p.parse_args()
for name in MODELS if args.model=='all' else [args.model]:
 snapshot_download(MODELS[name],local_dir=Path(__file__).parent/'models'/FOLDERS[name],ignore_patterns=['*.gguf','*.onnx','*.h5','*.msgpack','*.bin'])
