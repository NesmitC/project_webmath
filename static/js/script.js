document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("askForm");
    const responseBox = document.getElementById("response");

    if (!form || !responseBox) {
        console.error("Элементы формы/ответа не найдены");
        return;
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const questionInput = form.querySelector("textarea[name='question']");
        const question = questionInput?.value.trim();

        if (!question) return;

        responseBox.innerHTML += `<p class="message user"><b>Вы:</b> ${question}</p>`;
        const loadingMsg = `<p class="message bot" id="assistant-response"><b>🤖:</b> <i>Думаю...</i></p>`;
        responseBox.innerHTML += loadingMsg;

        try {
            const res = await fetch("/assistant", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });

            const data = await res.json();

            // Обновляем только последнее сообщение
            const assistantDiv = document.getElementById("assistant-response");
            if (assistantDiv) {
                assistantDiv.outerHTML = `<p><b>🤖 Ассистент:</b> ${data.answer}</p>`;
            }

        } catch (error) {
            const assistantDiv = document.getElementById("assistant-response");
            if (assistantDiv) {
                assistantDiv.outerHTML = `<p style="color:red;"><b>Ошибка:</b> ${error.message}</p>`;
            }
        }

        // Очистка поля ввода
        if (questionInput) questionInput.value = "";
    });
});