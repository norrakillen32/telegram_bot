import json
import re
from typing import Tuple, Optional, Dict, List, Any
import difflib

class TextPreprocessor:
    """Предобработка текста пользователя с учетом опечаток"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста: нижний регистр, удаление лишних символов"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        stop_words = {
            'как', 'где', 'что', 'кто', 'когда', 'почему', 'зачем',
            'мне', 'мной', 'меня', 'тебе', 'тобой', 'тебя',
            'свой', 'своя', 'своё', 'свои',
            'это', 'этот', 'эта', 'эти', 'этот',
            'вот', 'тут', 'там', 'здесь', 'туда',
            'очень', 'просто', 'вообще', 'совсем',
            'можно', 'нужно', 'надо', 'хочу', 'хотел'
        }
        
        words = text.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords

class FuzzySearcher:
    """Нечеткий поиск с учетом опечаток"""
    
    @staticmethod
    def fuzzy_ratio(text1: str, text2: str) -> float:
        """Улучшенный расчет схожести текстов"""
        # Приводим к нижнему регистру
        text1 = text1.lower()
        text2 = text2.lower()
        
        # 1. Базовое сравнение
        base_ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # 2. Разбиваем на слова
        words1 = text1.split()
        words2 = text2.split()
        
        # 3. Находим общие слова (даже частичные совпадения)
        common_score = 0
        for w1 in words1:
            for w2 in words2:
                # Проверяем частичное совпадение
                if w1 in w2 or w2 in w1:
                    common_score += 1
                # Проверяем похожие слова (расстояние Левенштейна)
                elif len(w1) > 3 and len(w2) > 3:
                    similarity = difflib.SequenceMatcher(None, w1, w2).ratio()
                    if similarity > 0.6:
                        common_score += similarity
        
        word_overlap = common_score / max(len(words1), len(words2), 1)
        
        # 4. Первые буквы слов
        first_letter_score = 0
        if words1 and words2:
            first_match = 0
            for i in range(min(len(words1), len(words2))):
                if words1[i][0] == words2[i][0]:
                    first_match += 1
            first_letter_score = first_match / max(len(words1), len(words2))
        
        # 5. Финальный score
        fuzzy_score = (base_ratio * 0.4) + (word_overlap * 0.4) + (first_letter_score * 0.2)
        return min(fuzzy_score, 1.0)

class KnowledgeBaseSearcher:
    """Поиск в локальной базе знаний с учетом опечаток"""
    
    def __init__(self, file_path: str = "knowledge_base.json"):
        self.file_path = file_path
        self.kb_data = self._load_knowledge_base()
        self.preprocessor = TextPreprocessor()
        self.fuzzy_searcher = FuzzySearcher()
        self.question_index = self._build_index()
        # Создадим индекс для похожих слов
        self.synonym_index = self._build_synonym_index()
    
    def _build_synonym_index(self) -> Dict[str, List[str]]:
        """Создание индекса синонимов и похожих слов"""
        synonyms = {
            'создание': ['создать', 'создай', 'создавать', 'создаю', 'создал'],
            'новая': ['новый', 'новое', 'новые', 'новую', 'новой'],
            'накладная': ['накладной', 'накладные', 'накладных', 'накладную', 'накладным'],
            'отчет': ['отчета', 'отчеты', 'отчетов', 'отчетом', 'отчетам'],
            'платеж': ['платежа', 'платежи', 'платежей', 'платежом', 'платежам'],
            'документ': ['документа', 'документы', 'документов', 'документом', 'документам'],
        }
        return synonyms
    
    def _expand_keywords(self, keywords: List[str]) -> List[str]:
        """Расширение ключевых слова синонимами"""
        expanded = set(keywords)
        for keyword in keywords:
            if keyword in self.synonym_index:
                expanded.update(self.synonym_index[keyword])
        return list(expanded)
    
    def find_best_match(
        self, 
        user_question: str, 
        source_type: Optional[str] = None,
        threshold: float = 0.25  # СНИЖЕННЫЙ ПОРОГ
    ) -> Tuple[Optional[Dict], float]:
        if not self.kb_data:
            return None, 0.0
        
        normalized_question = self.preprocessor.normalize_text(user_question)
        keywords = self.preprocessor.extract_keywords(normalized_question)
        
        # Расширяем ключевые слова синонимами
        expanded_keywords = self._expand_keywords(keywords)
        
        best_item = None
        best_confidence = 0.0
        
        # Собираем кандидатов
        candidate_items = []
        seen_ids = set()
        
        # Ищем по всем ключевым словам и их синонимам
        for keyword in expanded_keywords:
            if keyword in self.question_index:
                for item in self.question_index[keyword]:
                    item_id = item.get('id')
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        candidate_items.append(item)
        
        # Если не нашли по ключевым словам, ищем во всей базе
        if not candidate_items:
            candidate_items = self.kb_data
        
        # Проверяем каждого кандидата
        for item in candidate_items:
            item_question = item.get('question', '')
            item_source = item.get('source', 'manual')
            
            if source_type and item_source != source_type:
                continue
            
            normalized_item = self.preprocessor.normalize_text(item_question)
            
            # Улучшенное сравнение
            similarity = self._calculate_similarity(normalized_question, normalized_item)
            
            # Проверяем частичные совпадения
            partial_match_score = 0
            for kw in keywords:
                if kw in normalized_item:
                    partial_match_score += 0.2
            
            item_keywords = self.preprocessor.extract_keywords(normalized_item)
            common_keywords = set(keywords) & set(item_keywords)
            keyword_overlap = len(common_keywords) / max(len(keywords), 1)
            
            # Новая формула с учетом частичных совпадений
            confidence = (similarity * 0.4) + (keyword_overlap * 0.3) + (partial_match_score * 0.3)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_item = item
        
        print(f"🔍 Поиск: '{user_question}' -> лучшая уверенность: {best_confidence:.2f}")
        
        if best_confidence >= threshold:
            return best_item, best_confidence
        
        return None, 0.0
    
    def find_by_exact_question(
        self, 
        question: str, 
        source_type: Optional[str] = None
    ) -> Optional[Dict]:
        """Поиск точного совпадения по вопросу"""
        normalized_question = self.preprocessor.normalize_text(question)
        
        for item in self.kb_data:
            item_question = self.preprocessor.normalize_text(item.get('question', ''))
            item_source = item.get('source', 'manual')
            
            if source_type and item_source != source_type:
                continue
            
            if item_question == normalized_question:
                return item
        
        return None

class IntentClassifier:
    """Классификатор намерений пользователя"""
    
    def __init__(self):
        self.intents = {
            'greeting': ['привет', 'здравствуй', 'добрый', 'hello', 'hi', 'начать', 'прив'],
            'farewell': ['пока', 'до свидания', 'выход', 'закончить', 'спасибо', 'пок', 'всего'],
            'help': ['помощь', 'помоги', 'что ты умеешь', 'команды', 'подскажи', 'посоветуй'],
            'question_1c': ['как', 'где', 'почему', 'зачем', 'можно ли', 'какой', 'чем'],
            'document': ['накладная', 'счет', 'акт', 'договор', 'ордер', 'отчет', 'документ'],
            'operation': ['создать', 'удалить', 'изменить', 'провести', 'отменить', 'сделать', 'написать'],
            'search': ['найти', 'поиск', 'искать', 'где найти', 'как найти', 'найди'],
            'button_click': ['button:', 'menu:', 'нажать кнопку', 'клик по', 'кнопка']
        }
    
    def classify(self, text: str) -> List[str]:
        text_lower = text.lower()
        detected_intents = []
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_intents.append(intent)
                    break
        return detected_intents if detected_intents else ['unknown']
    
    def is_button_click(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        text_lower = text.lower()
        
        for prefix in ['button:', 'menu:']:
            if text_lower.startswith(prefix):
                parts = text_lower.split(':', 1)
                if len(parts) == 2:
                    return True, prefix.rstrip(':'), parts[1].strip()
        
        button_patterns = [
            (['нажать кнопку', 'нажми кнопку', 'нажы кнопку', 'нажатькнопку'], 'button'),
            (['клик по кнопке', 'кликнуть кнопку', 'клик по', 'кликнуть'], 'button'),
            (['в меню', 'меню', 'в разедел', 'разедел'], 'menu'),
            (['раздел', 'раздил', 'радел'], 'menu')
        ]
        
        for patterns, source_type in button_patterns:
            for pattern in patterns:
                if pattern in text_lower:
                    start_idx = text_lower.find(pattern) + len(pattern)
                    button_text = text_lower[start_idx:].strip()
                    if button_text:
                        return True, source_type, button_text
        
        return False, None, None

class ButtonHandler:
    """Обработчик нажатий кнопок с учетом опечаток"""
    
    def __init__(self, kb_searcher: KnowledgeBaseSearcher):
        self.kb_searcher = kb_searcher
        self.preprocessor = TextPreprocessor()
    
    def handle_button_click(
        self, 
        source_type: str, 
        button_text: str
    ) -> Optional[Dict]:
        normalized_button = self.preprocessor.normalize_text(button_text)
        
        exact_match = self.kb_searcher.find_by_exact_question(
            normalized_button, 
            source_type=source_type
        )
        
        if exact_match:
            return exact_match
        
        fuzzy_match, confidence = self.kb_searcher.find_best_match(
            normalized_button,
            source_type=source_type,
            threshold=0.3
        )
        
        if fuzzy_match and confidence >= 0.3:
            return fuzzy_match
        
        any_match, confidence = self.kb_searcher.find_best_match(
            normalized_button,
            threshold=0.35
        )
        
        if any_match:
            return any_match
        
        return None

class NLPEngine:
    """Основной NLP-движок"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.intent_classifier = IntentClassifier()
        self.kb_searcher = KnowledgeBaseSearcher()
        self.button_handler = ButtonHandler(self.kb_searcher)
        self._current_options = {}
        print("✅ NLPEngine инициализирован")
        print(f"📊 Загружено {len(self.kb_searcher.kb_data)} записей из базы знаний")
    
    def get_final_answer(self, user_message: str) -> str:
        print(f"🔍 get_final_answer вызван с: '{user_message}'")
        try:
            analysis = self.process_message(user_message)
            
            if analysis['has_kb_answer']:
                kb_item = analysis['kb_item']
                answer = kb_item.get('answer', '')
                confidence = analysis['kb_confidence']
                
                # СНИЖЕННЫЙ ПОРОГ для уточнения
                if confidence < 0.4:  # было 0.65
                    print(f"🔄 Низкая уверенность ({confidence:.2f}), предлагаем уточнение")
                    clarification_response = self.get_clarification_response(analysis)
                    return clarification_response
                
                # Для кнопок добавляем специальное оформление
                if analysis.get('is_button_click'):
                    source = kb_item.get('source', '')
                    button_text = kb_item.get('metadata', {}).get('button_text', '')
                    
                    if button_text and source in ['menu', 'button']:
                        header = f"🔘 **{button_text}**\n\n"
                        return header + answer
                
                # Для fuzzy match добавляем пояснение
                confidence_percent = int(confidence * 100)
                
                if analysis.get('is_fuzzy_match'):
                    original_question = kb_item.get('question', '')
                    return f"✅ {answer}\n\n<i>(Возможно, вы имели в виду: '{original_question}'. Найдено с уверенностью {confidence_percent}%)</i>"
                else:
                    return f"✅ {answer}\n\n<i>(Найдено в базе знаний с уверенностью {confidence_percent}%)</i>"
            
            # Если ответ не найден, ищем похожие вопросы
            similar_questions = self._find_similar_questions(user_message)
            if similar_questions:
                return self._create_similar_questions_response(user_message, similar_questions)
            
            suggestions = self._get_search_suggestions(user_message)
            return f"🤔 <b>К сожалению, я не смог найти ответ на ваш вопрос.</b>\n\n{suggestions}"
            
        except Exception as e:
            print(f"❌ Ошибка в get_final_answer: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ <b>Произошла ошибка при обработке запроса:</b>\n\n{str(e)[:200]}"
    
    def _find_similar_questions(self, user_message: str, limit: int = 5) -> List[Dict]:
        """Находит похожие вопросы даже с низкой уверенностью"""
        similar = []
        normalized_query = self.preprocessor.normalize_text(user_message)
        
        for item in self.kb_searcher.kb_data:
            item_question = self.preprocessor.normalize_text(item.get('question', ''))
            similarity = self.kb_searcher._calculate_similarity(normalized_query, item_question)
            
            if similarity > 0.2:  # Низкий порог для похожих вопросов
                similar.append({
                    'item': item,
                    'similarity': similarity,
                    'question': item.get('question', '')
                })
        
        # Сортируем по убыванию схожести
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]
    
    def _create_similar_questions_response(self, user_query: str, similar_questions: List[Dict]) -> str:
        """Создает ответ с похожими вопросами"""
        if not similar_questions:
            return ""
        
        response = f"🔍 <b>По вашему запросу не найден точный ответ.</b>\n\n"
        response += f"<i>Возможно, вам подойдет один из этих вариантов:</i>\n\n"
        
        for i, sim in enumerate(similar_questions[:3], 1):
            question = sim['question']
            similarity = int(sim['similarity'] * 100)
            response += f"{i}. <b>{question}</b> (сходство: {similarity}%)\n"
        
        response += f"\n<b>Выберите номер варианта (1-{min(3, len(similar_questions))})</b>"
        
        # Сохраняем варианты для обработки выбора
        self._current_options = {
            i: sim['item'] for i, sim in enumerate(similar_questions[:3], 1)
        }
        
        return response
    
    def get_option_selection(self, option_number: int) -> Optional[str]:
        """Исправленная обработка выбора опции"""
        print(f"🔍 Выбор опции {option_number}, доступные опции: {list(self._current_options.keys())}")
        
        if option_number in self._current_options:
            item = self._current_options[option_number]
            if isinstance(item, dict):
                answer = item.get('answer', '')
                source = item.get('source', '')
                
                if source in ['button', 'menu']:
                    button_text = item.get('metadata', {}).get('button_text', '')
                    return f"🔘 **{button_text}**\n\n{answer}"
                else:
                    return answer
            else:
                print(f"⚠️ Неверный формат элемента: {type(item)}")
                return None
        
        print(f"⚠️ Опция {option_number} не найдена")
        return None
# Создаем глобальный экземпляр NLP-движка
nlp_engine = NLPEngine()
