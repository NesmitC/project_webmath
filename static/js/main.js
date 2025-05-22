function checkSolution() {
    const solution = document.getElementById('user-solution').value;
            
    fetch('/check_solution', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ solution: solution })
    })
    .then(response => response.json())
    .then(data => {
        const resultDiv = document.getElementById('result');
        if (data.error) {
            resultDiv.innerHTML = `<p class="error">Ошибка: ${data.error}</p>`;
        } else if (data.correct) {
            resultDiv.innerHTML = '<p class="success">Верно!</p>';
        } else {
            resultDiv.innerHTML = `
                <p class="error">Неверно</p>
                <p>Ожидалось: F(x) = ${data.expected.replace('**', '^')} + C</p>
            `;
        }
    });
}
        
function newTask() {
    window.location.reload();
}