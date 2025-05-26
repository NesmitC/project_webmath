# здесь будут модели

# models.py

from transformers import pipeline

chatbot = pipeline("text-generation", model="gpt2")  # или твоя модель

def get_response(question: str) -> str:
    result = chatbot(question, max_length=50, num_return_sequences=1)
    return result[0]['generated_text']

