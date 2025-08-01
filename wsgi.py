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

# 2. Теперь можно импортировать модули, которые используют переменные окружения
from flask import Flask, render_template, request, jsonify
from app.assistant import ask_teacher
from app import create_app
import requests


# 3. Создаём приложение
app = create_app()

# 4. Остальные импорты (если нужно)
import re
from calculus import generate_random_function, plot_function, calculate_derivative
from sympy import symbols, sympify, lambdify, diff
from datetime import datetime



def backend_factory():
    return requests.Session()


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5005,
        debug=True
    )