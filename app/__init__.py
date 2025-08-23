# app/__init__.py
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/examenator.db'

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

# ✅ ОБЪЯВЛЯЕМ login_manager, но не инициализируем
login_manager = LoginManager()
login_manager.login_view = 'main.login'


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

    # ✅ Привязываем login_manager к приложению
    login_manager.init_app(app)

    # ✅ Загрузчик пользователя
    @login_manager.user_loader
    def load_user(user_id):
        print(f"🔍 Загрузка пользователя по ID: {user_id}")
        from app.models import User
        user = User.query.get(int(user_id))
        if user:
            print(f"✅ Найден пользователь: {user.username}")
        else:
            print("❌ Пользователь не найден")
        return user

    # ✅ Импортируем модели
    from app.models import User

    app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    # ✅ Регистрируем Blueprint'ы
    from app.routes import main
    app.register_blueprint(main)

    from app.admin import admin
    app.register_blueprint(admin)

    # ✅ Регистрируем assistant Blueprint
    from app.assistant import bp as assistant_bp
    app.register_blueprint(assistant_bp, url_prefix='/assistant') # 👉 Теперь маршрут будет: /assistant/ask

    # ✅ Создаём папку и таблицы
    with app.app_context():
        instance_dir = os.path.join(basedir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db.create_all()
        print("✅ Все таблицы созданы: users, test_types, tests, questions, results")

    return app


__all__ = ['create_app', 'db', 'mail']
