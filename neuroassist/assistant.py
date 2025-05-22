import json
import logging
from pathlib import Path
from difflib import get_close_matches
from typing import Dict, List, Optional
from datetime import datetime  # Добавлен правильный импорт

class CompanyAssistant:
    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """
        Инициализация нейроассистента
        
        Args:
            knowledge_base_dir (str): Папка с базами знаний. По умолчанию "knowledge_base".
        """
        self.logger = self._setup_logger()
        self.knowledge_base = Path(__file__).parent.parent / knowledge_base_dir
        self.intents = self._load_intents()
        self._validate_structure()

    def _setup_logger(self):
        """Настройка системы логирования"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Логи в файл
        file_handler = logging.FileHandler(
            Path(__file__).parent / 'assistant.log'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Вывод в консоль
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        return logger

    def _validate_structure(self):
        """Проверка корректности структуры файлов"""
        required_files = {
            'intents.json': "Файл шаблонов ответов",
            'products.txt': "База продуктов",
            'policies.txt': "Политики компании"
        }
        
        for file, description in required_files.items():
            if not (Path(__file__).parent / file).exists():
                self.logger.warning(f"Отсутствует {description}: {file}")

    def _load_intents(self) -> Dict:
        """Загрузка файла с шаблонами ответов"""
        intents_path = Path(__file__).parent / "intents.json"
        try:
            with open(intents_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки intents.json: {str(e)}")
            return {"intents": []}

    def _load_knowledge_file(self, filename: str) -> Optional[str]:
        """
        Безопасная загрузка файла знаний
        
        Args:
            filename (str): Имя файла (без пути)
            
        Returns:
            Optional[str]: Содержимое файла или None при ошибке
        """
        try:
            filepath = (self.knowledge_base / filename).resolve()
            
            # Защита от Path Traversal
            if not filepath.parent.samefile(self.knowledge_base.resolve()):
                raise ValueError(f"Недопустимый путь: {filename}")
                
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger.info(f"Загружен файл: {filename} ({len(content)} символов)")
                return content
        except Exception as e:
            self.logger.error(f"Ошибка загрузки {filename}: {str(e)}")
            return None

    def _find_in_knowledge(self, question: str) -> Optional[str]:
        """Поиск ответа в базах знаний"""
        knowledge_files = ['products.txt', 'policies.txt']
        
        for file in knowledge_files:
            content = self._load_knowledge_file(file)
            if not content:
                continue
                
            for line in content.split('\n'):
                line = line.strip()
                if line and question.lower() in line.lower():
                    return line
        return None

    def _find_in_intents(self, question: str) -> Optional[str]:
        """Поиск по шаблонным ответам"""
        question_lower = question.lower()
        
        # 1. Точное совпадение
        for intent in self.intents.get("intents", []):
            if question_lower in map(str.lower, intent.get("patterns", [])):
                return intent.get("responses", [""])[0]
        
        # 2. Похожие вопросы
        all_patterns = [
            p for intent in self.intents.get("intents", []) 
            for p in intent.get("patterns", [])
        ]
        
        matches = get_close_matches(question_lower, all_patterns, n=1, cutoff=0.6)
        if matches:
            matched_question = matches[0]
            for intent in self.intents.get("intents", []):
                if matched_question in intent.get("patterns", []):
                    return intent.get("responses", [""])[0]
        
        return None

    def find_answer(self, question: str) -> str:
        """
        Основной метод для получения ответа
        
        Args:
            question (str): Вопрос пользователя
            
        Returns:
            str: Ответ ассистента
        """
        if not isinstance(question, str) or not question.strip():
            return "Пожалуйста, задайте корректный вопрос"
        
        start_time = datetime.now()
        self.logger.info(f"Обработка вопроса: '{question}'")
        
        try:
            # 1. Поиск в шаблонных ответах
            intent_answer = self._find_in_intents(question)
            if intent_answer:
                self.logger.info(f"Найден шаблонный ответ за {datetime.now() - start_time}")
                return intent_answer
            
            # 2. Поиск в базах знаний
            knowledge_answer = self._find_in_knowledge(question)
            if knowledge_answer:
                self.logger.info(f"Найден ответ в БЗ за {datetime.now() - start_time}")
                return f"Согласно нашей базе знаний: {knowledge_answer}"
            
            # 3. Ответ по умолчанию
            default_answer = ("Я не нашел точного ответа. "
                            "Попробуйте переформулировать вопрос.")
            self.logger.warning(f"Ответ не найден для вопроса: '{question}'")
            return default_answer
                    
        except Exception as e:
            self.logger.error(f"Ошибка: {str(e)}", exc_info=True)
            return "Произошла внутренняя ошибка. Пожалуйста, попробуйте позже."

    def add_knowledge(self, filename: str, content: str) -> bool:
        """
        Добавление новых знаний
        
        Args:
            filename (str): Имя файла (products.txt/policies.txt)
            content (str): Новое содержимое
            
        Returns:
            bool: Успешность операции
        """
        try:
            if filename not in ['products.txt', 'policies.txt']:
                raise ValueError("Недопустимое имя файла")
                
            filepath = self.knowledge_base / filename
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n# Добавлено {datetime.now()}\n{content}\n")
            self.logger.info(f"Добавлены данные в {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления знаний: {str(e)}")
            return False