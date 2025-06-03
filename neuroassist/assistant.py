# neuroassist/assistant.py

from rag.rag import KnowledgeSearch  # ✅ Исправленный импорт
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class CompanyAssistant:
    def __init__(self):
        # Путь к корневой директории проекта
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # Загрузка .env из instance/
        env_path = os.path.join(project_root, "instance", ".env")
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            raise FileNotFoundError(f".env файл не найден по пути: {env_path}")

        # Путь к базе знаний
        self.file_path = os.path.join(project_root, "data", "rus", "ege.txt")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Файл базы знаний не найден: {self.file_path}")

        # Инициализация RAG поиска
        self.kb_search = KnowledgeSearch(self.file_path)

        # Токен DeepSeek
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в .env")

        # Подключение к модели
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com" 
        )

    def find_answer(self, question):
        """Основной метод: сначала ищем через FAISS, потом через ключевые слова"""
        logger.info(f"Получен вопрос: {question[:50]}...")

        # Семантический поиск через FAISS
        rag_context = self.kb_search.search(question)
        if rag_context:
            logger.info("Контекст найден через FAISS")
            return self.ask_model_with_context(rag_context, question)

        # Резервный поиск по ключевым словам
        local_answer = self.find_in_local_db(question)
        if local_answer:
            logger.info("Найдено через find_in_local_db()")
            return local_answer

        # Если ничего не найдено → обращение к модели без контекста
        return self.ask_model(question)

    def ask_model_with_context(self, context, question):
        """Запрашивает ответ у модели DeepSeek с использованием контекста"""
        messages = [
            {"role": "system", "content": "Вы — преподаватель ЕГЭ. "
                                         "Используйте только информацию из переданного контекста. "
                                         "Если информации нет — скажите об этом."},
            {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос:\n{question}"}
        ]
        return self._get_model_response(messages)

    def ask_model(self, question):
        """Запрашивает ответ у модели DeepSeek без контекста"""
        messages = [
            {"role": "system", "content": "Вы — преподаватель ЕГЭ. "
                                         "Если не знаете точного ответа — так и скажите."},
            {"role": "user", "content": question}
        ]
        return self._get_model_response(messages)

    def _get_model_response(self, messages):
        """Общий метод для получения ответа от модели"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=500,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка при обращении к модели: {str(e)}")
            return "Не удалось получить ответ от нейроассистента."

    def find_in_local_db(self, question):
        """Резервный поиск по ключевым словам в текстовом файле"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            paragraphs = full_text.split('\n\n')
            for paragraph in paragraphs:
                if any(word.lower() in paragraph.lower() for word in question.split()):
                    return paragraph.strip()

            return None
        except Exception as e:
            logger.error(f"Ошибка при поиске в БД: {str(e)}")
            return None