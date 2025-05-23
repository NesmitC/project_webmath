# neuroassist/assistant.py

import os
from huggingface_hub import InferenceClient
from openai import OpenAI
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CompanyAssistant:
    def __init__(self):
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

    def find_answer(self, question):
        """Запрашивает ответ у модели DeepSeek"""
        if not question or not isinstance(question, str):
            return "Пожалуйста, задайте ваш вопрос."

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # можно попробовать deepseek-lite
                messages=[
                    {"role": "user", "content": question}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[ERROR] Не удалось получить ответ: {e}")
            return "Не удалось получить ответ от модели. Попробуйте позже."