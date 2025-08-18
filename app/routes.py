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
import re
from app.utils.primary_to_secondary import get_secondary_score
from flask_login import current_user
from datetime import datetime, timezone


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



# --- ЭКЗАМЕНАТОР: выбор диагностики ---
@main.route('/examenator')
@login_required
def examenator():
    """
    Страница выбора диагностики.
    Показывает доступные тесты: входящая, текущая, контрольная.
    """
    examenator_data = {}
    valid_types = ['incoming', 'current', 'final']

    for test_type in TestType.query.filter(TestType.diagnostic_type.in_(valid_types)).all():
        test = Test.query.filter_by(test_type_id=test_type.id).first()
        if test and len(test.questions) > 0:
            examenator_data[test_type.diagnostic_type] = {
                'title': test_type.title,
                'description': test_type.description,
                'test_id': test.id,
                'diagnostic_type': test_type.diagnostic_type
            }

    return render_template('examenator.html', examenatorData=examenator_data)

# --- ПРОХОЖДЕНИЕ ТЕСТА ЦЕЛИКОМ ---
@main.route('/test/<diagnostic_type>')
@login_required
def start_test(diagnostic_type):
    """
    Начало прохождения теста по типу диагностики.
    Всё на одной странице.
    """
    if diagnostic_type not in ['incoming', 'current', 'final']:
        flash("Неверный тип диагностики.")
        return redirect(url_for('main.examenator'))

    test_type = TestType.query.filter_by(diagnostic_type=diagnostic_type).first_or_404()
    test = Test.query.filter_by(test_type_id=test_type.id).first()

    if not test:
        flash(f"Тест '{test_type.title}' ещё не создан.")
        return redirect(url_for('main.examenator'))

    questions = Question.query.filter_by(test_id=test.id).order_by(Question.question_number).all()
    if not questions:
        flash("В этом тесте пока нет вопросов.")
        return redirect(url_for('main.examenator'))

    return render_template(
        'test_full.html',
        test=test,
        test_type=test_type,
        questions=questions
    )


@main.route('/question/<int:question_index>')
def question(question_index):
    if 'current_test_id' not in session:
        return redirect(url_for('main.examenator'))

    test_id = session['current_test_id']
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).order_by(Question.question_number).all()

    if not questions:
        return redirect(url_for('main.examenator'))

    if question_index < 0 or question_index >= len(questions):
        return redirect(url_for('main.result'))

    current_question = questions[question_index]

    return render_template(
        'question.html',
        current_question=current_question,  # ✅ Обязательно!
        index=question_index,
        total=len(questions)
    )

# ==================================================================


# Паттерн: только кириллица и цифры, длина 1–50
CYRILLIC_DIGITS_ONLY = re.compile(r'^[0-9а-яА-ЯёЁ]{1,50}$')

@main.route('/submit-test', methods=['POST'])
@login_required
def submit_test():
    test_id = request.form['test_id']
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test.id).order_by(Question.question_number).all()

    # ✅ Сохраняем diagnostic_type заранее
    diagnostic_type = test.test_type.diagnostic_type

    primary_score = 0
    results = []

    for q in questions:
        user_answer = None

        # --- Типы с текстовым ответом: input, single, contextual-input ---
        if q.question_type in ['input', 'single', 'contextual-input']:
            user_answer = request.form.get(f'answer_{q.id}', '').strip()

            # Проверка: не пусто и только кириллица + цифры
            if not user_answer:
                flash(f"❌ Задание {q.question_number}: ответ не может быть пустым.", "error")
                # ❌ Не делаем redirect — продолжаем сбор результатов
                # Просто не добавляем баллы
                points = 0
                results.append({
                    'question': q,
                    'user_answer': user_answer,
                    'is_correct': False,
                    'points': points,
                    'max_points': 1
                })
                continue

            if not CYRILLIC_DIGITS_ONLY.match(user_answer):
                flash(f"❌ Задание {q.question_number}: разрешены только цифры и кириллица (1–50 символов).", "error")
                points = 0
                results.append({
                    'question': q,
                    'user_answer': user_answer,
                    'is_correct': False,
                    'points': points,
                    'max_points': 1
                })
                continue

        # --- Типы с множественным выбором ---
        elif q.question_type in ['multiple', 'contextual-multiple']:
            answers = request.form.getlist(f'answer_{q.id}')
            cleaned = sorted([a.strip() for a in answers if a.strip()])
            user_answer = '; '.join(cleaned)

        # --- Установите соответствие ---
        elif q.question_type == 'matching':
            answers = []
            for i in range(10):  # максимум 10 пар
                val = request.form.get(f'answer_{q.id}_{i}')
                if val:
                    answers.append(f"{chr(65 + i)}-{val}")
                else:
                    answers.append(f"{chr(65 + i)}-?")

            user_answer = ', '.join(answers)

            # Нормализация для сравнения
            def normalize_matching(answer_str):
                pairs = [p.strip().upper() for p in answer_str.split(',') if p.strip()]
                return ', '.join(sorted(pairs))

            user_answer_normalized = normalize_matching(user_answer)
            correct_answer_normalized = normalize_matching(q.correct_answer.strip())

            is_correct = user_answer_normalized == correct_answer_normalized
            points = 1 if is_correct else 0

            primary_score += points
            results.append({
                'question': q,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'points': points,
                'max_points': 1
            })
            continue  # пропускаем общую логику

        # --- Все остальные типы ---
        else:
            user_answer = request.form.get(f'answer_{q.id}', '').strip()

        # --- Проверка правильности и начисление баллов ---
        points = 0
        max_points = 1
        correct_answer_clean = q.correct_answer.strip() if q.correct_answer else ""

        if user_answer and correct_answer_clean:
            # 🔢 Если ответ состоит только из цифр
            if user_answer.isdigit() and correct_answer_clean.isdigit():
                user_set = set(user_answer)
                correct_set = set(correct_answer_clean)

                # Задания 8 и 22 — особая система баллов
                if q.question_number in [8, 22]:
                    max_points = 2
                    matches = len(user_set & correct_set)  # пересечение
                    if matches == 5:
                        points = 2
                    elif matches >= 3:
                        points = 1
                    else:
                        points = 0
                # Остальные цифровые задания — 1 балл за совпадение состава цифр
                else:
                    points = 1 if sorted(user_answer) == sorted(correct_answer_clean) else 0

            # 📝 Текстовые ответы (поддержка нескольких вариантов через |)
            else:
                user_clean = user_answer.strip().lower()
                # Разбиваем правильные ответы по | и приводим к нижнему регистру
                correct_options = [opt.strip().lower() for opt in correct_answer_clean.split('|') if opt.strip()]
                # Если пользовательский ответ совпадает с любым из правильных — засчитываем
                if user_clean in correct_options:
                    points = 1
                else:
                    points = 0

        else:
            points = 0  # пустой ответ

        primary_score += points  # ✅ Начисляем баллы за вопрос

        results.append({
            'question': q,
            'user_answer': user_answer,
            'is_correct': points > 0,
            'points': points,
            'max_points': max_points
        })

    # --- ✅ ОБРАБОТКА СОЧИНЕНИЯ — ВНЕ ЦИКЛА ---
    essay_score = request.form.get('essay_score', '').strip()
    essay_points = 0

    if essay_score.isdigit():
        score = int(essay_score)
        if 0 <= score <= 22:
            essay_points = score
        else:
            flash("❌ Балл за сочинение должен быть от 0 до 22.", "error")
    else:
        flash("❌ Балл за сочинение должен быть цифрой от 0 до 22.", "error")

    primary_score += essay_points  # ✅ Добавляем только один раз

    # --- Финальные баллы ---
    secondary_score = get_secondary_score(primary_score)  # ✅ Переводим в 100-балльную шкалу

    # --- ✅ СОХРАНЕНИЕ РЕЗУЛЬТАТА В БД ---
    if current_user.is_authenticated:
        try:
            result = Result(
                user_id=current_user.id,
                test_type=diagnostic_type,
                score=primary_score,
                total=secondary_score,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(result)
            db.session.commit()
            print("✅ Результат сохранён в БД")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка сохранения: {e}")
    else:
        print("⚠️ Пользователь не залогинен — результат не сохранён")
        flash("⚠️ Результат не сохранён: вы не авторизованы.", "error")

    # --- Отображение результата ---
    return render_template(
        'result.html', 
        results=results, 
        primary_score=primary_score,
        essay_points=essay_points,
        secondary_score=secondary_score
    )



# ==================================================================

@main.route('/result')
def result():
    if 'current_test_id' not in session:
        return redirect(url_for('main.examenator'))

    test = Test.query.get_or_404(session['current_test_id'])
    questions = Question.query.filter_by(test_id=test.id).order_by(Question.question_number).all()
    user_answers = session.get('answers', [])

    correct = 0
    results = []

    for i, q in enumerate(questions):
        is_correct = user_answers[i].strip().lower() == q.correct_answer.strip().lower()
        if is_correct:
            correct += 1
        results.append({
            'question': q,
            'user_answer': user_answers[i],
            'is_correct': is_correct
        })

    # Очищаем сессию
    session.pop('current_test_id', None)
    session.pop('current_question_index', None)
    session.pop('answers', None)

    return render_template('result.html', results=results, correct=correct, total=len(questions))


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
