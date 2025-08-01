// static/js/script.js

// Элементы чата
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');

// Функция добавления сообщения в чат
function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'flex justify-end' : 'flex justify-start';

    const bubbleClass = sender === 'user'
        ? 'bg-indigo-600 text-white rounded-lg px-4 py-2 max-w-xs'
        : 'bg-gray-200 text-gray-800 rounded-lg px-4 py-2 max-w-xs';

    messageDiv.innerHTML = `<div class="${bubbleClass}">${text}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Отправка сообщения
async function sendMessage() {
    const question = userInput.value.trim();
    if (!question) return;

    // Показываем сообщение пользователя
    addMessage('user', question);
    userInput.value = '';

    // Показываем "печатаю..."
    addMessage('bot', 'Печатаю...');
    const typing = chatMessages.lastChild;

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();
        typing.remove(); // Удаляем "печатаю..."
        addMessage('bot', data.answer);
    } catch (error) {
        typing.remove();
        addMessage('bot', 'Ошибка подключения. Попробуйте позже.');
    }
}

// Разрешаем отправку по Enter
if (userInput) {
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}