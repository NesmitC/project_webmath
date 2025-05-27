# rag.py

import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class KnowledgeSearch:
    def __init__(self, file_path=None):
        # Установка пути к базе знаний
        if file_path is None:
            current_dir = os.path.dirname(__file__)
            file_path = os.path.join(current_dir, "..", "data", "rus", "ege.txt")

        self.file_path = os.path.normpath(file_path)
        logger.debug(f"[RAG] Загрузка базы знаний из: {self.file_path}")

        # Загрузка модели и данных
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.paragraphs, self.embeddings = self.load_knowledge()
        self.index = self.build_index(self.embeddings)

        logger.debug("[RAG] База знаний успешно загружена")


    def load_knowledge(self):
        """Загружает текст и создаёт эмбеддинги"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"База знаний не найдена: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Разбиваем на абзацы
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        embeddings = self.model.encode(paragraphs, convert_to_tensor=False)

        logger.debug(f"[RAG] Найдено {len(paragraphs)} абзацев")
        return paragraphs, embeddings


    def build_index(self, embeddings):
        """Создаёт FAISS индекс"""
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings))
        logger.debug(f"[RAG] Индекс FAISS построен (размер: {dimension})")
        return self.index


    def search(self, question, top_k=1):
        """Ищет ближайшие фрагменты к вопросу"""
        query_emb = self.model.encode([question], convert_to_tensor=False)
        distances, indices = self.index.search(np.array(query_emb), top_k)

        results = [self.paragraphs[i] for i in indices[0]]
        context = "\n\n".join(results).strip()

        logger.debug(f"[RAG] Лучший результат:\n{context[:200]}...")

        return context