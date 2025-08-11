# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Создаём db экземпляр заранее
db = SQLAlchemy()

# Импортируем blueprint
from .routes import main

def create_app():
    # Определяем пути к папкам
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    # Настройка базы данных ДО init_app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/examenator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Регистрация blueprint
    app.register_blueprint(main)

    # Инициализация db
    db.init_app(app)

    return app

# Для удобного импорта: from app import db
__all__ = ['create_app', 'db']