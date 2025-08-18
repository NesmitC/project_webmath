# app/routes.py

from flask import Blueprint, render_template, jsonify, request, url_for, flash, session, redirect, current_app
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
from flask_login import current_user, login_required, login_user
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
    """Обработка отправки теста"""
    try:
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))

        test_id = request.form.get('test_id')
        if not test_id:
            return redirect(url_for('main.examenator'))

        test = Test.query.get(test_id)
        if not test:
            return redirect(url_for('main.examenator'))

        questions = Question.query.filter_by(test_id=test.id).order_by(Question.question_number).all()
        if not questions:
            return redirect(url_for('main.examenator'))

        processing_result = process_test_answers(test, questions, request.form)
        if processing_result.get('error'):
            return redirect(url_for('main.examenator'))

        try:
            result = Result(
                user_id=current_user.id,
                test_type=test.test_type.diagnostic_type,
                score=processing_result['primary_score'],
                total=processing_result['secondary_score'],
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(result)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка сохранения результата: {str(e)}")
            return redirect(url_for('main.examenator'))

        return render_template(
            'result.html',
            results=processing_result['results'],
            primary_score=processing_result['primary_score'],
            essay_points=processing_result['essay_points'],
            secondary_score=processing_result['secondary_score']
        )

    except Exception as e:
        current_app.logger.error(f"Ошибка в submit_test: {str(e)}", exc_info=True)
        return redirect(url_for('main.examenator'))


def process_test_answers(test, questions, form_data):
    """Обрабатывает все ответы теста"""
    result = {
        'primary_score': 0,
        'secondary_score': 0,
        'essay_points': 0,
        'results': [],
        'error': None
    }

    try:
        for q in questions:
            question_result = process_question(q, form_data)
            result['results'].append(question_result)
            result['primary_score'] += question_result['points']

        essay_points, essay_error = process_essay(form_data.get('essay_score', ''))
        if essay_error:
            result['error'] = essay_error
            return result

        result['essay_points'] = essay_points
        result['primary_score'] += essay_points
        result['secondary_score'] = get_secondary_score(result['primary_score'])

    except Exception as e:
        result['error'] = str(e)
        current_app.logger.error(f"Ошибка process_test_answers: {str(e)}")

    return result


def process_question(question, form_data):
    """Обрабатывает один вопрос теста"""
    response = {
        'question': question,
        'user_answer': '',
        'is_correct': False,
        'points': 0,
        'max_points': 1,
        'error': None
    }

    try:
        user_answer = get_user_response(question, form_data)
        response['user_answer'] = user_answer

        if question.question_type == 'matching':
            response.update(evaluate_matching_question(question, user_answer))
        else:
            response.update(evaluate_standard_question(question, user_answer))

    except ValueError as e:
        response['error'] = str(e)
        response['points'] = 0
    except Exception as e:
        response['error'] = "Ошибка обработки вопроса"
        response['points'] = 0
        current_app.logger.warning(f"Ошибка process_question: {str(e)}")

    return response


def get_user_response(question, form_data):
    """Извлекает ответ пользователя"""
    if question.question_type in ['input', 'single', 'contextual-input']:
        answer = form_data.get(f'answer_{question.id}', '').strip()
        if not answer:
            raise ValueError("Пустой ответ")
        if not CYRILLIC_DIGITS_ONLY.match(answer):
            raise ValueError("Недопустимые символы")
        return answer

    elif question.question_type in ['multiple', 'contextual-multiple']:
        answers = form_data.getlist(f'answer_{question.id}')
        return '; '.join(sorted(a.strip() for a in answers if a.strip()))

    elif question.question_type == 'matching':
        answers = []
        for i in range(10):
            val = form_data.get(f'answer_{question.id}_{i}')
            answers.append(f"{chr(65 + i)}-{val if val else '?'}")
        return ', '.join(answers)

    return form_data.get(f'answer_{question.id}', '').strip()


def evaluate_matching_question(question, user_answer):
    """Оценивает вопрос на сопоставление"""
    def normalize(answer_str):
        pairs = [p.strip().upper() for p in answer_str.split(',') if p.strip()]
        return ', '.join(sorted(pairs))

    is_correct = normalize(user_answer) == normalize(question.correct_answer.strip())
    return {
        'is_correct': is_correct,
        'points': 1 if is_correct else 0,
        'max_points': 1
    }


def evaluate_standard_question(question, user_answer):
    """Оценивает стандартные вопросы"""
    correct_answer = question.correct_answer.strip() if question.correct_answer else ""
    points = 0
    max_points = 1

    if user_answer and correct_answer:
        if user_answer.isdigit() and correct_answer.isdigit():
            if question.question_number in [8, 22]:
                max_points = 2
                matches = len(set(user_answer) & set(correct_answer))
                points = 2 if matches == 5 else 1 if matches >= 3 else 0
            else:
                points = 1 if sorted(user_answer) == sorted(correct_answer) else 0
        else:
            user_clean = user_answer.lower().strip()
            correct_options = [opt.strip().lower() for opt in correct_answer.split('|') if opt.strip()]
            points = 1 if user_clean in correct_options else 0

    return {
        'is_correct': points > 0,
        'points': points,
        'max_points': max_points
    }


def process_essay(essay_score):
    """Обрабатывает баллы за сочинение"""
    essay_score = essay_score.strip()
    if not essay_score:
        return 0, None
        
    if not essay_score.isdigit():
        return 0, "Неверный формат балла"
    
    score = int(essay_score)
    if not (0 <= score <= 22):
        return 0, "Балл вне диапазона"
    
    return score, None


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


@main.route('/login', methods=['GET', 'POST'])  # Добавьте GET метод
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Вы успешно вошли в систему", "success")
            next_page = request.args.get('next') or url_for('main.profile')
            return redirect(next_page)
        
        flash("Неверное имя пользователя или пароль", "error")
    
    # Добавьте рендеринг шаблона для GET запросов
    return render_template('login.html')



@main.route('/profile')
@login_required
def profile():
    """Страница профиля пользователя"""
    # Добавим проверку is_authenticated для надежности
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    
    try:
        results = Result.query.filter_by(user_id=current_user.get_id())\
                             .order_by(Result.timestamp.desc())\
                             .all()
        
        return render_template(
            'profile.html',
            user=current_user,
            results=results
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка загрузки профиля: {str(e)}")
        flash("Произошла ошибка при загрузке профиля", "error")
        return redirect(url_for('main.index'))


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
