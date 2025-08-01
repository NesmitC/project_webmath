# app/routes.py
from flask import Blueprint, render_template, jsonify
from .assistant import ask_teacher

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/ask', methods=['POST'])
def ask():
    from flask import request
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({"answer": "Пожалуйста, задайте вопрос."})
    try:
        answer = ask_teacher(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"Ошибка: {str(e)}"})