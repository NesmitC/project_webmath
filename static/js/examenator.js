// static/js/examenator.js

// Универсальный рендер для сложных заданий (task7, match)
class ExamRenderer {
    constructor(container, text, type = 'default') {
        this.container = container;
        this.text = text;
        this.type = type;
    }

    splitLines() {
        return this.text.split('\n').filter(line => line.trim() !== '');
    }

    highlightCaps(text) {
        return text.replace(/([А-ЯЁ]{2,}(?:\s+[А-ЯЁ]{2,})*)/g, '<span class="highlighted-word">$1</span>');
    }

    renderTask7(inputId) {
        const lines = this.splitLines();
        let html = '<div class="task-list">';
        lines.forEach(line => {
            const highlighted = this.highlightCaps(line);
            html += `<p>${highlighted}</p>`;
        });
        html += '</div>';
        html += `<div class="mt-4"><label class="block font-medium mb-2">Ответ:</label><input type="text" id="${inputId}" class="border p-2 w-full rounded" placeholder="Введите слово" /></div>`;
        this.container.innerHTML = html;
    }

    renderMatch() {
        const parts = this.text.split('|');
        const labels = ['А', 'Б', 'В'];
        let html = '<div class="match-options">';
        for (let i = 0; i < labels.length; i++) {
            html += `
                <div class="mb-3">
                    <span class="font-semibold">${labels[i]}</span>
                    <select name="${this.container.id}-pair${i}" class="border p-1 ml-2 rounded">
                        <option value="">—</option>
                        ${parts.map((_, idx) => `<option value="${idx + 1}">${idx + 1}</option>`).join('')}
                    </select>
                    <span class="ml-2">${parts[i]}</span>
                </div>`;
        }
        html += '</div>';
        this.container.innerHTML = html;
    }

    render() {
        const baseId = this.container.id.replace('question-', '');
        const inputId = `input-${baseId}`;

        switch (this.type) {
            case 'task7':
                this.renderTask7(inputId);
                break;
            case 'match':
                this.renderMatch();
                break;
            default:
                this.container.textContent = this.text;
        }
    }
}

// Основной код
document.addEventListener('DOMContentLoaded', () => {
    if (!window.examenatorData) {
        console.error("❌ Данные экзаменатора не загружены");
        return;
    }

    const { examenatorData, testTypes } = window;

    function loadTest(type) {
        const container = document.getElementById(`${type}-questions`);
        const test = examenatorData[type];

        if (!test) {
            container.innerHTML = '<p class="text-red-500">❌ Ошибка загрузки теста.</p>';
            return;
        }

        let questionHtml = '';

        test.questions.forEach(q => {
            const inputId = `${type}-q${q.id}`;
            const questionContainerId = `question-${q.id}`;

            if (q.type === "input") {
                questionHtml += `
          <div class="mb-6 p-4 border rounded bg-white">
            <p class="font-semibold mb-3">${q.id}. ${q.question}</p>
            <input type="text" id="${inputId}" class="border p-2 w-full rounded" placeholder="Введите ответ" />
          </div>`;
            }

            else if (q.type === "checkbox") {
                const options = Array.isArray(q.options) ? q.options :
                    typeof q.options === 'string' ? q.options.split('|') :
                        [];
                let optionsHtml = '';
                options.forEach((opt, i) => {
                    optionsHtml += `
            <label class="block mt-2">
                <input type="checkbox" value="${i}" name="${inputId}" class="mr-2">
                ${opt}
            </label>`;
                });

                questionHtml += `
          <div class="mb-6 p-4 border rounded bg-white">
            <p class="font-semibold mb-3">${q.id}. ${q.question}</p>
            <div class="checkbox-options">${optionsHtml}</div>
          </div>`;
            }

            else if (q.type === "textarea") {
                questionHtml += `
          <div class="mb-6 p-4 border rounded bg-white">
            <p class="font-semibold mb-3">${q.id}. ${q.question}</p>
            <small class="text-gray-500 block mb-2">${q.info || 'Ответ должен быть не менее 150 слов.'}</small>
            <textarea id="${inputId}" rows="5" class="border p-2 w-full rounded"></textarea>
          </div>`;
            }

            // Для task7 и match — контейнер, рендерим отдельно
            else if (['task7', 'match'].includes(q.type)) {
                questionHtml += `
          <div class="mb-6 p-4 border rounded bg-white">
            <p class="font-semibold mb-3">${q.id}. ${q.question}</p>
            <div id="${questionContainerId}" class="question-container mt-2"></div>
          </div>`;
            }

            else if (q.type === "short-answer") {
                questionHtml += `
        <div class="mb-6 p-4 border rounded bg-white">
            <p class="font-semibold mb-3">${q.id}. ${q.question}</p>
            <input 
                type="text" 
                id="${inputId}" 
                class="border p-2 w-full rounded mt-2" 
                placeholder="Введите ответ (например: их, 34)" />
        </div>`;
            }

            // Для обычных текстов
            else {
                questionHtml += `
          <div class="mb-6 p-4 border rounded bg-white">
            <p class="font-semibold mb-3">${q.id}. ${q.question}</p>
          </div>`;
            }
        });

        container.innerHTML = questionHtml;

        // Теперь рендерим сложные задания
        test.questions.forEach(q => {
            if (['task7', 'match'].includes(q.type)) {
                const containerEl = document.getElementById(`question-${q.id}`);
                if (containerEl) {
                    new ExamRenderer(
                        containerEl,
                        q.question_text || q.question,
                        q.type
                    ).render();
                }
            }
        });
    }

    // Загружаем все тесты
    testTypes.forEach(loadTest);

    // Функция проверки
    window.checkAllTests = function () {
        let correct = 0;
        let total = 0;

        testTypes.forEach(type => {
            const test = examenatorData[type];
            if (!test) return;

            test.questions.forEach(q => {
                const inputId = `${type}-q${q.id}`;
                total++;

                if (q.type === "input") {
                    const val = document.getElementById(inputId)?.value.trim().toLowerCase() || '';
                    const expected = q.correct_answer?.toLowerCase() || '';
                    if (val === expected) correct++;
                }

                else if (q.type === "task7") {
                    const val = document.getElementById(`input-${q.id}`)?.value.trim().toLowerCase() || '';
                    const expected = q.correct_answer?.toLowerCase() || '';
                    if (val === expected) correct++;
                }

                else if (q.type === "checkbox") {
                    const checked = Array.from(document.querySelectorAll(`input[name="${inputId}"]:checked`))
                        .map(el => parseInt(el.value));
                    const correctAnswers = q.correct_answer
                        ?.split(',')
                        .map(s => parseInt(s.trim())) || [];
                    const isCorrect = checked.length === correctAnswers.length &&
                        checked.every(v => correctAnswers.includes(v)) &&
                        correctAnswers.every(v => checked.includes(v));
                    if (isCorrect) correct++;
                }

                else if (q.type === "match") {
                    const userAnswers = [];
                    for (let i = 0; i < 3; i++) {
                        const val = document.querySelector(`[name="question-${q.id}-pair${i}"]`)?.value;
                        userAnswers.push(val || '');
                    }
                    const correctAnswer = q.correct_answer?.split(',').map(s => s.trim()) || [];
                    if (userAnswers.join(',') === correctAnswer.join(',')) correct++;
                }

                else if (q.type === "textarea") {
                    const val = document.getElementById(inputId)?.value || '';
                    const wordCount = val.trim().split(/\s+/).filter(w => w.length > 0).length;
                    if (wordCount >= 150) correct++;
                }
            });
        });

        document.getElementById('score').textContent = correct;
        document.getElementById('max-score').textContent = total;
        document.getElementById('result').classList.remove('hidden');

        const levelText = correct / total > 0.8 ? "Высокий уровень" :
            correct / total > 0.6 ? "Средний уровень" : "Начальный уровень";
        document.getElementById('level').textContent = `Уровень: ${levelText}`;

        // Отправляем результат
        fetch('/submit-test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test_type: 'all', score: correct, total: total })
        }).catch(err => console.error("❌ Ошибка отправки:", err));
    };
});