import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CLASSIFIER_MODEL = "llama-3.1-8b-instant"       # fast, lightweight, free
EXTRACTOR_MODEL = "openai/gpt-oss-120b"          # stronger, free on groq
SUMMARIZER_MODEL = "openai/gpt-oss-120b"         # stronger, free on groq

CHROMA_COLLECTION_NAME = "fin_docs"
CHROMA_PERSIST_DIR = "./chroma_store"
