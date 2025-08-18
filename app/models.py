# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from app import db
from flask_login import UserMixin


class TestType(db.Model):
    __tablename__ = 'test_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    diagnostic_type = db.Column(db.String(20))  # 'incoming', 'current', 'final'


class Test(db.Model):
    __tablename__ = 'test'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    test_text = db.Column(db.Text)
    test_type_id = db.Column(db.Integer, db.ForeignKey('test_type.id'), nullable=False)

    # Связи
    test_type = db.relationship('TestType', backref='tests')  # ✅ Обязательно!
    questions = db.relationship('Question', backref='test', lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    question_number = db.Column(db.Integer, nullable=False)
    context_text = db.Column(db.Text)
    question_type = db.Column(db.String(50), nullable=False)
    task_text = db.Column(db.Text)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)
    correct_answer = db.Column(db.String(200), nullable=False)
    info = db.Column(db.Text)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    score = db.Column(db.Integer, default=1)


# === НОВОЕ: Пользователь и результаты ===

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Хэшированный
    email = db.Column(db.String(150), unique=True, nullable=True)
    telegram = db.Column(db.String(100), unique=True, nullable=True)
    confirmed = db.Column(db.Boolean, default=False)  # ← новое поле
    is_admin = db.Column(db.Boolean, default=False)  # ← новое поле
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    results = db.relationship('Result', backref='user', lazy=True, cascade="all, delete-orphan")

    # Методы для flask_login
    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)  # 'incoming', 'current', 'final'
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))