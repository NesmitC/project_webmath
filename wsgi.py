# wsgi.py
from flask import Flask, render_template, request, jsonify
import re
from calculus import generate_random_function, plot_function, calculate_derivative
from sympy import symbols, sympify, lambdify, diff
import os
from dotenv import load_dotenv
from datetime import datetime
from app.assistant import ask_teacher
import requests
from models import get_response, clean_response
from app import create_app
from huggingface_hub import snapshot_download


app = Flask(__name__)


app = create_app()



def backend_factory():
    return requests.Session()



if __name__ == '__main__':
    app.run(
        # host = 'localhost',
        host='0.0.0.0',
        port = 5005,
        debug = True
    )
