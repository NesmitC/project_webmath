# здесь будут модели

# models.py
import os


def get_response(question):
    """Ищет ответ в ege.txt"""
    project_root = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(project_root, "data", "rus", "ege.txt")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Поиск по ключевым словам
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if any(word.lower() in paragraph.lower() for word in question.split()):
                return paragraph.strip()

        return None  # Ничего не найдено

    except FileNotFoundError:
        print(f"[ERROR] Файл {file_path} не найден")
        return None
    except Exception as e:
        print(f"[ERROR] Ошибка при чтении файла: {str(e)}")
        return None


def clean_response(text):
    """Очистка и фильтрация ответа"""
    if not text:
        return "Не удалось найти информацию по вашему вопросу"
    return text.strip()