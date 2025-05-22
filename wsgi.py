from flask import Flask, render_template, request, jsonify
from calculus import generate_random_function, plot_function, calculate_derivative
from sympy import symbols, sympify, lambdify, diff
import os
from dotenv import load_dotenv
from neuroassist.assistant import CompanyAssistant



app = Flask(__name__)
assistant = CompanyAssistant()

# Обработчик POST-запросов
@app.route('/assistant', methods=['POST'])
def ask_assistant():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Требуется JSON с полем 'question'"}), 400
            
        answer = assistant.find_answer(data['question'])
        return jsonify({
            "question": data['question'],
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        assistant.logger.error(f"API Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    

# Добавляем GET-вариант для тестирования из браузера
@app.route('/assistant', methods=['GET'])
def ask_assistant_get():
    question = request.args.get('q', '')
    if not question:
        return "Используйте параметр ?q=ваш_вопрос", 400
    
    answer = assistant.find_answer(question)
    return f"""
    <h1>Ответ ассистента</h1>
    <p><b>Вопрос:</b> {question}</p>
    <p><b>Ответ:</b> {answer}</p>
    <a href="/">Новый вопрос</a>
    """



# Загружаем .env из instance/ или корня
env_path = os.path.join(os.path.dirname(__file__), 'instance', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Попробует загрузить из корня



@app.route('/')
def index():
    return "Hello, World!"



@app.route('/task')
def task():
    f_expr, F_expr = generate_random_function()
    graph = plot_function(F_expr)
    return render_template('task.html', 
                         f_expr=f_expr,
                         F_expr=f"F(x) = {F_expr.replace('**', '^')} + C",
                         graph=graph)

@app.route('/check_solution', methods=['GET', 'POST'])
def check_solution():
    if request.method == 'GET':
        return jsonify({"message": "Используйте POST для проверки решения"})
    
    try:
        data = request.get_json()
        user_solution = data.get('solution', '')
        
        # В реальном приложении нужно хранить текущую задачу в сессии
        _, correct_F = generate_random_function()
        
        # Простая проверка (можно улучшить)
        is_correct = user_solution.replace(' ', '') == correct_F.replace('**', '^')
        
        return jsonify({
            "correct": is_correct,
            "expected": correct_F
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400





if __name__ == '__main__':
    app.run(
        host = 'localhost',
        port = 5005,
        debug = True
    )
