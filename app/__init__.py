from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')

    from app.routes import bp
    app.register_blueprint(bp)

    return app
