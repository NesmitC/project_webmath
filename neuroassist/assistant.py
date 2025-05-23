# neuroassist/assistant.py

import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv


class CompanyAssistant:
    def __init__(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # корень проекта
        env_path = os.path.join(project_root, 'instance', '.env')

        # Загружаем .env по указанному пути
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            raise FileNotFoundError(f".env файл не найден по пути: {env_path}")

        self.api_key = os.getenv("HUGGINGFACE_API_KEY")

        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY не найден в .env")

        self.model_name = "Qwen/Qwen2.5-Coder-32B-Instruct"
        self.client = InferenceClient(api_key=self.api_key)

    def find_answer(self, question):
        """Запрашивает ответ у модели ИИ"""
        if not question or not isinstance(question, str):
            return "Пожалуйста, задайте ваш вопрос."

        try:
            response = self.client.chat_completion(
                model=self.model_name,
                messages=[{"role": "user", "content": question}]
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Ошибка при обращении к модели: {str(e)}"