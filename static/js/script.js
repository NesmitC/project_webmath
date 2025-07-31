// Пример: плавный скролл

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});



document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.querySelector(".chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-btn");

    // Функция добавления сообщения в чат
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message p-3 rounded-lg max-w-xs ${isUser ? "bg-indigo-600 text-white ml-auto" : "bg-gray-100 ml-2 mr-auto"
            }`;
        messageDiv.innerHTML = isUser
            ? `<strong>Вы:</strong> ${text}`
            : `<strong>Нейроучитель:</strong> ${text}`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Отправка сообщения
    function sendMessage() {
        const question = userInput.value.trim();
        if (!question) return;

        addMessage(question, true);
        userInput.value = "";

        // Отправка на сервер
        fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question })
        })
            .then(response => response.json())
            .then(data => {
                addMessage(data.answer);
            })
            .catch(err => {
                addMessage("Ошибка подключения к серверу. Попробуйте позже.");
            });
    }

    // Обработчики событий
    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});