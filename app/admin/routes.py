# app/admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import TestType, Test, Question, User
from app import db
from functools import wraps

# Импортируем admin из текущего пакета
from . import admin


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


@admin.route('/add-question/<test_type_name>', methods=['GET', 'POST'])
@admin_required
def add_question(test_type_name):
    test_type = TestType.query.filter_by(name=test_type_name).first_or_404()
    
    # ✅ Исправлено: используем filter_by(test_type_id=...)
    test = Test.query.filter_by(test_type_id=test_type.id).first()
    
    if not test:
        flash("Сначала создайте тест для этого типа.")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        question_number = int(request.form['question_number'])
        question_type = request.form['question_type']
        task_text = request.form.get('task_text')  # может быть None
        question_text = request.form['question_text']
        options = request.form.get('options')
        correct_answer = request.form['correct_answer']
        info = request.form.get('info')

        question = Question(
            question_number=question_number,
            question_type=question_type,
            task_text=task_text,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            info=info,
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
    test_type = TestType.query.filter_by(name=test_type_name).first_or_404()
    
    # ✅ Исправлено: используем filter_by(test_type_id=...)
    test = Test.query.filter_by(test_type_id=test_type.id).first()
    
    if not test:
        flash("Тест ещё не создан. Сначала создайте тест.")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        title = request.form['title']
        test_text = request.form['test_text']
        
        test.title = title
        test.test_text = test_text
        db.session.commit()
        
        flash("✅ Текст теста успешно обновлён")
        return redirect(url_for('admin.index'))

    return render_template('admin/edit_test.html', test=test, test_type=test_type)


@admin.route('/view-test/<test_type_name>')
@admin_required
def view_test(test_type_name):
    # Находим тип теста по имени
    test_type = TestType.query.filter_by(name=test_type_name).first_or_404()
    
    # ✅ Правильно находим тест по test_type_id
    test = Test.query.filter_by(test_type_id=test_type.id).first()
    
    # Если теста нет — показываем сообщение и возвращаемся
    if not test:
        flash("Тест ещё не создан.")
        return redirect(url_for('admin.index'))
    
    # Передаём тест и тип теста в шаблон
    return render_template('admin/view_test.html', test=test, test_type=test_type)