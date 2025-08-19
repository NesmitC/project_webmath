# Временный скрипт: clear_results.py
from app import create_app, db
from app.models import Result

app = create_app()
with app.app_context():
    Result.query.delete()
    db.session.commit()
    print("Все результаты удалены.")