import random
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Важно: используем неинтерактивный бэкенд
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from sympy import symbols, sympify, lambdify, sin, cos, exp, log, Abs, diff

x = symbols('x')

def generate_random_function():
    """Генерирует случайную f(x) и её первообразную F(x)."""
    functions = [
        ("2*x", "x**2"),
        ("3*x**2", "x**3"),
        ("cos(x)", "sin(x)"),
        ("exp(x)", "exp(x)"),
        ("1/x", "log(Abs(x))"),
        ("sqrt(x)", "2/3*x**(3/2)"),
    ]
    f_expr, F_expr = random.choice(functions)
    return f"f(x) = {f_expr}", F_expr

def plot_function(F_expr, x_range=(-3, 5)):
    """Строит график и возвращает base64 изображение."""
    try:
        expr = sympify(F_expr)
        func = lambdify(x, expr, modules=['numpy'])
        
        x_vals = np.linspace(*x_range, 500)
        y_vals = func(x_vals)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(x_vals, y_vals)
        ax.set_title(f"График первообразной")
        ax.grid(True)
        
        buf = BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Ошибка построения графика: {e}")
        return None
    
    
def calculate_derivative(F_expr):
    """Вычисляет производную от первообразной (т.е. исходную функцию f(x))"""
    try:
        expr = sympify(F_expr)
        derivative = diff(expr, x)  # diff - функция символьного дифференцирования
        return str(derivative).replace('**', '^')
    except Exception as e:
        return f"Ошибка вычисления производной: {e}"