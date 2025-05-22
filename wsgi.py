from flask import Flask, render_template, request, jsonify
from calculus import generate_random_function, plot_function, calculate_derivative
from sympy import symbols, sympify, lambdify, diff
import os
from dotenv import load_dotenv

# Загружаем .env из instance/ или корня
env_path = os.path.join(os.path.dirname(__file__), 'instance', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Попробует загрузить из корня



app = Flask(__name__)

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
