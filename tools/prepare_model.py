"""Run once while building, never during private email processing."""
from pathlib import Path
from sentence_transformers import SentenceTransformer
model=SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
model.save(str(Path(__file__).parent/'models'/'multilingual-minilm'))
