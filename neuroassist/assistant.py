# neuroassist/assistant.py

import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import logging

# Логирование для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CompanyAssistant:
    def __init__(self):
        # Явно указываем путь к .env
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env_path = os.path.join(project_root, 'instance', '.env')

        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            raise FileNotFoundError(f".env файл не найден по пути: {env_path}")

        self.api_key = os.getenv("HUGGINGFACE_API_KEY")

        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY не найден в .env")

        # Используем модель, которая точно доступна всем ↓
        self.model_name = "HuggingFaceH4/zephyr-7b-beta"

        # Добавляем таймаут
        self.client = InferenceClient(api_key=self.api_key, timeout=10)

    def find_answer(self, question):
        """Запрашивает ответ у модели ИИ"""
        if not question or not isinstance(question, str):
            return "Пожалуйста, задайте ваш вопрос."

        logger.debug(f"Отправка вопроса: {question[:50]}...")

        try:
            response = self.client.chat_completion(
                model=self.model_name,
                messages=[{"role": "user", "content": question}],
                max_tokens=200
            )
            answer = response.choices[0].message.content.strip()
            logger.debug("Ответ получен")
            return answer

        except Exception as e:
            logger.error(f"Ошибка при обращении к модели: {str(e)}")
            return f"Ошибка: {str(e)}"