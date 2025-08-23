// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // === Находим элементы ===
    const assistantWindow = document.getElementById('assistant-window');
    const toggleBtn = document.getElementById('assistant-toggle');
    const closeBtn = document.getElementById('close-chat');
    const clearBtn = document.getElementById('clear-chat');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');

    // === Если элементов нет — выходим ===
    if (!assistantWindow || !toggleBtn || !closeBtn || !chatMessages || !userInput || !sendButton) {
        return;
    }

    let isSending = false; // Защита от двойной отправки

    // === По умолчанию: окно видно, аватар скрыт ===
    toggleBtn.classList.add('hidden');

    // === Клик по крестику → скрываем окно, показываем аватар ===
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        assistantWindow.classList.add('hidden');
        toggleBtn.classList.remove('hidden');
    });

    // === Клик по аватару → показываем окно, скрываем аватар ===
    toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        assistantWindow.classList.remove('hidden');
        toggleBtn.classList.add('hidden');
        userInput.focus();
        loadChatHistory();
    });

    // === При открытии — фокус и загрузка ===
    const focusAndLoad = () => {
        if (!assistantWindow.classList.contains('hidden')) {
            userInput.focus();
            loadChatHistory();
        }
    };

    focusAndLoad();
    assistantWindow.addEventListener('transitionend', focusAndLoad);

    // === Отправка сообщения ===
    function sendMessage() {
        const question = userInput.value.trim();
        if (!question || isSending) return;

        isSending = true;
        addMessage('user', question);
        userInput.value = '';
        saveChatHistory();

        const typing = addMessage('bot', 'Печатаю...');

        fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        })
            .then(r => r.json())
            .then(data => {
                typing.remove();
                addMessage('bot', data.answer || 'Извините, не удалось получить ответ.');
                saveChatHistory();
            })
            .catch(err => {
                console.error('Chat error:', err);
                typing.remove();
                addMessage('bot', 'Ошибка подключения. Попробуйте позже.');
            })
            .finally(() => {
                isSending = false;
            });
    }

    // === Обработчики отправки ===
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // === Добавление сообщения ===
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = sender === 'user' ? 'flex justify-end' : 'flex justify-start';

        const bubbleClass = sender === 'user'
            ? 'bg-indigo-600 text-white rounded-lg px-4 py-2 max-w-xs text-sm'
            : 'bg-white border border-gray-200 rounded-lg px-4 py-2 max-w-xs text-sm shadow-sm';

        messageDiv.innerHTML = `<div class="${bubbleClass}">${text}</div>`;
        chatMessages.appendChild(messageDiv);
        onChatUpdate(); // Обновляем высоту
        return messageDiv;
    }

    // === Сохранение истории (в сессии) ===
    function saveChatHistory() {
        const messages = [];
        Array.from(chatMessages.children).forEach(msgEl => {
            const isUser = msgEl.querySelector('.bg-indigo-600') !== null;
            const text = msgEl.querySelector('div').innerText;
            messages.push({ sender: isUser ? 'user' : 'bot', text });
        });
        sessionStorage.setItem('neurochat-history', JSON.stringify(messages));
    }

    // === Загрузка истории ===
    function loadChatHistory() {
        const saved = sessionStorage.getItem('neurochat-history');
        const hasSeenGreeting = sessionStorage.getItem('neurochat-greeting-shown');

        chatMessages.innerHTML = '';

        let messages = [];
        if (saved) {
            try {
                messages = JSON.parse(saved);
                messages.forEach(({ sender, text }) => {
                    addMessage(sender, text);
                });
            } catch (e) {
                console.error('Failed to load chat history:', e);
            }
        }

        // Показываем приветствие, если чат пуст и ещё не показывали
        if (messages.length === 0 && !hasSeenGreeting) {
            showTypingAndGreet();
        }
    }


    // === Эффект печати при приветствии ===
    function showTypingAndGreet() {
        const typing = addMessage('bot', 'Печатаю...');

        setTimeout(() => {
            typing.remove();
            const fullText = 'Привет! Я здесь, чтобы помочь.';
            const botMessage = addMessage('bot', '');

            let i = 0;
            const typingInterval = setInterval(() => {
                if (i < fullText.length) {
                    botMessage.querySelector('div').innerText = fullText.slice(0, i + 1);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    i++;
                } else {
                    clearInterval(typingInterval);
                    saveChatHistory();
                }
            }, 50);
        }, 1200);
    }

    // === Кнопка "Очистить чат" ===
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            chatMessages.innerHTML = '';
            sessionStorage.removeItem('neurochat-history');
            sessionStorage.removeItem('neurochat-greeting-shown');
            showTypingAndGreet();
        });
    }

    // === Динамическое изменение высоты чата: высота = ширина × 2 ===
    function resizeChat() {
        const container = chatMessages;
        const parent = container.parentElement;

        const width = container.clientWidth;
        const maxHeight = width * 2;
        const availableHeight = parent.clientHeight - 130;
        const finalMaxHeight = Math.min(maxHeight, availableHeight, 600);

        container.style.height = 'auto';
        container.style.maxHeight = 'none';

        const contentHeight = container.scrollHeight;
        const minHeight = 80;

        let newHeight = Math.max(contentHeight, minHeight);

        if (newHeight > finalMaxHeight) {
            newHeight = finalMaxHeight;
            container.style.overflowY = 'auto';
        } else {
            container.style.overflowY = 'hidden';
        }

        container.style.height = `${newHeight}px`;
        container.style.maxHeight = `${finalMaxHeight}px`;
        container.scrollTop = container.scrollHeight;
    }

    // === Обновление высоты чата ===
    function onChatUpdate() {
        setTimeout(resizeChat, 50);
    }

    // === Инициализация высоты при загрузке ===
    onChatUpdate();
});

// =============================================
// Определим, авторизован ли пользователь
// Вариант 1: через глобальную переменную из шаблона
const isUserAuthenticated = window.currentUser?.isAuthenticated || false;

// Вариант 2: если нет — можно не передавать, но лучше передать
fetch('/assistant/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: userInput.value.trim(),
        is_authenticated: window.currentUser?.isAuthenticated || false
    })
})