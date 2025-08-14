# app/admin/__init__.py
from flask import Blueprint

# Создаём Blueprint
admin = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')