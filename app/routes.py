from flask import render_template, request, jsonify, Blueprint
from app.assistant import ask_teacher
from app import app


bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Пожалуйста, задайте вопрос."})
    
    answer = ask_teacher(question)
    return jsonify({"answer": answer})


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "").strip()
    answer = ask_teacher(question)
    return jsonify({"answer": answer})