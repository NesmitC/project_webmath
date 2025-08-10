# app/neuro_exam.py

import os
import re
import requests
import time
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Настройки ---
HF_CACHE_DIR = os.path.join("models", "embeddings")
os.makedirs(HF_CACHE_DIR, exist_ok=True)

_VECTOR_STORE_PATH = "faiss_index_webmath"
DATA_URL = "https://docs.google.com/document/d/1UnYDQtPDprgcvcJeM2j4P7KLNy-Z24kWOKX84QO74P4/edit?usp=sharing"



# --- Загрузка текста из Google Docs ---
def load_document_text(url: str) -> str:
    url = url.strip().split('/edit')[0]
    match_ = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
    if not match_:
        raise ValueError('Invalid Google Docs URL')
    doc_id = match_.group(1).strip()
    export_url = f'https://docs.google.com/document/d/{doc_id}/export?format=txt'
    response = requests.get(export_url)
    response.raise_for_status()
    return response.text
