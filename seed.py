# seed.py
from app import create_app, db
from app.models import TestType

app = create_app()

with app.app_context():
    # Удаляем старые (для чистоты)
    db.session.query(TestType).filter(TestType.name.like('ege_rus_%')).delete()

    # Создаём три типа
    incoming = TestType(
        name="ege_rus_incoming",
        subject="russian",
        title="Входящая диагностика",
        description="Стартовое тестирование",
        diagnostic_type="incoming"
    )

    current = TestType(
        name="ege_rus_current",
        subject="russian",
        title="Текущая диагностика",
        description="Промежуточное тестирование",
        diagnostic_type="current"
    )

    final = TestType(
        name="ege_rus_final",
        subject="russian",
        title="Контрольная диагностика",
        description="Итоговое тестирование",
        diagnostic_type="final"
    )

    db.session.add_all([incoming, current, final])
    db.session.commit()

    print("✅ Все три типа диагностики добавлены!")