# app/__init__.py

from flask import Flask
from .assistant import ask_teacher  # Убедись, что assistant.py работает

def create_app():
    """
    Фабричная функция для создания Flask-приложения.
    """
    app = Flask(__name__)

    # Пример маршрута — можно заменить или удалить
    @app.route('/')
    def index():
        return "Нейросотрудник-учитель русского языка. Готов к работе!"

    # API-эндпоинт для вопросов
    @app.route('/ask', methods=['POST'])
    def ask():
        from flask import request, jsonify
        data = request.get_json()
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "Пустой вопрос"}), 400
        
        try:
            answer = ask_teacher(question)
            return jsonify({"answer": answer})
        except Exception as e:
            return jsonify({"error": f"Ошибка при генерации ответа: {str(e)}"}), 500

    return app