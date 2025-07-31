# app/assistant.py

import os
import re
import requests
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

# --- Глобальные переменные ---
_embeddings = None
_db = None
_retriever = None
_hard_cases = {}
_VECTOR_STORE_PATH = "faiss_index_webmath"

# --- Загрузка сложных случаев ---
CSV_URL = "https://docs.google.com/spreadsheets/d/1dQxvFLhajJOvdCM2rdqTMeJhy49cOVBQKfRH_3i0IRw/export?format=csv&gid=0"

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

# --- Инициализация базы знаний при первом запросе ---
def get_retriever():
    global _embeddings, _db, _retriever
    if _retriever is not None:
        return _retriever

    print("🔄 Загрузка модели эмбеддингов...")

    _embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if os.path.exists(_VECTOR_STORE_PATH):
        print("📂 Загрузка сохранённого FAISS-индекса...")
        _db = FAISS.load_local(
            _VECTOR_STORE_PATH,
            _embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        print("🆕 Создание нового FAISS-индекса...")

        # Загружаем базу знаний
        raw_data = load_document_text('https://docs.google.com/document/d/1CcW-xOVPIPUZaiMxJsl5SmCKyebfhIYwmkz1ONH_neI/edit?usp=sharing')

        # Добавляем определение
        definition = """
        ## Что такое спряжение?
        Спряжение — это изменение глаголов по лицам и числам в изъявительном наклонении. В русском языке два спряжения: первое и второе.
        """
        cleaned_data = definition + "\n\n" + raw_data

        # Разбивка
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
        texts = text_splitter.split_text(cleaned_data)
        docs = [Document(page_content=txt) for txt in texts]

        # Создание базы
        _db = FAISS.from_documents(docs, _embeddings)
        _db.save_local(_VECTOR_STORE_PATH)

    _retriever = _db.as_retriever(k=1)
    print("✅ Модель и база знаний готовы.")
    return _retriever

# --- DeepSeek API ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise EnvironmentError("DEEPSEEK_API_KEY не установлена")

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
    retriever = get_retriever()
    relevant_docs = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    prompt = f"""
Ты — нейросотрудник-учитель русского языка. Отвечай кратко, точно и только по фактам из контекста.

Правила:
1. Отвечай на русском языке.
2. Ответ — 1–2 предложения, без лишних слов.
3. Не упоминай "раздел", "чанк", "заголовок".
4. Если вопрос с ошибкой — ответь: «Правильно: ...»
5. Если вопрос неясен — попроси уточнить.
6. Если ответа нет — скажи: «Ваш вопрос будет передан методической службе.»

Контекст:
{context}

Вопрос: {question}

Ответ:
"""

    return deepseek_complete(prompt)

# --- Загрузка данных при импорте ---
load_hard_cases()