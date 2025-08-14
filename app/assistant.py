# app/assistant.py

import os
import re
import requests
import time
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

# --- Настройки ---
HF_CACHE_DIR = os.path.join("models", "embeddings")
os.makedirs(HF_CACHE_DIR, exist_ok=True)

_VECTOR_STORE_PATH = "faiss_index_webmath"
CSV_URL = "https://docs.google.com/spreadsheets/d/1dQxvFLhajJOvdCM2rdqTMeJhy49cOVBQKfRH_3i0IRw/export?format=csv&gid=0"

# --- Глобальные переменные ---
_embeddings = None
_db = None
_retriever = None
_hard_cases = {}

# --- Загрузка сложных случаев ---
def load_hard_cases():
    global _hard_cases
    try:
        df = pd.read_csv(CSV_URL)
        print("✅ Таблица сложных случаев успешно загружена")
        for _, row in df.iterrows():
            triggers = str(row["trigger"]).lower().split("|")
            for trigger in triggers:
                trigger = trigger.strip()
                if trigger:
                    _hard_cases[trigger] = {
                        "answer": row["answer"],
                        "rule": row["rule"]
                    }
    except Exception as e:
        print(f"❌ Ошибка загрузки CSV: {e}")

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

# --- Ленивая инициализация модели и базы знаний ---
def get_retriever():
    global _retriever, _embeddings, _db

    if _retriever is not None:
        return _retriever

    print("🔄 Инициализация модели эмбеддингов и базы знаний...")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            # ✅ Используем легковесную модель с поддержкой safetensors
            _embeddings = HuggingFaceEmbeddings(
#                model_name="sentence-transformers/all-MiniLM-L6-v2",
#                model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
                model_name="./models/embeddings/sentence-transformers__all-MiniLM-L6-v2",
                cache_folder=HF_CACHE_DIR,
                encode_kwargs={
                    "device": "cpu"
                }
            )
            break
        except Exception as e:
            print(f"❌ Ошибка при загрузке модели: {e}")
            if attempt == max_retries:
                raise
            time.sleep(5)

            test_emb = _embeddings.embed_query("привет")
            print(f"✅ Локальная модель работает, размер: {len(test_emb)}")

    # --- Загрузка или создание FAISS базы ---
    if os.path.exists(_VECTOR_STORE_PATH):
        print("📂 Загрузка сохранённого FAISS-индекса...")
        _db = FAISS.load_local(
            _VECTOR_STORE_PATH,
            _embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        print("🆕 Создание нового FAISS-индекса...")
        try:
            raw_data = load_document_text('https://docs.google.com/document/d/1CcW-xOVPIPUZaiMxJsl5SmCKyebfhIYwmkz1ONH_neI/edit?usp=sharing')
        except Exception as e:
            print(f"⚠️ Не удалось загрузить документ: {e}")
            raw_data = ""

        definition = "Спряжение — это изменение глаголов по лицам и числам. В русском языке два спряжения: первое и второе."
        cleaned_data = definition + "\n\n" + raw_data

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
        texts = text_splitter.split_text(cleaned_data)
        docs = [Document(page_content=txt) for txt in texts]

        _db = FAISS.from_documents(docs, _embeddings)
        _db.save_local(_VECTOR_STORE_PATH)
        print("✅ FAISS-индекс сохранён локально.")

    _retriever = _db.as_retriever(search_kwargs={"k": 2})
    print("✅ Модель и база знаний готовы.")
    return _retriever

# --- DeepSeek API ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# if not DEEPSEEK_API_KEY:
  #  raise EnvironmentError("DEEPSEEK_API_KEY не установлена")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

def deepseek_complete(prompt: str) -> str:
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 200
    }
    try:
        response = requests.post(DEEPSEEK_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Ошибка при обращении к DeepSeek: {str(e)}"

# --- ОСНОВНАЯ ФУНКЦИЯ ---
def ask_teacher(question: str):
    question = question.strip()
    if not question:
        return "Пожалуйста, задайте вопрос."

    # 1. Проверка сложных случаев
    q_lower = question.lower()
    for trigger in _hard_cases:
        if trigger in q_lower:
            case = _hard_cases[trigger]
            answer = case["answer"]
            if case["rule"]:
                answer += f" Правило: {case['rule']}"
            return answer

    # 2. Поиск в базе знаний
    try:
        retriever = get_retriever()
        relevant_docs = retriever.get_relevant_documents(question)

        if not relevant_docs:
            return "Ваш вопрос будет передан методической службе."
        
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""
Ты — опытный учитель русского языка. Отвечай кратко, точно и только по фактам из контекста.
Обязательно кратко поясни, ПОЧЕМУ так пишется, а не иначе.

Правила:
1. Отвечай на русском языке.
2. Будь доброжелателен, на приветствия дружелюбно здоровайся, потом предлагай помощь,
не комментируй свои ответы предложениями в скобках. Будь краток.
3. Если пользователь использует неэтичные выражения, мат, твердо скажи о недопустимости такого речевого поведения,
это делает человека убогим, неполноценным.
4. Ответ — 1–2 предложения, сначала ответ, потом КРАТКОЕ правило или причина.
5. Не упоминай "раздел", "чанк", "заголовок".
6. Если вопрос с ошибкой — ответь: «Правильно: ...» и объясни почему.
7. Если вопрос неясен — попроси уточнить.
8. Если ответа нет — скажи: «Ваш вопрос будет передан методической службе.»

Контекст:
{context}

Вопрос: {question}

Ответ:
"""
        return deepseek_complete(prompt)
    except Exception as e:
        return f"Ошибка при обработке запроса: {str(e)}"

# --- Загрузка данных при старте ---
if __name__ == "__main__":
    load_hard_cases()
    print("⏳ Инициализация базы знаний при старте...")
    get_retriever()
    print("✅ Сервер готов к работе.")