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

document.getElementById("chat-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const question = document.getElementById("question").value.trim();
    if (!question) return;

    const chatBox = document.getElementById("chat-box");
    const userMsg = document.createElement("div");
    userMsg.className = "message user";
    userMsg.textContent = "Вы: " + question;
    chatBox.appendChild(userMsg);

    fetch("/chat", {
    method: "POST",
    headers: {
        "Content-Type": "application/x-www-form-urlencoded"
    },
    body: "question=" + encodeURIComponent(question)
    })
    .then(response => response.json())
    .then(data => {
        const botMsg = document.createElement("div");
        botMsg.className = "message bot";
        botMsg.textContent = "🤖 Ассистент: " + data.answer;
        chatBox.appendChild(botMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    // Очистка поля ввода
    document.getElementById("question").value = "";
});