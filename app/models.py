# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from app import db

class TestType(db.Model):
    __tablename__ = 'test_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Связь: один тип → много тестов
    tests = db.relationship('Test', backref='type', lazy=True, cascade="all, delete-orphan")


class Test(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    test_text = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('test_types.id'), nullable=False)

    # Связь: один тест → много вопросов
    questions = db.relationship('Question', backref='test', lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    info = db.Column(db.Text)


# === НОВОЕ: Пользователь и результаты ===

class User(db.Model):
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


class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)  # 'incoming', 'current', 'final'
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))