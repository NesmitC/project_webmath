from flask import Flask, render_template
from calculus import generate_random_function, plot_function

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/task')
def task():
    f_expr, F_expr = generate_random_function()
    graph = plot_function(F_expr)  # Теперь передаём только выражение (без "F(x) =")
    return render_template('task.html', 
                         f_expr=f_expr, 
                         F_expr=f"F(x) = {F_expr} + C",  # Добавляем красивый формат
                         graph=graph)

if __name__ == '__main__':
    app.run(
        host = 'localhost',
        port = 5005,
        debug = True
    )
