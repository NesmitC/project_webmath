import os
import json
from pathlib import Path
from difflib import get_close_matches

class CompanyAssistant:
    def __init__(self):
        self.knowledge = self._load_knowledge()
        self.intents = self._load_intents()

    def _load_knowledge(self):
        knowledge = {}
        base_dir = Path(__file__).parent.parent / "knowledge_base"
        
        for file in base_dir.glob("*.txt"):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            knowledge[file.stem] = content
        return knowledge

    def _load_intents(self):
        with open(Path(__file__).parent / "intents.json", 'r', encoding='utf-8') as f:
            return json.load(f)

    def find_answer(self, question):
        # Сначала проверяем точные совпадения
        for intent in self.intents["intents"]:
            if question.lower() in intent["patterns"]:
                return intent["responses"][0]
        
        # Ищем в базе знаний
        for category, text in self.knowledge.items():
            if question.lower() in text.lower():
                relevant_part = next(
                    (line for line in text.split('\n') 
                     if question.lower() in line.lower()), 
                    None
                )
                return f"В базе знаний найдено: {relevant_part}"
        
        # Если ничего не найдено
        return "Уточните вопрос. Я могу рассказать о наших продуктах, ценах и сроках."