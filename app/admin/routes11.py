# app/admin/routes.py
from app.admin import admin

from flask import render_template, request, redirect, url_for, flash, session
from app.models import TestType, Test, Question, User
from app import db
from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return "Доступ запрещён", 403
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/')
@admin_required
def index():
    types = TestType.query.all()
    return render_template('admin/index.html', types=types)


def get_test_by_type_name(test_type_name):
    """Унифицированная функция для получения теста по имени типа"""
    test_type = TestType.query.filter_by(name=test_type_name).first_or_404()
    test = Test.query.filter_by(test_type_id=test_type.id).first()

    return test, test_type


@admin.route('/diagnostic/<diagnostic_type>')
@admin_required
def select_diagnostic(diagnostic_type):
    print(f"✅ Вызван маршрут: diagnostic_type = {diagnostic_type}")  # ← отладка
    type_map = {
        'incoming': 'ege_rus_incoming',
        'current': 'ege_rus_current',
        'final': 'ege_rus_final'
    }
    if diagnostic_type not in type_map:
        flash("❌ Неверный тип диагностики", "error")
        return redirect(url_for('admin.index'))

    test_type_name = type_map[diagnostic_type]
    test_type = TestType.query.filter_by(name=test_type_name).first_or_404()

    # Проверим, есть ли уже тест
    test = Test.query.filter_by(test_type_id=test_type.id).first()

    return render_template(
        'admin/manage_diagnostic.html', test_type=test_type,
        test=test,
        diagnostic_type=diagnostic_type
    )


@admin.route('/add-test/<test_type_name>', methods=['GET', 'POST'])
@admin_required
def add_test(test_type_name):
    test_type = TestType.query.filter_by(name=test_type_name).first_or_404()
    
    if request.method == 'POST':
        title = request.form['title']
        test_text = request.form['test_text']
        
        # Проверим, нет ли уже теста
        existing = Test.query.filter_by(test_type_id=test_type.id).first()
        if existing:
            flash("Тест для этого типа уже существует.")
            return redirect(url_for('admin.index'))

        test = Test(
            title=title,
            test_text=test_text,
            test_type_id=test_type.id
        )
        db.session.add(test)
        db.session.commit()
        flash("✅ Тест создан")
        return redirect(url_for('admin.index'))

    return render_template('admin/add_test.html', test_type_name=test_type_name)


@admin.route('/add-question/<test_type_name>', methods=['GET', 'POST'])
@admin_required
def add_question(test_type_name):
    test, test_type = get_test_by_type_name(test_type_name)
    if not test:
        flash("Сначала создайте тест для этого типа.")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        question = Question(
            question_number=int(request.form['question_number']),
            question_type=request.form['question_type'],
            task_text=request.form.get('task_text'),
            question_text=request.form['question_text'],
            options=request.form.get('options'),
            correct_answer=request.form['correct_answer'],
            info=request.form.get('info'),
            test_id=test.id
        )
        db.session.add(question)
        db.session.commit()
        flash("✅ Вопрос добавлен")
        return redirect(url_for('admin.index'))

    return render_template('admin/add_question.html', test_type_name=test_type_name, test=test)


@admin.route('/edit-question/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        question.question_number = int(request.form['question_number'])
        question.question_type = request.form['question_type']
        question.task_text = request.form.get('task_text')
        question.question_text = request.form['question_text']
        question.correct_answer = request.form['correct_answer']
        question.options = request.form.get('options')
        question.info = request.form.get('info')
        
        db.session.commit()
        flash("✅ Вопрос обновлён")
        return redirect(url_for('admin.index'))

    return render_template('admin/edit_question.html', question=question)


@admin.route('/edit-test/<test_type_name>', methods=['GET', 'POST'])
@admin_required
def edit_test(test_type_name):
    test, test_type = get_test_by_type_name(test_type_name)
    if not test:
        flash("Тест ещё не создан.")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        test.title = request.form['title']
        test.test_text = request.form['test_text']
        db.session.commit()
        flash("✅ Текст теста обновлён")
        return redirect(url_for('admin.index'))

    return render_template('admin/edit_test.html', test=test, test_type=test_type)


@admin.route('/view-test/<test_type_name>')
@admin_required
def view_test(test_type_name):
    test, test_type = get_test_by_type_name(test_type_name)
    if not test:
        flash("Тест ещё не создан.")
        return redirect(url_for('admin.index'))
    return render_template('admin/view_test.html', test=test, test_type=test_type)