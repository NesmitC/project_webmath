import random
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def generate_random_function():
    """Генерирует случайную f(x) и её первообразную F(x)."""
    functions = [
        ("f(x) = 2x", "x**2"),  # Первообразная для 2x -> x^2
        ("f(x) = 3x**2", "x**3"),  # Для 3x^2 -> x^3
        ("f(x) = cos(x)", "sin(x)"),
        ("f(x) = e^x", "e^x"),
    ]
    return random.choice(functions)

def plot_function(F_expr, x_range=(-3, 5)):
    """Генерирует график F(x) и возвращает его в base64."""
    x = np.linspace(x_range[0], x_range[1], 100)
    y = eval(F_expr, {'x': x, 'sin': np.sin, 'cos': np.cos, 'e': np.e, 'exp': np.exp})
    
    plt.figure()
    plt.plot(x, y)
    plt.title(f"График F(x) = {F_expr}")
    plt.grid()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')