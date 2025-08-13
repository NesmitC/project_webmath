# init_db.py
from wsgi import app
from app.models import db

with app.app_context():
    db.create_all()
    print("✅ Базы данных и таблицы созданы в database/examenator.db")