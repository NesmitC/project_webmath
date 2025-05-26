console.log("main.js загружен");

document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('question');
    const question = input.value;

    // Показать вопрос
    const chatBox = document.getElementById('chat-box');
    const userMessage = document.createElement('p');
    userMessage.innerHTML = `<strong>Вы:</strong> ${question}`;
    chatBox.appendChild(userMessage);

    input.value = ''; // очистить

    // Отправить вопрос на сервер
    const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
    });

    const data = await response.json();
    const botMessage = document.createElement('p');
    botMessage.innerHTML = `<strong>Ассистент:</strong> ${data.answer}`;
    chatBox.appendChild(botMessage);
});
