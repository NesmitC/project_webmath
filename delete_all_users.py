# delete_all_users.py
from wsgi import app
from app.models import db, User, Result

with app.app_context():
    # Удаляем результаты
    Result.query.delete()
    print("✅ Все результаты удалены")

    # Удаляем пользователей
    User.query.delete()
    print("✅ Все пользователи удалены")

    # Сохраняем
    db.session.commit()

    # Проверка
    print(f"Осталось пользователей: {User.query.count()}")