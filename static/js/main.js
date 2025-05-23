console.log("main.js загружен");


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

document.getElementById("chat-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    const question = document.getElementById("question").value.trim();
    const chatBox = document.getElementById("chat-box");

    if (!question) return;

    // Показываем вопрос пользователя
    chatBox.innerHTML += `<div class="user"><b>Вы:</b> ${question}</div>`;
    // Показываем "ждите..."
    const loadingMsg = `<div class="bot"><b>🤖 Ассистент:</b> <i>Думаю...</i></div>`;
    chatBox.innerHTML += loadingMsg;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const res = await fetch("/assistant", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        const data = await res.json();

        // Обновляем последнее сообщение
        chatBox.innerHTML = chatBox.innerHTML.replace('Думаю...', data.answer);

    } catch (error) {
        chatBox.innerHTML = chatBox.innerHTML.replace('Думаю...', 'Ошибка подключения');
        console.error("Fetch error:", error);
    }
});