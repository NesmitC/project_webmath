# app/models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TestType(db.Model):
    __tablename__ = 'test_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Связь с тестами
    tests = db.relationship('Test', backref='type', lazy=True)

    def __repr__(self):
        return f"<TestType {self.name}>"


class Test(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    test_text = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('test_types.id'), nullable=False)

    # Связь с вопросами
    questions = db.relationship('Question', backref='test', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.title}>"


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3...27
    question_type = db.Column(db.String(50), nullable=False)  # 'input', 'checkbox', 'match', 'textarea'
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)  # строки через "|", например: "опция1|опция2"
    correct_answer = db.Column(db.Text)  # "их" или "0,1" или "1,3,5"
    info = db.Column(db.Text)  # для сочинений

    def __repr__(self):
        return f"<Question {self.question_number} for Test {self.test_id}>"