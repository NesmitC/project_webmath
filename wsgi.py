# wsgi.py

# 1. СНАЧАЛА — загружаем переменные окружения
from dotenv import load_dotenv
import os

# Указываем путь к .env
dotenv_path = os.path.join(os.path.dirname(__file__), 'instance', '.env')

# Проверяем, существует ли файл
if not os.path.exists(dotenv_path):
    raise FileNotFoundError(f"Файл .env не найден по пути: {dotenv_path}")

# Загружаем переменные
load_dotenv(dotenv_path)
print(f"✅ .env успешно загружен из: {dotenv_path}")

# 2. Создаём приложение ДО импортов
from app import create_app, db
app = create_app()

# Устанавливаем secret_key из .env
app.secret_key = os.getenv('SECRET_KEY')

# 3. Создаём таблицы в контексте приложения
with app.app_context():
    db.create_all()
    print("✅ Все таблицы созданы: users, test_types, tests, questions")

# . Теперь можно импортировать модули, зависящие от app/db
from flask import render_template, request, jsonify
import requests

# Не нужно повторно настраивать SQLALCHEMY_DATABASE_URI — уже в create_app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5005,
        debug=True
    )