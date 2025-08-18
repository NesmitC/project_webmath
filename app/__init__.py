# app/__init__.py
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
import os


# Создаём экземпляры расширений
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()


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

    # --- ✅ Перенесён внутрь create_app() ---
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    # Загрузчик пользователя
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    # --- КОНЕЦ ---

    # Импортируем модели после инициализации db
    from app.models import User

    # Контекстный процессор для current_user
    def inject_user():
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user is None:
                session.pop('user_id', None)
        return dict(current_user=user)

    app.context_processor(inject_user)

    # Регистрируем Blueprint'ы
    from app.routes import main
    app.register_blueprint(main)

    from app.admin import admin
    app.register_blueprint(admin)

    return app


# Экспорт для импорта в других файлах
__all__ = ['create_app', 'db', 'mail']