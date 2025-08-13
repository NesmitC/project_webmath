// static/js/examenator.js

// Универсальный рендер заданий
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

    // Рендер задания 7: список с красной строкой + одно текстовое поле
    renderTask7(inputId) {
        const lines = this.splitLines();
        let html = '<div class="task-list">';
        lines.forEach(line => {
            const highlighted = this.highlightCaps(line);
            html += `<p>${highlighted}</p>`;
        });
        html += '</div>';

        // Текстовое поле для ответа
        html += `
            <div class="mt-4">
                <label class="block font-medium mb-2">Ответ:</label>
                <input type="text" id="${inputId}" class="border p-2 w-full rounded" placeholder="Введите слово" />
            </div>
        `;

        this.container.innerHTML = html;
    }

    // Рендер выбор нескольких (через |)
    renderCheckbox() {
        const options = this.text.split('|');
        let html = '<div class="checkbox-options">';
        options.forEach((opt, i) => {
            html += `
                <label class="block mt-2">
                    <input type="checkbox" value="${i}" name="${this.container.id}" class="mr-2">
                    ${i + 1}) ${opt}
                </label>`;
        });
        html += '</div>';
        this.container.innerHTML = html;
    }

    // Рендер соответствия
    renderMatch() {
        const parts = this.text.split('|');
        const labels = ['А', 'Б', 'В', 'Г', 'Д'];
        let html = '<div class="match-options">';
        for (let i = 0; i < Math.min(labels.length, parts.length); i++) {
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
            case 'checkbox':
                this.renderCheckbox();
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
    console.log("✅ Данные загружены:", examenatorData);

    function loadTest(type) {
        const container = document.getElementById(`${type}-questions`);
        const test = examenatorData[type];

        if (!test) {
            container.innerHTML = '<p class="text-red-500">❌ Ошибка загрузки теста.</p>';
            return;
        }

        let questionHtml = '';

        test.questions.forEach(q => {
            const questionContainerId = `question-${q.id}`;
            const label = q.question || `Задание ${q.id}`;

            questionHtml += `
                <div class="mb-6 p-4 border rounded bg-white">
                    <p class="font-semibold mb-3">${q.id}. ${label}</p>
                    <div id="${questionContainerId}" class="question-container mt-2"></div>
                </div>
            `;
        });

        container.innerHTML = questionHtml;

        // Рендерим каждый вопрос
        test.questions.forEach(q => {
            const containerEl = document.getElementById(`question-${q.id}`);
            if (!containerEl) return;

            new ExamRenderer(
                containerEl,
                q.question_text || q.question,
                q.type
            ).render();
        });
    }

    testTypes.forEach(loadTest);

    window.checkAllTests = function () {
        let correct = 0;
        let total = 0;

        testTypes.forEach(type => {
            const test = examenatorData[type];
            if (!test) return;

            test.questions.forEach(q => {
                total++;

                if (q.type === "task7") {
                    const val = document.getElementById(`input-${q.id}`)?.value.trim().toLowerCase() || '';
                    const expected = q.correct_answer?.toLowerCase() || '';
                    if (val === expected) correct++;
                }

                else if (q.type === "input") {
                    const val = document.getElementById(`input-${q.id}`)?.value.trim().toLowerCase() || '';
                    const expected = q.correct_answer?.toLowerCase() || '';
                    if (val === expected) correct++;
                }

                else if (q.type === "checkbox") {
                    const checked = Array.from(document.querySelectorAll(`input[name="question-${q.id}"]:checked`))
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
                    const val = document.getElementById(`input-${q.id}`)?.value || '';
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
            body: JSON.stringify({ test_type: type, score: correct, total: total })
        }).catch(err => console.error("❌ Ошибка отправки:", err));
    };
});