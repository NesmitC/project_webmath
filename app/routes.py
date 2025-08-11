# app/routes.py

from flask import Blueprint, render_template, jsonify, request
from .assistant import ask_teacher
from .neuro_method import ask_methodist  # ✅ Импорт методиста
import os
import json


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


@main.route('/about')
def about():
    return render_template('about.html')


# Путь к файлу
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'examenator_data.json')

@main.route('/examenator')
def examenator():
    # Получаем все тесты с типами и вопросами
    examenator_data = {}
    test_types = ['incoming', 'current', 'final']

    for t in test_types:
        type_obj = TestType.query.filter_by(name=t).first()
        if type_obj and type_obj.tests:
            test = type_obj.tests[0]  # один тест на тип
            examenator_data[t] = {
                'title': test.title,
                'text': test.test_text,
                'questions': []
            }
            for q in test.questions:
                examenator_data[t]['questions'].append({
                    'id': q.question_number,
                    'type': q.question_type,
                    'question': q.question_text,
                    'options': q.options.split('|') if q.options else None,
                    'answer': q.correct_answer,
                    'info': q.info
                })

    return render_template('examenator.html', examenatorData=examenator_data, test_types=test_types)