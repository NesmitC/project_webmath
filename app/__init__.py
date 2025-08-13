# app/__init__.py
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
import os

# Создаём экземпляры расширений
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()

# Контекстный процессор — доступен во всех шаблонах
def inject_user():
    from app.models import User  # ✅ Импорт внутри функции
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        user = None
    return dict(current_user=user)

def create_app():
    basedir = os.path.dirname(os.path.dirname(__file__))
    template_dir = os.path.join(basedir, 'templates')
    static_dir = os.path.join(basedir, 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/examenator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Настройки email
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Инициализация расширений
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # ✅ Регистрируем контекстный процессор
    app.context_processor(inject_user)

    # Регистрируем Blueprint'ы
    from .routes import main
    from .admin import admin
    app.register_blueprint(main)
    app.register_blueprint(admin)

    return app

# Экспорт для импорта в других файлах
__all__ = ['create_app', 'db', 'mail']