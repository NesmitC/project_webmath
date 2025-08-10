# app/routes.py

from flask import Blueprint, render_template, jsonify, request
from .assistant import ask_teacher
from .neuro_method import ask_methodist  # ✅ Импорт методиста

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"answer": "Пожалуйста, задайте вопрос."})

    # Сначала проверяем, не методический ли вопрос
    methodist_response = ask_methodist(question)
    if methodist_response:
        return jsonify({
            "answer": f"Методист: {methodist_response}"
        })

    # Если не методический — отвечает учитель
    teacher_response = ask_teacher(question)
    return jsonify({
        "answer": f"Учитель: {teacher_response}"
    })