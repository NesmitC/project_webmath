# neuroassist/assistant.py

import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
import markdown2
from bs4 import BeautifulSoup
import re
from rag import KnowledgeSearch

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CompanyAssistant:
    def __init__(self):
        # Получаем текущую директорию (где находится assistant.py)
        current_dir = os.path.dirname(__file__)
        # Поднимаемся на уровень выше (в корень проекта)
        project_root = os.path.abspath(os.path.join(current_dir, ".."))

        # Путь к .env
        env_path = os.path.join(project_root, "instance", ".env")
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            raise FileNotFoundError(f".env файл не найден по пути: {env_path}")

        # Путь к базе знаний
        self.file_path = os.path.join(project_root, "data", "rus", "ege.txt")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Файл базы знаний не найден: {self.file_path}")

        # Загружаем RAG-поиск с указанием точного пути
        self.kb_search = KnowledgeSearch(self.file_path)

        # API ключ для DeepSeek
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в .env")

        # Подключение к модели
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com "
        )


    def find_in_local_db(self, question):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.full_text = f.read()

            sections = self.full_text.split("# Конец ")

            for section in sections:
                if "задание 13" in question.lower():
                    if "егэ задание 13" in section or "# задание 13" in section.lower():
                        print("[DEBUG] Используется контекст из Задания 13")
                        return self.extract_content(section)

                elif "задание 12" in question.lower():
                    if "егэ задание 12" in section or "# задание 12" in section.lower():
                        print("[DEBUG] Используется контекст из Задания 12")
                        return self.extract_content(section)

            print("[DEBUG] Контекст не найден → стандартный поиск")
            paragraphs = self.full_text.split('\n\n')
            for paragraph in paragraphs:
                if any(word in paragraph.lower() for word in question.split()):
                    return paragraph.strip()

            return None

        except Exception as e:
            print(f"[ERROR] Причина ошибки при поиске: {str(e)}")
            return None


    def extract_content(self, section):
        """Извлекает полезную часть раздела"""
        lines = section.splitlines()
        content_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        return "\n".join(content_lines).strip()


    def ask_model(self, question):
        """Запрашивает ответ у модели DeepSeek"""

        messages = [
            {"role": "system", "content": "Вы — преподаватель ЕГЭ. "
                                         "Используйте только информацию из переданного контекста. "
                                         "Если информации нет — скажите об этом."},
            {"role": "user", "content": question}
        ]

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=500,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Ошибка: {str(e)}"


    def find_answer(self, question):
        """Основной метод: сначала ищем через FAISS, потом через ключевые слова"""
        print(f"[DEBUG] Получен вопрос: {question[:50]}...")

        # Семантический поиск через FAISS
        rag_context = self.kb_search.search(question)
        if rag_context:
            print("[DEBUG] Контекст найден через FAISS")
            return self.ask_model_with_context([
                {"role": "system", "content": "Вы — преподаватель ЕГЭ. "
                                            "Используйте только информацию из контекста"},
                {"role": "user", "content": f"Контекст:\n{rag_context}\n\nВопрос:\n{question}"}
            ])

        # Резервный поиск по ключевым словам
        local_answer = self.find_in_local_db(question)
        if local_answer:
            print("[DEBUG] Найдено через find_in_local_db()")
            return local_answer

        # Если ничего не найдено → обращение к модели без контекста
        return self.ask_model(question)


    def ask_model_with_context(self, messages):
        """Отправляет запрос в модель с явным указанием контекста"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=500,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] При обращении к модели: {str(e)}")
            return "Не удалось получить ответ от модели"


    def clean_markdown(text):
        # Убираем ** и __
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        return text.strip()


    def markdown_to_safe_html(self, text):
        # Преобразуем Markdown в HTML
        html = markdown2.markdown(text)

        # Очищаем потенциально опасные теги через BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        allowed_tags = ['p', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'code', 'pre']
        for tag in soup.find_all(True):
            if tag.name not in allowed_tags:
                tag.unwrap()

        return str(soup)