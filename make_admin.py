# make_admin.py
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Найди пользователя по имени
    username = input("Введите имя пользователя: ")
    user = User.query.filter_by(username=username).first()

    if user:
        user.is_admin = True
        db.session.commit()
        print(f"✅ Пользователь '{user.username}' теперь администратор!")
    else:
        print("❌ Пользователь не найден")