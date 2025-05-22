import random
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Важно для работы в Flask
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from sympy import (symbols, lambdify, diff, 
                  sin, cos, exp, log, Abs, sqrt)
from sympy.parsing.sympy_parser import (parse_expr, 
                                       standard_transformations, 
                                       implicit_multiplication,
                                       convert_xor)

# Инициализация символьной переменной
x = symbols('x')

# Настройки безопасного парсера
transformations = (standard_transformations + 
                  (implicit_multiplication, 
                   convert_xor))

def safe_sympify(expr):
    """
    Безопасно преобразует строку в sympy-выражение.
    Поддерживает:
    - Неявное умножение (2x → 2*x)
    - Степени через ^ (x^2 → x**2)
    - Основные математические функции
    """
    try:
        return parse_expr(expr, transformations=transformations)
    except Exception as e:
        raise ValueError(f"Некорректное выражение: {expr}. Ошибка: {str(e)}")

def generate_random_function():
    """Генерирует случайную f(x) и её первообразную F(x)."""
    functions = [
        ("2*x", "x**2"),
        ("3*x**2", "x**3"),
        ("cos(x)", "sin(x)"),
        ("exp(x)", "exp(x)"),
        ("1/x", "log(Abs(x))"),
        ("sqrt(x)", "(2/3)*x**(3/2)"),
        ("sin(x)", "-cos(x)"),
    ]
    f_expr, F_expr = random.choice(functions)
    return f"f(x) = {f_expr}", F_expr

def plot_function(F_expr, x_range=(-3, 5)):
    """
    Строит график функции с защищённым парсингом.
    Возвращает base64-encoded изображение или None при ошибке.
    """
    try:
        # Безопасный парсинг
        expr = safe_sympify(F_expr)
        
        # Генерация данных
        func = lambdify(x, expr, modules=['numpy'])
        x_vals = np.linspace(x_range[0], x_range[1], 500)
        y_vals = func(x_vals)
        
        # Построение графика
        plt.figure(figsize=(10, 5))
        plt.plot(x_vals, y_vals)
        plt.title(f"График первообразной")
        plt.xlabel("x")
        plt.ylabel("F(x)")
        plt.grid(True)
        
        # Конвертация в base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    except Exception as e:
        print(f"Ошибка при построении графика: {e}")
        return None

def calculate_derivative(F_expr):
    """
    Вычисляет производную с защищённым парсингом.
    Возвращает строку с производной или сообщение об ошибке.
    """
    try:
        expr = safe_sympify(F_expr)
        derivative = diff(expr, x)
        return str(derivative).replace('**', '^')
    except Exception as e:
        return f"Ошибка вычисления производной: {str(e)}"