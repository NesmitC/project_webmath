# app/assistant.py
import os
import re
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

# === ЗАГРУЗКА ТЕКСТА ИЗ GOOGLE DOCS ===
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

# Загружаем базу знаний
raw_data = load_document_text('https://docs.google.com/document/d/1CcW-xOVPIPUZaiMxJsl5SmCKyebfhIYwmkz1ONH_neI/edit?usp=sharing')

# === ДОБАВЛЯЕМ ЯСНОЕ ОПРЕДЕЛЕНИЕ ===
definition = """
## Что такое спряжение?
Спряжение — это изменение глаголов по лицам и числам в изъявительном наклонении. В русском языке два спряжения: первое и второе.
"""
cleaned_data = definition + "\n\n" + raw_data

# === ЗАГРУЗКА СЛОЖНЫХ СЛУЧАЕВ ИЗ GOOGLE ТАБЛИЦЫ ===
CSV_URL = "https://docs.google.com/spreadsheets/d/1dQxvFLhajJOvdCM2rdqTMeJhy49cOVBQKfRH_3i0IRw/export?format=csv&gid=0"
hard_cases = {}

try:
    df = pd.read_csv(CSV_URL)
    print("✅ Таблица сложных случаев успешно загружена")
    for _, row in df.iterrows():
        triggers = str(row["trigger"]).lower().split("|")
        for trigger in triggers:
            trigger = trigger.strip()
            if trigger:
                hard_cases[trigger] = {
                    "answer": row["answer"],
                    "rule": row["rule"]
                }
except Exception as e:
    print(f"❌ Ошибка загрузки CSV: {e}")

# === РАЗБИВКА ТЕКСТА ===
text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
texts = text_splitter.split_text(cleaned_data)
docs = [Document(page_content=txt) for txt in texts]

# === ВЕКТОРНАЯ БАЗА ===
embeddings = HuggingFaceEmbeddings(
#    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" # Очень качественная мультязычная модель, особенно на семантической близости. Хорошо понимает синонимы и перефразы на русском. Лучше работает с длинными фразами
#    model_name="intfloat/multilingual-e5-large" # лучший выбор для RAG, отлично работает с многими языками, включая русский. Обучена на парах "вопрос–документ" Поддерживает до 512 токенов. Минус: тяжёлая (немного медленнее), но в Colab с GPU — нормально
#    model_name="cointegrated/LaBSE-en-ru" # специализированная на английском и русском, Отлично работает, если в базе есть билингвальные фразы, Быстрая и точная. Хорошо понимает переводы и аналоги
#    model_name="ai-forever/sbert_large_mt_nlu_ru" # от Сбер и DeepPavlov. Обучена только на русском языке, Создана специально для NLU (понимания естественного языка). Очень хороша в классификации и семантическом поиске. Подходит для образовательных задач
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
db = FAISS.from_documents(docs, embeddings)
retriever = db.as_retriever(k=1)

# === DEEPSEEK API ===
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

def deepseek_complete(prompt: str) -> str:
    import requests
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

# === ОСНОВНАЯ ФУНКЦИЯ ОТВЕТА ===
def ask_teacher(question: str):
    question = question.strip().lower()
    if not question:
        return "Пожалуйста, задайте вопрос."

    # 1. Проверка сложных случаев
    for trigger in hard_cases:
        if trigger in question:
            case = hard_cases[trigger]
            answer = case["answer"]
            if case["rule"]:
                answer += f" Правило: {case['rule']}"
            return answer

    # 2. Поиск в базе знаний
    relevant_docs = retriever.get_relevant_documents(question)
    context = "\n".join([doc.page_content for doc in relevant_docs])

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