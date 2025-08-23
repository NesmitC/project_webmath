# app/neuro_kurator.py

from app.models import Result
from datetime import datetime

# Правила: какие номера заданий относятся к каким темам
THEME_MAP = {
    'стиль и лексика текста': [1, 2, 3],
    'орфоэпия': [4],
    'речевая норма: паронимы': [5],
    'речевая норма: плеоназм (избыточность) и лексическая сочетаемость': [6],
    'грамматические нормы': [7, 8],
    'орфография': [9, 10, 11, 12, 13, 14, 15],
    'пунктуация': [16, 17, 18, 19, 20, 21],
    'выразительные средства': [22],
    'смысл текста': [23],
    'типы текста': [24],
    'лексические особенности текста': [25],
    'связь предложений': [26],
    'сочинение': ['essay']
}

# Порог для "слабого места" — средний балл за задание < 1.2
WEAK_THRESHOLD = 1.2


def analyze_student(user_id, db):
    """Анализирует все результаты ученика и возвращает персональный отчёт"""
    results = Result.query.filter_by(user_id=user_id).order_by(Result.timestamp).all()

    if not results:
        return {"error": "Нет данных о тестировании"}

    # Собираем статистику по каждому заданию
    scores = {i: [] for i in range(1, 27)}
    essay_scores = []
    test_dates = []

    for r in results:
        for i in range(1, 27):
            q_score = getattr(r, f'q{i}', 0)
            if q_score is not None:
                scores[i].append(q_score)
        if r.essay_score is not None:
            essay_scores.append(r.essay_score)
        test_dates.append(r.timestamp)

    # Считаем средние баллы
    avg_scores = {i: sum(s) / len(s) for i, s in scores.items() if s}
    avg_essay = sum(essay_scores) / len(essay_scores) if essay_scores else 0

    # Находим слабые темы
    weak_themes = []
    for theme, questions in THEME_MAP.items():
        if theme == 'сочинение':
            if avg_essay < 12:
                weak_themes.append('сочинение')
            continue

        theme_scores = [avg_scores[q] for q in questions if q in avg_scores]
        if theme_scores:
            avg = sum(theme_scores) / len(theme_scores)
            if avg < WEAK_THRESHOLD:
                weak_themes.append(theme)

    # Определяем тип тестирования
    test_types = [r.test_type for r in results]
    first_type = test_types[0] if test_types else '—'
    last_type = test_types[-1] if test_types else '—'

    # Формируем рекомендации
    recommendations = generate_recommendations(weak_themes)

    return {
        'user_id': user_id,
        'total_tests': len(results),
        'first_test': test_dates[0] if test_dates else None,
        'last_test': test_dates[-1] if test_dates else None,
        'test_progress': f"{first_type} → {last_type}",
        'avg_scores': avg_scores,
        'weak_themes': weak_themes,
        'strong_themes': [t for t in THEME_MAP.keys() if t not in weak_themes],
        'avg_essay': round(avg_essay, 1),
        'recommendations': recommendations,
        'has_improved': len(results) > 1  # можно улучшить — сравнивать first и last score
    }


def generate_recommendations(weak_themes):
    """Генерирует персональные рекомендации (для русского языка)"""
    recs = []

    if 'орфоэпия' in weak_themes:
        recs.append("Пройди модуль «Орфоэпия» и реши 5 тренировочных тестов.")
    if 'речевая норма: паронимы' in weak_themes:
        recs.append("Повтори паронимы — выполни 3 упражнения из модуля «Лексика».")
    if 'орфография' in weak_themes:
        recs.append("Повтори корни с чередованием и правила правописания приставок — реши 5 упражнений.")
    if 'пунктуация' in weak_themes:
        recs.append("Потренируй расстановку запятых в сложных предложениях — выполни интерактивный тест.")
    if 'сочинение' in weak_themes:
        recs.append("Напиши сочинение и отправь на проверку — я дам подробную обратную связь по критериям.")
    if 'стиль и лексика текста' in weak_themes:
        recs.append("Повтори стилистические ошибки и лексическую сочетаемость — посмотри видео и пройди викторину.")
    if not recs:
        recs.append("Отличная работа! У тебя нет слабых тем. Хочешь пройти пробный экзамен?")

    return recs