from flask import Flask, render_template, request, jsonify
import re
from calculus import generate_random_function, plot_function, calculate_derivative
from sympy import symbols, sympify, lambdify, diff
import os
from dotenv import load_dotenv
from datetime import datetime
from neuroassist.assistant import CompanyAssistant
import requests
from models import get_response, clean_response



app = Flask(__name__)


# Загрузка переменных окружения
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), 'instance', '.env'))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions" 

headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}


@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.2,
            "max_tokens": 512
        }

        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        answer = response.json()["choices"][0]["message"]["content"]
        return jsonify({
            "question": question,
            "answer": answer
        })

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({
            "question": question,
            "answer": "Произошла ошибка при обращении к нейроассистенту."
        }), 500

# ----------------------------------------------------------------------

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
    question = data.get("question", "").strip()
    
    # Проверка на пустой вопрос
    if not question:
        return jsonify({"answer": "Пожалуйста, введите вопрос."})
    
    # Получение ответа от нейроассистента
    try:
        answer = assistant.find_answer(question)
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
        # host = 'localhost',
        host='0.0.0.0',
        port = 5005,
        debug = True
    )
