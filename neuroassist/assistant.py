# neuroassist/assistant.py

import os
from huggingface_hub import InferenceClient
from openai import OpenAI
from dotenv import load_dotenv
import logging
import markdown2
from bs4 import BeautifulSoup
import re



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CompanyAssistant:
    def __init__(self):
        # Загружаем .env
        project_root = os.path.abspath(os.path.dirname(__file__))
        env_path = os.path.join(project_root, '..', 'instance', '.env')

        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            raise FileNotFoundError(f".env файл не найден по пути: {env_path}")

        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в .env")

        # Подключение к DeepSeek
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com "
        )

        # Путь к базе знаний
        self.file_path = os.path.join(project_root, "..", "data", "rus", "ege.txt")

    def find_in_local_db(self, question):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Делим по заданиям
            sections = text.split("# Конец ")
            
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
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                if any(word in paragraph.lower() for word in question.split()):
                    return paragraph.strip()

            return None

        except Exception as e:
            print(f"[ERROR] Причина ошибки: {str(e)}")
            return None


    def extract_content(self, section):
        """Извлекает полезную часть раздела"""
        lines = section.splitlines()
        content_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        return "\n".join(content_lines).strip()



    def ask_model(self, question):
        """Запрашивает ответ у модели DeepSeek"""

        messages = [
            {"role": "system", "content": "Вы — преподаватель математики и русского языка ЕГЭ. Будьте приветливы"
                                        "Отвечайте чётко, по делу, без лишних примеров. "
                                        "Если вопрос не связан с ЕГЭ — скажите, что вы специализируетесь только на ЕГЭ"},
            {"role": "user", "content": question}
        ]

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=300,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Ошибка: {str(e)}"


    def find_answer(self, question):
        """Основной метод: сначала ищем локально, потом обращаемся к модели"""
        local_answer = self.find_in_local_db(question)
        if local_answer:
            return local_answer

        return self.ask_model(question)
    

def clean_markdown(text):
    # Сначала очистим от лишних символов
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    return text.strip()

def markdown_to_safe_html(text):
    # Преобразуем Markdown в HTML
    html = markdown2.markdown(text)

    # Очищаем потенциально опасные теги через BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Разрешённые теги:
    allowed_tags = ['p', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre']
    
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()  # удаляем тег, оставляем текст

    return str(soup)