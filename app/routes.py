# app/routes.py

from flask import Blueprint, render_template, jsonify, request, url_for, flash, session, redirect
from .assistant import ask_teacher
from .neuro_method import ask_methodist  # ✅ Импорт методиста
from app.models import TestType, Test, Question, User, Result
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from app import db, mail


main = Blueprint('main', __name__)


# ✅ Декоратор для защиты маршрутов
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("⚠️ Войдите в аккаунт, чтобы пройти тест.")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

# === Маршруты ===

@main.route('/')
def index():
    return render_template('index.html')



@main.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"answer": "Пожалуйста, задайте вопрос."})

    # Сначала проверяем, не методический ли вопрос
    methodist_response = ask_methodist(question)
    if methodist_response:
        return jsonify({
            "answer": f"Методист: {methodist_response}"
        })

    # Если не методический — отвечает учитель
    teacher_response = ask_teacher(question)
    return jsonify({
        "answer": f"Учитель: {teacher_response}"
    })


@main.route('/about')
def about():
    return render_template('about.html')


# Путь к файлу
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'examenator.db')



@main.route('/examenator')
@login_required   # ← Эта строка защищает маршрут
def examenator():
    examenator_data = {}
    test_types = ['incoming', 'current', 'final']

    for t in test_types:
        type_obj = TestType.query.filter_by(name=t).first()
        if type_obj and type_obj.tests:
            test = type_obj.tests[0]
            examenator_data[t] = {
                'title': test.title,
                'text': test.test_text,
                'questions': []
            }
            for q in test.questions:
                examenator_data[t]['questions'].append({
                    'id': q.question_number,
                    'type': q.question_type,
                    'question': q.question_text,
                    'question_text': q.question_text,
                    'options': q.options.split('|') if q.options else [],
                    'correct_answer': q.correct_answer,
                    'info': q.info
                })

    return render_template('examenator.html', examenatorData=examenator_data, test_types=test_types)

# ✅ Остальные маршруты (регистрация, вход, профиль) — без изменений

# ==================================================================
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')
        telegram = request.form.get('telegram')

        # Преобразуем пустую строку в None
        telegram = telegram.strip() if telegram else None
        if telegram == '':
            telegram = None

        # Проверка, существует ли пользователь
        if User.query.filter_by(username=username).first():
            flash("Пользователь с таким именем уже существует.")
            return redirect(url_for('main.register'))

        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует.")
            return redirect(url_for('main.register'))

        # Хэшируем пароль
        hashed_password = generate_password_hash(password)

        # Создаём пользователя
        user = User(
            username=username,
            password=hashed_password,
            email=email,
            telegram=telegram  # Теперь None, если пусто
        )
        db.session.add(user)
        db.session.commit()

        send_confirmation_email(user)
        flash("✅ Регистрация успешна! Проверьте email для подтверждения.")
        return redirect(url_for('main.index'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("✅ Вы вошли в систему!")
            return redirect(url_for('main.profile'))
        else:
            flash("❌ Неверное имя пользователя или пароль.")

    return render_template('login.html')

@main.route('/profile')
@login_required  # ← тоже защищаем профиль
def profile():
    user = User.query.get(session['user_id'])
    results = Result.query.filter_by(user_id=user.id).order_by(Result.timestamp.desc()).all()
    return render_template('profile.html', user=user, results=results)

@main.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Вы вышли из системы.")
    return redirect(url_for('main.index'))

# ---------------------------------------------------------------------
@main.route('/submit-test', methods=['POST'])
@login_required  # ← результаты тоже только для авторизованных
def submit_test():
    data = request.get_json()
    result = Result(
        user_id=session['user_id'],
        test_type=data.get('test_type'),
        score=data.get('score'),
        total=data.get('total')
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({"message": "Результат сохранён!"})

# ---------------------------------------------------------------------
# Создаём сериализатор
def get_serializer():
    return URLSafeTimedSerializer(os.getenv('SECRET_KEY'))

def send_confirmation_email(user):
    s = get_serializer()
    token = s.dumps(user.email, salt='email-confirm-salt')

    confirm_url = url_for('main.confirm_email', token=token, _external=True)

    html = f"""
    <h3>Добро пожаловать в Нейростат, {user.username}!</h3>
    <p>Пожалуйста, подтвердите ваш email, перейдя по ссылке:</p>
    <a href="{confirm_url}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">
        Подтвердить email
    </a>
    <p>Ссылка действует 1 час.</p>
    """

    msg = Message("Подтвердите ваш email", recipients=[user.email])
    msg.html = html
    mail.send(msg)


# ---------------------------------------------------------------------
# Маршруты для подтверждения emeil
@main.route('/confirm/<token>')
def confirm_email(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt='email-confirm-salt', max_age=3600)  # 1 час
    except:
        flash("Ссылка недействительна или истекла.")
        return redirect(url_for('main.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Пользователь не найден.")
        return redirect(url_for('main.login'))

    if user.confirmed:
        flash("Ваш email уже подтверждён.")
    else:
        user.confirmed = True
        db.session.commit()
        flash("✅ Email успешно подтверждён! Добро пожаловать!")

    return redirect(url_for('main.profile'))

@main.route('/resend')
def resend_confirmation():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    if user.confirmed:
        flash("Ваш email уже подтверждён.")
    else:
        send_confirmation_email(user)
        flash("Письмо с подтверждением отправлено на ваш email.")

    return redirect(url_for('main.profile'))


# ---------------------------------------------------------------------
