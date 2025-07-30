# rag.py

import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from huggingface_hub import snapshot_download

# Скачай модель заранее
local_model_path = snapshot_download(repo_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Используй локальную копию
embeddings = HuggingFaceEmbeddings(model_name=local_model_path)


class KnowledgeSearch:
    def __init__(self, index_path=None, embeddings_path=None, paragraphs_path=None):
        current_dir = os.path.dirname(__file__)
        self.index_path = index_path or os.path.join(current_dir, "knowledge.index")
        self.embeddings_path = embeddings_path or os.path.join(current_dir, "embeddings.npy")
        self.paragraphs_path = paragraphs_path or os.path.join(current_dir, "paragraphs.npy")

        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.paragraphs = np.load(self.paragraphs_path, allow_pickle=True)
        self.index = faiss.read_index(self.index_path)

    def search(self, question, top_k=1):
        query_emb = self.model.encode([question], show_progress_bar=False, convert_to_tensor=False)
        distances, indices = self.index.search(np.array(query_emb), top_k)
        results = [self.paragraphs[i] for i in indices[0]]
        return "\n\n".join(results).strip()