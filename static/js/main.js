document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("chat-form");
    const chatBox = document.getElementById("chat-box");

    if (!form || !chatBox) return;

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const questionInput = document.getElementById("question");
        const question = questionInput.value.trim();

        if (!question) return;

        // Показываем вопрос пользователя
        chatBox.innerHTML += `<div class="message user"><b>Вы:</b> ${question}</div>`;
        // Индикатор ожидания
        chatBox.innerHTML += `<div class="message bot"><b>🤖 Ассистент:</b> <i>Думаю...</i></div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const res = await fetch("/assistant", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });

            const data = await res.json();

            // Обновляем последнее сообщение
            const botMessages = chatBox.getElementsByClassName("bot");
            const lastMessage = botMessages[botMessages.length - 1];
            if (lastMessage) {
                lastMessage.innerHTML = `<b>🤖 Ассистент:</b> ${data.answer}`;
            }

        } catch (error) {
            const botMessages = chatBox.getElementsByClassName("bot");
            const lastMessage = botMessages[botMessages.length - 1];
            if (lastMessage) {
                lastMessage.innerHTML = `<b>🤖 Ассистент:</b> Ошибка подключения`;
            }
        }

        questionInput.value = "";
    });
});