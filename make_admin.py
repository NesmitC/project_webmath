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

'''
Открой терминал (в корне проекта) и выполни:

bash
python make_admin.py

Введи имя пользователя
mika 
----------------------------
Открой файл app/assistant.py
Закомментируй или удали эту строку
# if not os.getenv('DEEPSEEK_API_KEY'):
#     raise EnvironmentError("DEEPSEEK_API_KEY не установлена")

'''
