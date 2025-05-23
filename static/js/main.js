console.log("main.js загружен");

document.getElementById("chat-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    const question = document.getElementById("question").value.trim();
    const chatBox = document.getElementById("chat-box");

    if (!question) return;

    // Отображаем вопрос пользователя
    chatBox.innerHTML += `<div class="user"><b>Вы:</b> ${question}</div>`;
    // Индикатор ожидания
    chatBox.innerHTML += `<div class="bot"><b>🤖 Ассистент:</b> <i>Думаю...</i></div>`;
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