# seed_data.py
from wsgi import app
from app.models import db, TestType, Test, Question

with app.app_context():
    # Удаляем старые данные
    db.drop_all()
    db.create_all()

    # Создаём типы тестов
    incoming = TestType(name='incoming')
    current = TestType(name='current')
    final = TestType(name='final')
    db.session.add_all([incoming, current, final])
    db.session.commit()

    # Текст для всех тестов (можно разный)
    text_incoming = "Нам лишь кажется, что, когда с нами что-то случается, это уникальное явление..."
    text_current = "В.И. Даль — выдающийся русский лексикограф, этнограф, писатель..."
    text_final = "Трудности — это неотъемлемая часть жизни. Они могут сломить человека, но могут и раскрыть его лучшие качества..."

    # === Входящая диагностика ===
    test_incoming = Test(title="Входящая диагностика", test_text=text_incoming, type_id=incoming.id)
    db.session.add(test_incoming)
    db.session.commit()

    db.session.add_all([
        Question(test_id=test_incoming.id, question_number=1, question_type="input", question_text="Подберите местоимение...", correct_answer="их"),
        Question(test_id=test_incoming.id, question_number=2, question_type="checkbox", question_text="Укажите верные значения...", options="НАТУРА. Характер...|ОТМЕЧАТЬ. Праздновать...", correct_answer="0,1"),
    ])
    db.session.commit()

    # === Текущая диагностика ===
    test_current = Test(title="Текущая диагностика", test_text=text_current, type_id=current.id)
    db.session.add(test_current)
    db.session.commit()

    db.session.add_all([
        Question(test_id=test_current.id, question_number=1, question_type="input", question_text="Укажите способ образования слова СОЗДАТЕЛЬ.", correct_answer="суффиксальный"),
        Question(test_id=test_current.id, question_number=2, question_type="checkbox", question_text="Укажите верные значения слов.", options="ВОЗРАЗИТЬ. Заявить о несогласии.|ВОСТОРГ. Подъём чувств.", correct_answer="0,1"),
    ])
    db.session.commit()

    # === Итоговая диагностика ===
    test_final = Test(title="Итоговая диагностика", test_text=text_final, type_id=final.id)
    db.session.add(test_final)
    db.session.commit()

    db.session.add_all([
        Question(test_id=test_final.id, question_number=1, question_type="input", question_text="Подберите уступительный союз.", correct_answer="хотя"),
        Question(test_id=test_final.id, question_number=27, question_type="textarea", question_text="Напишите сочинение-рассуждение: «Как трудности раскрывают характер человека?»", info="Объём — не менее 150 слов."),
    ])
    db.session.commit()

    print("✅ Все три теста (входящая, текущая, итоговая) добавлены в базу!")