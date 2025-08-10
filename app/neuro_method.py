# app/neuro_method.py

import os
import fitz  # PyMuPDF
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Настройки ---
# Путь от корня проекта: project_webmath/data/methodist
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "methodist")
METHODIST_INDEX_PATH = "faiss_index_methodist"

# Общая модель (используем ту же, что и учителя)
EMBEDDINGS_MODEL_PATH = "./models/embeddings/sentence-transformers__all-MiniLM-L6-v2"

# --- Глобальные переменные ---
_embeddings = None
_db = None
_retriever = None

# --- Инициализация модели ---
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        print("🔄 Загрузка модели эмбеддингов для методиста...")
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDINGS_MODEL_PATH,
            encode_kwargs={"device": "cpu"}
        )
    return _embeddings

# --- Извлечение текста из PDF ---
def extract_text_from_pdfs(pdf_dir: str) -> str:
    full_text = ""
    if not os.path.exists(pdf_dir):
        print(f"❌ Папка {pdf_dir} не найдена")
        return full_text

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("⚠️ В папке pdfs/ нет PDF-файлов")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            print(f"✅ Извлечено {len(text)} символов из {pdf_file}")
            full_text += f"\n\n--- Документ: {pdf_file} ---\n\n{text}"
        except Exception as e:
            print(f"❌ Ошибка при чтении {pdf_file}: {e}")
    return full_text

# --- Инициализация базы знаний ---
def get_retriever():
    global _retriever, _db

    if _retriever is not None:
        return _retriever

    print("🔄 Инициализация нейроассистента-методиста...")

    embeddings = get_embeddings()

    if os.path.exists(METHODIST_INDEX_PATH):
        print("📂 Загрузка сохранённого индекса методиста...")
        _db = FAISS.load_local(
            METHODIST_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        print("🆕 Создание нового FAISS-индекса для методиста...")
        raw_text = extract_text_from_pdfs(PDF_DIR)

        if not raw_text.strip():
            print("⚠️ Нет текста из PDF — создана пустая база")
            raw_text = "Документы по расписанию, ФГОС, кодификаторам и допуску к экзаменам временно недоступны."

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        texts = text_splitter.split_text(raw_text)
        docs = [Document(page_content=txt) for txt in texts]

        _db = FAISS.from_documents(docs, embeddings)
        _db.save_local(METHODIST_INDEX_PATH)
        print("✅ Индекс методиста сохранён локально.")

    _retriever = _db.as_retriever(search_kwargs={"k": 2})
    print("✅ Нейроассистент-методист готов к работе.")
    return _retriever

# --- Основная функция ---
def ask_methodist(question: str) -> str:
    """
    Принимает вопрос, ищет в PDF-документах, возвращает ответ.
    Если вопрос не по теме — возвращает None, чтобы переключиться на учителя.
    """
    question = question.strip().lower()
    if not question:
        return None

    # 🔍 Ключевые слова, по которым понятно, что вопрос к методисту
    trigger_words = [
        "экзамен", "огэ", "егэ", "расписание", "допуск", "документ", "фгос", "кодификатор",
        "программа", "аттестация", "заявление", "сроки", "дата", "регламент", "проходной",
        "форма", "бланк", "инструкция", "правила поведения", "проверяющий"
    ]

    if not any(word in question for word in trigger_words):
        return None  # Не методический вопрос → передаём учителю

    try:
        retriever = get_retriever()
        relevant_docs = retriever.get_relevant_documents(question)
        if not relevant_docs:
            return "На ваш вопрос пока нет ответа в методических документах. Обратитесь к администрации."

        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # Можно использовать тот же DeepSeek, что и у учителя
        from app.assistant import deepseek_complete

        prompt = f"""
Ты — нейроассистент-методист. Отвечай кратко, точно и только по фактам из контекста.

Правила:
1. Отвечай на русском.
2. Только факты из контекста.
3. Не упоминай "чанк", "раздел".
4. Если вопрос неясен — попроси уточнить.
5. Если ответа нет — скажи: «Нет информации в документах.»

Контекст:
{context}

Вопрос: {question}

Ответ:
"""
        return deepseek_complete(prompt)

    except Exception as e:
        return f"Ошибка методиста: {str(e)}"