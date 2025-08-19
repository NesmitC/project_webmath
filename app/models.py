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
    results = db.relationship('Result', back_populates='user')

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

    # Баллы по каждому заданию (1–26): 0, 1 или 2
    q1 = db.Column(db.Integer, default=0)
    q2 = db.Column(db.Integer, default=0)
    q3 = db.Column(db.Integer, default=0)
    q4 = db.Column(db.Integer, default=0)
    q5 = db.Column(db.Integer, default=0)
    q6 = db.Column(db.Integer, default=0)
    q7 = db.Column(db.Integer, default=0)
    q8 = db.Column(db.Integer, default=0)
    q9 = db.Column(db.Integer, default=0)
    q10 = db.Column(db.Integer, default=0)
    q11 = db.Column(db.Integer, default=0)
    q12 = db.Column(db.Integer, default=0)
    q13 = db.Column(db.Integer, default=0)
    q14 = db.Column(db.Integer, default=0)
    q15 = db.Column(db.Integer, default=0)
    q16 = db.Column(db.Integer, default=0)
    q17 = db.Column(db.Integer, default=0)
    q18 = db.Column(db.Integer, default=0)
    q19 = db.Column(db.Integer, default=0)
    q20 = db.Column(db.Integer, default=0)
    q21 = db.Column(db.Integer, default=0)
    q22 = db.Column(db.Integer, default=0)
    q23 = db.Column(db.Integer, default=0)
    q24 = db.Column(db.Integer, default=0)
    q25 = db.Column(db.Integer, default=0)
    q26 = db.Column(db.Integer, default=0)

    # Сочинение — отдельно
    essay_score = db.Column(db.Integer, default=0)

    # Общий балл (можно вычислять автоматически)
    score = db.Column(db.Integer, nullable=False)  # сумма всех заданий + сочинение
    total = db.Column(db.Integer, nullable=False)  # максимальный возможный балл

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Связь с пользователем (если есть)
    user = db.relationship('User', back_populates='results')

    def __repr__(self):
        return f'<Result user_id={self.user_id} test_type={self.test_type} score={self.score}/{self.total}>'

    def calculate_score(self):
        """Вычисляем общий балл на основе полей q1..q26 и essay_score"""
        questions = [getattr(self, f'q{i}', 0) for i in range(1, 27)]
        total_questions = sum(questions)
        self.score = total_questions + (self.essay_score or 0)
        # total — это максимально возможный балл (например, 52 за задания + 24 за сочинение = 76)
        # Можно задать вручную или вычислить по тесту
        return self.score