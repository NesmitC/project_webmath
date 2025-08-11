# app/__init__.py
from flask import Flask
import os

# Импортируем db и модели
from .models import db

# Импортируем Blueprint'ы
from .routes import main
from .admin import admin

def create_app():
    # Определяем пути к папкам
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    # Настройка базы данных
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/examenator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Регистрируем Blueprint'ы
    app.register_blueprint(main)
    app.register_blueprint(admin)  # Регистрируем админку

    # Инициализируем SQLAlchemy
    db.init_app(app)

    return app