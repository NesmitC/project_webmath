# build_rag_index.py

import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path

# Путь к базе знаний
DATA_PATH = "data/rus/ege.txt"
OUTPUT_DIR = Path("rag")
MODEL_NAME = "distiluse-base-multilingual-cased-v2"

# Создаем папку, если не существует
OUTPUT_DIR.mkdir(exist_ok=True)

# Загрузка текста из файла
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

# Разбиваем на абзацы
paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

# Инициализация модели и кодирование
print("[INFO] Загрузка модели...")
model = SentenceTransformer(MODEL_NAME)
print(f"[INFO] Кодирование {len(paragraphs)} абзацев...")
embeddings = model.encode(paragraphs, show_progress_bar=True, convert_to_tensor=False)

# Сохраняем абзацы
np.save(OUTPUT_DIR / "paragraphs.npy", paragraphs)

# Сохраняем эмбеддинги
np.save(OUTPUT_DIR / "embeddings.npy", embeddings)

# Построение и сохранение FAISS индекса
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))
faiss.write_index(index, str(OUTPUT_DIR / "knowledge.index"))

print(f"[INFO] Индекс и данные успешно сохранены в папке: {OUTPUT_DIR}/")