# app/admin/routes.py
from flask import render_template, request, redirect, url_for, flash, session
from app.models import db, TestType, Test, Question, User
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

@admin.route('/test/<test_type>')
@admin_required
def view_test(test_type):
    type_obj = TestType.query.filter_by(name=test_type).first_or_404()
    test = Test.query.filter_by(type_id=type_obj.id).first()
    if not test:
        flash("Тест не найден")
        return redirect(url_for('admin.index'))
    return render_template('admin/view_test.html', test=test, type_obj=type_obj)

@admin.route('/add-question/<test_type>', methods=['GET', 'POST'])
@admin_required
def add_question(test_type):
    type_obj = TestType.query.filter_by(name=test_type).first_or_404()
    test = Test.query.filter_by(type_id=type_obj.id).first()

    if not test:
        flash("Сначала создайте тест для этого типа.")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        question = Question(
            test_id=test.id,
            question_number=int(request.form['question_number']),
            question_type=request.form['question_type'],
            question_text=request.form['question_text'],
            options=request.form['options'] or None,
            correct_answer=request.form['correct_answer'],
            info=request.form['info'] or None
        )
        db.session.add(question)
        db.session.commit()
        flash("✅ Вопрос добавлен!")
        return redirect(url_for('admin.view_test', test_type=test_type))

    return render_template('admin/add_question.html', test_type=test_type, test=test)


# ✏️ Редактирование и удаление вопросов
@admin.route('/edit-question/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    # Находим вопрос
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        # Обновляем поля
        question.question_number = int(request.form['question_number'])
        question.question_type = request.form['question_type']
        question.question_text = request.form['question_text']
        question.options = request.form['options'] or None
        question.correct_answer = request.form['correct_answer']
        question.info = request.form['info'] or None

        db.session.commit()
        flash("✅ Вопрос успешно обновлён!")
        return redirect(url_for('admin.view_test', test_type=question.test.type.name))

    return render_template('admin/edit_question.html', question=question)


# ✏️ Редактирование текстов
@admin.route('/edit-test/<test_type>', methods=['GET', 'POST'])
@admin_required
def edit_test(test_type):
    # Находим тип теста и сам тест
    type_obj = TestType.query.filter_by(name=test_type).first_or_404()
    test = Test.query.filter_by(type_id=type_obj.id).first()

    if not test:
        flash("Тест не найден")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        # Обновляем поля
        test.title = request.form['title']
        test.test_text = request.form['test_text']
        db.session.commit()
        flash("✅ Текст теста успешно обновлён!")
        return redirect(url_for('admin.view_test', test_type=test_type))

    return render_template('admin/edit_test.html', test=test, type_obj=type_obj)


@admin.route('/delete-question/<int:question_id>', methods=['POST'])
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    test_type = question.test.type.name  # Сохраняем тип теста для редиректа
    db.session.delete(question)
    db.session.commit()
    flash("🗑️ Вопрос успешно удалён!")
    return redirect(url_for('admin.view_test', test_type=test_type))
