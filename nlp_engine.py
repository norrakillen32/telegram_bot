import json
import re
from typing import Tuple, Optional, List, Dict
import difflib
from datetime import datetime

class SimpleKnowledgeBase:
    """Упрощенная база знаний для Vercel"""
    
    def __init__(self):
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Загрузка данных из knowledge_base.json"""
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ База знаний загружена: {len(self.data)} записей")
        except Exception as e:
            print(f"❌ Ошибка загрузки базы знаний: {e}")
            self.data = []
    
    def normalize_text(self, text: str) -> str:
        """Нормализация текста"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def find_answer(self, question: str, threshold: float = 0.4) -> Tuple[Optional[str], float]:
        """Поиск ответа в базе знаний"""
        if not self.data:
            return None, 0.0
        
        question_norm = self.normalize_text(question)
        best_match = None
        best_score = 0.0
        
        for item in self.data:
            item_question = item.get('question', '')
            item_norm = self.normalize_text(item_question)
            
            # Простое сравнение строк
            score = difflib.SequenceMatcher(None, question_norm, item_norm).ratio()
            
            # Дополнительный поиск по ключевым словам
            if score < threshold:
                # Если прямое сравнение не сработало, проверяем вхождение
                if item_question.lower() in question.lower() or question.lower() in item_question.lower():
                    score = 0.6  # Средняя уверенность
            
            if score > best_score:
                best_score = score
                best_match = item.get('answer')
        
        return best_match, best_score

class SimpleNLPSystem:
    """Упрощенная NLP-система для Vercel"""
    
    def __init__(self):
        self.kb = SimpleKnowledgeBase()
        print("🤖 Упрощенная NLP-система инициализирована для Vercel")
    
    def search(self, question: str) -> str:
        """Поиск ответа на вопрос"""
        answer, confidence = self.kb.find_answer(question)
        
        if answer and confidence >= 0.4:
            return f"{answer}\n\n<i>(Найдено с уверенностью {confidence:.0%})</i>"
        
        # Fallback ответ
        return f"🤔 <b>По запросу '{question}' точного ответа не найдено.</b>\n\nПопробуйте переформулировать вопрос или обратиться к документации 1С."

# Глобальный экземпляр
nlp_simple = SimpleNLPSystem()

# Функция для бота
def search_answer(question: str) -> str:
    return nlp_simple.search(question)
