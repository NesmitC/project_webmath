from flask import Flask, render_template, request, jsonify
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable
from typing import Any, Optional
import re
from calculus import generate_random_function, plot_function, calculate_derivative
from sympy import symbols, sympify, lambdify, diff
import os
from dotenv import load_dotenv
from datetime import datetime
from neuroassist.assistant import CompanyAssistant
import requests
from models import get_response, clean_response

from huggingface_hub import InferenceClient
from langchain_huggingface import HuggingFaceEndpoint
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


app = Flask(__name__)


# Загрузка переменных окружения
load_dotenv()
# load_dotenv(os.path.join(os.path.dirname(__file__), 'instance', '.env'))

# DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions" 
# headers = {
#     "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
#     "Content-Type": "application/json"
# }


# class DeepSeekLLM(BaseLanguageModel):
#     def _call(self, prompt: str, stop: Optional[list] = None, **kwargs: Any) -> str:
#         return get_deepseek_response(prompt)

#     @property
#     def _llm_type(self) -> str:
#         return "deepseek"


# def get_deepseek_response(question):
#     try:
#         payload = {
#             "model": "deepseek-chat",
#             "messages": [{"role": "user", "content": question}],
#             "temperature": 0.2,
#             "max_tokens": 512
#         }

#         response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
#         response.raise_for_status()

#         return response.json()["choices"][0]["message"]["content"]
#     except Exception as e:
#         print(f"DeepSeek API Error: {str(e)}")
#         return "Извините, произошла ошибка при запросе к API"


# @app.route('/ask', methods=['POST'])
# def ask():
#     data = request.get_json()
#     question = data.get('question', '')

#     if not question:
#         return jsonify({"error": "Question is required"}), 400

#     answer = get_deepseek_response(question)
#     return jsonify({"question": question, "answer": answer})

# ----------------------------------------------------------------------

# Настройки Hugging Face API
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3" 

# Путь к векторному хранилищу
VECTORSTORE_PATH = "vectorstore"

# Инициализация модели Hugging Face
repo_id = "mistralai/Mistral-7B-Instruct-v0.3"
llm = HuggingFaceEndpoint(
    repo_id=repo_id,
    max_new_tokens=512,
    temperature=0.7,
    huggingfacehub_api_token=HF_TOKEN
)

# Загрузка FAISS-индекса (если используется RAG)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever()

# Создание цепочки RAG
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        result = qa_chain.invoke({"query": question})
        answer = result.get("result", "Не удалось получить ответ.")
        source_docs = result.get("source_documents", [])
        sources = [doc.metadata for doc in source_docs]
        return jsonify({
            "question": question,
            "answer": answer,
            "sources": sources
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ----------------------------------------------------------------------


assistant = CompanyAssistant()


@app.route('/test')
def test():
    try:
        answer = assistant.find_answer("Как интегрировать x^2?")
        return f"<pre>{answer}</pre>"
    except Exception as e:
        return f"Ошибка: {str(e)}"


@app.route('/assistant', methods=['POST'])
def ask_assistant():
    print("[LOG] Получен POST-запрос")
    data = request.get_json()
    print("[LOG] Полученные данные:", data)
    answer = assistant.find_answer(data['question'])
    question = data.get("question", "")
    
    # Проверка на пустой вопрос
    if not question.strip():
        return jsonify({"answer": "Пожалуйста, введите вопрос."})
    
    # Получение ответа от нейроассистента
    try:
        answer = get_response(question)  # предполагается, что эта функция есть в models.py
    except Exception as e:
        answer = f"Произошла ошибка при обработке: {e}"

    return jsonify({"answer": answer})


# ----------------------------------------------------------------

# Загружаем .env из instance/ или корня
env_path = os.path.join(os.path.dirname(__file__), 'instance', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Попробует загрузить из корня

# ---------------- диалоговое онкно с нейроассистентом -----------------

db_ru = os.path.join('data', 'rus.txt')


def find_answer(question):
    """Простой поиск по ключевым словам в файле"""
    question = question.lower()
    try:
        with open(db_ru, 'r', encoding='utf-8') as f:
            text = f.read()

        # Пример простого поиска
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if any(word in paragraph.lower() for word in question.split()):
                return paragraph.strip()

        return "К сожалению, я не нашёл информации по вашему вопросу."
    except Exception as e:
        return f"Ошибка при чтении файла: {e}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('question', '').strip()
    answer = find_answer(user_input)
    return {"answer": answer}



@app.route('/task')
def task():
    f_expr, F_expr = generate_random_function()
    graph = plot_function(F_expr)
    return render_template('task.html', 
                         f_expr=f_expr,
                         F_expr=f"F(x) = {F_expr.replace('**', '^')} + C",
                         graph=graph)

@app.route('/check_solution', methods=['GET', 'POST'])
def check_solution():
    if request.method == 'GET':
        return jsonify({"message": "Используйте POST для проверки решения"})
    
    try:
        data = request.get_json()
        user_solution = data.get('solution', '')
        
        # В реальном приложении нужно хранить текущую задачу в сессии
        _, correct_F = generate_random_function()
        
        # Простая проверка (можно улучшить)
        is_correct = user_solution.replace(' ', '') == correct_F.replace('**', '^')
        
        return jsonify({
            "correct": is_correct,
            "expected": correct_F
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400





if __name__ == '__main__':
    app.run(
        host = 'localhost',
        port = 5005,
        debug = True
    )
