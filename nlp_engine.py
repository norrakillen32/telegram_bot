import json
import re
from typing import Tuple, Optional, Dict, List
import difflib

class TextPreprocessor:
    """Предобработка текста пользователя"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста: нижний регистр, удаление лишних символов"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)  # Удаляем пунктуацию
        text = re.sub(r'\s+', ' ', text)      # Убираем лишние пробелы
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Список стоп-слов для русского языка
        stop_words = {
            'как', 'где', 'что', 'кто', 'когда', 'почему', 'зачем',
            'мне', 'мной', 'меня', 'тебе', 'тобой', 'тебя',
            'свой', 'своя', 'своё', 'свои',
            'это', 'этот', 'эта', 'эти', 'этот',
            'вот', 'тут', 'там', 'здесь', 'туда',
            'очень', 'просто', 'вообще', 'совсем'
        }
        
        words = text.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    @staticmethod
    def lemmatize_word(word: str) -> str:
        """Простая лемматизация (можно заменить на pymorphy2 или natasha)"""
        # Базовые правила для русского языка
        endings = {
            'ся': '', 'ться': '', 'тся': '', 'ться': '',
            'ия': 'и', 'ию': 'и', 'ии': 'и',
            'ая': 'а', 'ую': 'а', 'ой': 'а',
            'ый': 'ый', 'ого': 'ый', 'ому': 'ый',
            'ие': 'ие', 'их': 'ие', 'им': 'ие'
        }
        
        for ending, replacement in endings.items():
            if word.endswith(ending):
                return word[:-len(ending)] + replacement
        return word

class KnowledgeBaseSearcher:
    """Поиск в локальной базе знаний"""
    
    def __init__(self, file_path: str = "knowledge_base.json"):
        self.file_path = file_path
        self.kb_data = self._load_knowledge_base()
        self.preprocessor = TextPreprocessor()
    
    def _load_knowledge_base(self) -> List[Dict]:
        """Загрузка базы знаний"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Расчет схожести текстов (0-1)"""
        # Используем SequenceMatcher для сравнения строк
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def find_best_match(self, user_question: str, threshold: float = 0.6) -> Tuple[Optional[str], float]:
        """
        Поиск лучшего совпадения в базе знаний
        
        Возвращает (ответ, уверенность) или (None, 0)
        """
        if not self.kb_data:
            return None, 0.0
        
        normalized_question = self.preprocessor.normalize_text(user_question)
        keywords = self.preprocessor.extract_keywords(normalized_question)
        
        best_answer = None
        best_confidence = 0.0
        
        for item in self.kb_data:
            item_question = item.get('question', '')
            item_answer = item.get('answer', '')
            
            # Нормализуем вопрос из базы
            normalized_item = self.preprocessor.normalize_text(item_question)
            
            # Рассчитываем схожесть
            similarity = self._calculate_similarity(normalized_question, normalized_item)
            
            # Дополнительный бонус за ключевые слова
            item_keywords = self.preprocessor.extract_keywords(normalized_item)
            keyword_overlap = len(set(keywords) & set(item_keywords)) / max(len(keywords), 1)
            
            # Итоговая уверенность
            confidence = (similarity * 0.7) + (keyword_overlap * 0.3)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_answer = item_answer
        
        # Проверяем порог уверенности
        if best_confidence >= threshold:
            return best_answer, best_confidence
        
        return None, 0.0

class DocumentationSearcher:
    """Поиск в документации 1С"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
    
    def search(self, user_question: str) -> Tuple[str, str]:
        """
        Поиск в документации 1С
        
        Возвращает (источник, ответ)
        """
        normalized = self.preprocessor.normalize_text(user_question)
        keywords = self.preprocessor.extract_keywords(normalized)
        
        # TODO: Здесь можно подключить:
        # 1. Векторный поиск (ChromaDB, Qdrant)
        # 2. RAG с локальной LLM (Ollama)
        # 3. API 1С для поиска в документации
        
        # Временная логика поиска по ключевым словам
        answers_by_topic = {
            'накладная': "📦 <b>Документация по накладным:</b>\n\nВ документации 1С создание накладной описано в разделе 'Продажи' → 'Реализация товаров и услуг'. Для создания документа необходимо указать контрагента, склад, номенклатуру и количество.",
            'отчет': "📊 <b>Документация по отчетам:</b>\n\nОтчеты в 1С настраиваются через конфигуратор. Стандартные отчеты доступны в меню 'Отчеты'. Для создания собственного отчета используйте систему компоновки данных (СКД).",
            'оплата': "💰 <b>Документация по платежам:</b>\n\nПроведение оплаты осуществляется через документы 'Платежное поручение' или 'Кассовый ордер'. Документы находятся в разделах 'Банк' или 'Касса' соответственно.",
            'остаток': "📦 <b>Документация по остаткам:</b>\n\nОстатки товаров можно посмотреть через отчет 'Остатки товаров на складах' или через регистры накопления 'ТоварыНаСкладах'.",
            'приходный': "📥 <b>Документация по приходным ордерам:</b>\n\nПриходный ордер создается в разделе 'Склад' → 'Приходные ордера'. Документ используется для оприходования товаров от поставщиков."
        }
        
        # Ищем по ключевым словам
        for keyword in keywords:
            for topic, answer in answers_by_topic.items():
                if keyword.startswith(topic) or topic in keyword:
                    return "doc_1c", answer
        
        # Если не нашли по ключевым словам
        return "doc_1c", self._generate_default_answer(user_question, keywords)
    
    def _generate_default_answer(self, question: str, keywords: List[str]) -> str:
        """Генерация ответа по умолчанию"""
        if keywords:
            keywords_str = ", ".join(keywords[:3])
            return f"🔍 <b>Поиск в документации 1С:</b>\n\nПо запросу '{question}' я нашел упоминания о: {keywords_str}.\n\nОднако для точного ответа требуется дополнительная настройка поиска в документации."
        
        return f"🔍 <b>Поиск в документации 1С:</b>\n\nНе удалось найти информацию по запросу '{question}' в документации 1С.\n\nПопробуйте переформулировать вопрос или обратитесь к разделу справки в самой программе 1С."

class IntentClassifier:
    """Классификатор намерений пользователя"""
    
    def __init__(self):
        self.intents = {
            'greeting': ['привет', 'здравствуй', 'добрый', 'hello', 'hi', 'начать'],
            'farewell': ['пока', 'до свидания', 'выход', 'закончить', 'спасибо'],
            'help': ['помощь', 'помоги', 'что ты умеешь', 'команды'],
            'question_1c': ['как', 'где', 'почему', 'зачем', 'можно ли', 'какой'],
            'document': ['накладная', 'счет', 'акт', 'договор', 'ордер', 'отчет'],
            'operation': ['создать', 'удалить', 'изменить', 'провести', 'отменить'],
            'search': ['найти', 'поиск', 'искать', 'где найти', 'как найти']
        }
    
    def classify(self, text: str) -> List[str]:
        """Определение намерений в тексте"""
        text_lower = text.lower()
        detected_intents = []
        
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_intents.append(intent)
                    break
        
        return detected_intents if detected_intents else ['unknown']

class NLPEngine:
    """Основной NLP-движок"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.intent_classifier = IntentClassifier()
        self.kb_searcher = KnowledgeBaseSearcher()
        self.doc_searcher = DocumentationSearcher()
    
    def process_message(self, user_message: str) -> Dict:
        """
        Полная обработка сообщения пользователя
        
        Возвращает словарь с результатами анализа
        """
        # Нормализация текста
        normalized = self.preprocessor.normalize_text(user_message)
        
        # Классификация намерений
        intents = self.intent_classifier.classify(normalized)
        
        # Извлечение ключевых слов
        keywords = self.preprocessor.extract_keywords(normalized)
        
        # Поиск в базе знаний
        kb_answer, kb_confidence = self.kb_searcher.find_best_match(user_message)
        
        # Подготовка результата
        result = {
            'original_message': user_message,
            'normalized_message': normalized,
            'intents': intents,
            'keywords': keywords,
            'kb_answer': kb_answer,
            'kb_confidence': kb_confidence,
            'has_kb_answer': kb_answer is not None,
            'doc_answer': None,
            'doc_source': None
        }
        
        # Если в базе знаний не нашли, ищем в документации
        if not kb_answer:
            doc_source, doc_answer = self.doc_searcher.search(user_message)
            result['doc_answer'] = doc_answer
            result['doc_source'] = doc_source
        
        return result
    
    def get_final_answer(self, user_message: str) -> str:
        """Получение финального ответа для пользователя"""
        analysis = self.process_message(user_message)
        
        # Если нашли в базе знаний
        if analysis['has_kb_answer']:
            confidence_percent = int(analysis['kb_confidence'] * 100)
            return f"✅ {analysis['kb_answer']}\n\n<i>(Найдено в базе знаний с уверенностью {confidence_percent}%)</i>"
        
        # Если искали в документации
        if analysis['doc_answer']:
            source_map = {
                'doc_1c': 'документации 1С',
                'rag': 'интеллектуальном поиске',
                'api': 'API 1С'
            }
            source_name = source_map.get(analysis['doc_source'], 'источнике')
            
            return f"{analysis['doc_answer']}\n\n<i>(Найдено в {source_name})</i>"
        
        # Если ничего не нашли
        return "🤔 <b>К сожалению, я не смог найти ответ на ваш вопрос.</b>\n\nПопробуйте:\n1. Переформулировать вопрос\n2. Обратиться к администратору\n3. Проверить справку в самой программе 1С"

# Создаем глобальный экземпляр NLP-движка
nlp_engine = NLPEngine()
