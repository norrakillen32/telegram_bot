import os
import json
import re
import difflib
import requests
from typing import Dict, Any, List, Optional, Tuple

class TelegramBot:
    """Работа с Telegram API"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан!")
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML", 
                     reply_markup: Dict = None) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False
    
    def send_chat_action(self, chat_id: int, action: str = "typing") -> bool:
        """Отправка действия (печатает, загружает фото и т.д.)"""
        try:
            response = requests.post(
                f"{self.api_url}/sendChatAction",
                json={"chat_id": chat_id, "action": action},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

class ResponseFormatter:
    """Форматирование ответов и клавиатур"""
    
    @staticmethod
    def format_welcome_message() -> str:
        """Форматирование приветственного сообщения"""
        return """👋 <b>Добро пожаловать в бот-помощник по 1С!</b>

🤖 <i>Я использую искусственный интеллект для поиска ответов:</i>

<b>📚 Мои возможности:</b>
1. <b>База знаний</b> — быстрые ответы на частые вопросы
2. <b>Поиск в документации 1С</b> — ответы по официальной документации
3. <b>Анализ контекста</b> — понимаю ваши намерения

<b>💡 Примеры вопросов:</b>
• Как создать накладную на отгрузку?
• Где найти отчет о продажах за месяц?
• Как провести оплату от клиента?
• Как настроить пользователя в системе?

<b>⚡ Просто задайте ваш вопрос!</b>"""
    
    @staticmethod
    def create_main_keyboard() -> Dict:
        """Создание главной клавиатуры"""
        return {
            "keyboard": [
                [{"text": "📦 Накладные"}, {"text": "📊 Отчеты"}],
                [{"text": "💰 Платежи"}, {"text": "📋 Документы"}],
                [{"text": "📈 Финансы"}, {"text": "👥 Контрагенты"}],
                [{"text": "⚙️ Настройки"}, {"text": "🆘 Помощь"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
            "input_field_placeholder": "Выберите раздел или задайте вопрос..."
        }
    
    @staticmethod
    def create_invoices_keyboard() -> Dict:
        """Создание клавиатуры для раздела Накладные"""
        return {
            "keyboard": [
                [{"text": "📦 Новая накладная"}, {"text": "📋 Копировать накладную"}],
                [{"text": "🔄 Создать УПД"}, {"text": "🚚 ТТН для перевозки"}],
                [{"text": "🔍 Поиск накладной"}, {"text": "📊 Статистика накладных"}],
                [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
            ],
            "resize_keyboard": True
        }
    
    @staticmethod
    def create_reports_keyboard() -> Dict:
        """Создание клавиатуры для раздела Отчеты"""
        return {
            "keyboard": [
                [{"text": "📈 Прибыль и убытки"}, {"text": "💰 Денежный поток"}],
                [{"text": "📦 Остатки товаров"}, {"text": "👥 Дебиторская задолженность"}],
                [{"text": "📊 Продажи по периодам"}, {"text": "📋 Товарооборот"}],
                [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
            ],
            "resize_keyboard": True
        }
    
    @staticmethod
    def create_payments_keyboard() -> Dict:
        """Создание клавиатуры для раздела Платежи"""
        return {
            "keyboard": [
                [{"text": "💳 Оплата поставщику"}, {"text": "💰 Поступление от клиента"}],
                [{"text": "💵 Выдача под отчет"}, {"text": "🏦 Банковские выписки"}],
                [{"text": "🧾 Авансовые отчеты"}, {"text": "📑 Кассовая книга"}],
                [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
            ],
            "resize_keyboard": True
        }

class KnowledgeBaseSearcher:
    """Поиск в базе знаний"""
    
    def __init__(self, file_path: str = "knowledge_base.json"):
        self.file_path = file_path
        self.kb_data = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Загрузка базы знаний из JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.kb_data = json.load(f)
                print(f"✅ База знаний загружена: {len(self.kb_data)} записей")
        except FileNotFoundError:
            print(f"⚠️ Файл {self.file_path} не найден")
            self.kb_data = []
        except json.JSONDecodeError as e:
            print(f"⚠️ Ошибка чтения JSON: {e}")
            self.kb_data = []
        except Exception as e:
            print(f"⚠️ Ошибка загрузки базы знаний: {e}")
            self.kb_data = []
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)  # Удаляем пунктуацию
        text = re.sub(r'\s+', ' ', text)      # Убираем лишние пробелы
        return text
    
    def find_best_match(self, user_question: str, threshold: float = 0.4) -> Tuple[Optional[str], float]:
        """Поиск лучшего совпадения в базе знаний"""
        if not self.kb_data:
            return None, 0.0
        
        user_q = self.normalize_text(user_question)
        best_answer = None
        best_score = 0.0
        
        for item in self.kb_data:
            item_question = item.get('question', '')
            item_q = self.normalize_text(item_question)
            
            # Рассчитываем схожесть текстов
            score = difflib.SequenceMatcher(None, user_q, item_q).ratio()
            
            # Дополнительная проверка на вхождение ключевых слов
            if score < threshold:
                # Разбиваем на слова и проверяем совпадения
                user_words = set(user_q.split())
                item_words = set(item_q.split())
                common_words = user_words.intersection(item_words)
                if common_words:
                    score = max(score, len(common_words) / max(len(user_words), 1) * 0.8)
            
            if score > best_score:
                best_score = score
                best_answer = item.get('answer')
        
        return best_answer, best_score
    
    def search_answer(self, question: str) -> str:
        """Основная функция поиска ответа"""
        # Проверяем специальные кнопки и команды
        special_responses = {
            # Кнопки главного меню
            "📦 накладные": "📦 <b>Раздел «Накладные»</b>\n\nВыберите действие:\n• 📦 Новая накладная — создать с нуля\n• 📋 Копировать накладную — использовать шаблон\n• 🔄 Создать УПД — универсальный передаточный документ\n• 🚚 ТТН для перевозки — товарно-транспортная накладная\n• 🔍 Поиск накладной — найти по номеру или контрагенту\n• 📊 Статистика накладных — анализ продаж",
            "📊 отчеты": "📊 <b>Раздел «Отчеты»</b>\n\nОсновные отчеты:\n• 📈 Прибыль и убытки — финансовый результат\n• 💰 Денежный поток — движение денежных средств\n• 📦 Остатки товаров — наличие на складах\n• 👥 Дебиторская задолженность — долги покупателей\n• 📊 Продажи по периодам — динамика продаж\n• 📋 Товарооборот — оборачиваемость товаров",
            "💰 платежи": "💰 <b>Раздел «Платежи»</b>\n\nДоступные действия:\n• 💳 Оплата поставщику — платежное поручение\n• 💰 Поступление от клиента — оприходование оплаты\n• 💵 Выдача под отчет — аванс сотруднику\n• 🏦 Банковские выписки — загрузка операций из банка\n• 🧾 Авансовые отчеты — расчеты с подотчетными лицами\n• 📑 Кассовая книга — учет наличных операций",
            "📋 документы": "📋 <b>Раздел «Документы»</b>\n\nТипы документов в 1С:\n• Товарные документы (накладные, счета, акты)\n• Финансовые документы (платежные, кассовые)\n• Учетные документы (приходные/расходные ордера)\n• Документы по контрагентам (договоры, акты сверки)\n\n📍 Навигация: каждый раздел содержит свои документы",
            
            # Команды
            "/start": ResponseFormatter.format_welcome_message(),
            "помощь": "🆘 <b>Помощь по использованию бота:</b>\n\n<b>Основные команды:</b>\n/start — начать работу с ботом\n\n<b>Как задавать вопросы:</b>\n1. Конкретно: «Как создать накладную в 1С?»\n2. С контекстом: «Мне нужно провести оплату поставщику»\n3. По шагам: «Какие этапы создания отчета?»\n\n<b>Используйте кнопки меню</b> для быстрого доступа к разделам.",
            "привет": "👋 Привет! Я бот-помощник по 1С. Используйте кнопки меню или задайте вопрос.",
            
            # Кнопки подменю
            "📦 новая накладная": "🆕 <b>Создание новой накладной:</b>\n\n1. <b>Продажи</b> → <b>Реализация (акты, накладные)</b>\n2. Нажмите <b>Создать</b> → <b>Товары (накладная)</b>\n3. Заполните: контрагент, договор, склад\n4. Добавьте товары и укажите количество\n5. Нажмите <b>Провести</b> и <b>Печать</b> для ТОРГ-12",
            "📈 прибыль и убытки": "📈 <b>Отчет «Прибыль и убытки»:</b>\n\n1. <b>Отчеты</b> → <b>Стандартные отчеты</b>\n2. Выберите <b>Оборотно-сальдовая ведомость</b>\n3. Настройте период и счета (90, 91)\n4. Нажмите <b>Сформировать</b>\n\n<b>Ключевые показатели:</b>\n• Выручка (90.01)\n• Себестоимость (90.02)\n• Валовая прибыль\n• Чистая прибыль",
            "💳 оплата поставщику": "💳 <b>Оплата поставщику:</b>\n\n1. <b>Банк и касса</b> → <b>Платежные поручения</b>\n2. <b>Создать</b> → <b>Исходящее платежное поручение</b>\n3. Заполните: поставщик, сумма, назначение платежа\n4. Укажите банковские реквизиты\n5. Нажмите <b>Провести</b>\n\n<b>Основание:</b> можно указать счет или договор",
        }
        
        question_lower = question.lower().strip()
        
        # Проверяем специальные ответы
        for key, response in special_responses.items():
            if key.lower() == question_lower or key.lower() in question_lower:
                return response
        
        # Поиск в базе знаний
        answer, confidence = self.find_best_match(question)
        
        if answer and confidence >= 0.4:
            confidence_pct = int(confidence * 100)
            return f"{answer}\n\n<i>(Найдено в базе знаний: {confidence_pct}% совпадение)</i>"
        
        # Fallback ответ
        return f"""🤔 <b>По запросу '{question}' точного ответа не найдено.</b>

Попробуйте:
1. Переформулировать вопрос
2. Использовать кнопки меню
3. Задать более конкретный вопрос

<i>База знаний содержит {len(self.kb_data)} готовых ответов по 1С.</i>"""

class BotProcessor:
    """Основной процессор бота с интегрированным NLP-движком"""
    
    def __init__(self):
        self.telegram = TelegramBot()
        self.formatter = ResponseFormatter()
        # Заменяем KnowledgeBaseSearcher на NLPEngine
        self.nlp_engine = NLPEngine()
        self.user_sessions = {}  # Хранит сессии пользователей
    
    def _get_user_session(self, user_id: int) -> Dict:
        """Получение или создание сессии пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'message_count': 0,
                'last_activity': None,
                'current_menu': None,
                'waiting_for_clarification': False,
                'clarification_options': {},
                'original_query': ''
            }
        return self.user_sessions[user_id]
    
    def _update_user_session(self, user_id: int, message: str = None):
        """Обновление сессии пользователя"""
        session = self._get_user_session(user_id)
        session['message_count'] += 1
        session['last_activity'] = 'сейчас'
        return session
    
    def _handle_start(self, chat_id: int, args: str) -> bool:
        """Обработка команды /start"""
        # Сбрасываем состояние уточнения
        session = self._get_user_session(chat_id)
        session['waiting_for_clarification'] = False
        session['clarification_options'] = {}
        
        keyboard = self.formatter.create_main_keyboard()
        return self.telegram.send_message(
            chat_id,
            self.formatter.format_welcome_message(),
            reply_markup=keyboard
        )
    
    def _handle_help(self, chat_id: int, args: str) -> bool:
        """Обработка команды /help"""
        help_text = """🆘 <b>Помощь по использованию бота:</b>

<b>Основные команды:</b>
/start — начать работу с ботом
/help — показать эту справку

<b>Как задавать вопросы:</b>
1. <i>Конкретно</i>: «Как создать накладную в 1С?»
2. <i>С контекстом</i>: «Мне нужно провести оплату поставщику»
3. <i>По шагам</i>: «Какие этапы создания отчета?»

<b>Интерактивные возможности:</b>
• Бот может уточнять вопросы при неполной информации
• Отвечайте номером варианта (1, 2, 3) на уточняющие вопросы
• Используйте кнопки меню для точного выбора

<b>📊 Статистика вашего диалога</b> доступна по команде /stats"""
        
        return self.telegram.send_message(chat_id, help_text)
    
    def _handle_stats(self, chat_id: int, args: str) -> bool:
        """Обработка команды /stats"""
        session = self._get_user_session(chat_id)
        
        stats_text = f"""📊 <b>Ваша статистика:</b>

• <b>Всего сообщений:</b> {session['message_count']}
• <b>Последняя активность:</b> {session.get('last_activity', 'неизвестно')}
• <b>Текущее меню:</b> {session.get('current_menu', 'главное')}
• <b>Ожидание уточнения:</b> {'Да' if session.get('waiting_for_clarification') else 'Нет'}

<b>База знаний бота:</b>
• Загружено записей: {len(self.nlp_engine.kb_searcher.kb_data)}
• Используется NLP-движок с контекстным анализом"""
        
        return self.telegram.send_message(chat_id, stats_text)
    
    def _handle_option_selection(self, chat_id: int, option_number: int) -> bool:
        """Обработка выбора номера варианта из уточнения"""
        session = self._get_user_session(chat_id)
        options = session.get('clarification_options', {})
        
        if option_number in options:
            selected = options[option_number]
            item = selected['item']
            
            # Получаем ответ из выбранного варианта
            answer = item.get('answer', '')
            source = item.get('source', '')
            
            # Форматируем ответ в зависимости от типа
            if source in ['button', 'menu']:
                button_text = item.get('metadata', {}).get('button_text', '')
                response = f"🔘 **{button_text}**\n\n{answer}"
            else:
                response = answer
            
            # Сбрасываем состояние уточнения
            session['waiting_for_clarification'] = False
            session['clarification_options'] = {}
            
            return self.telegram.send_message(chat_id, response, parse_mode="HTML")
        else:
            # Неверный номер
            return self.telegram.send_message(
                chat_id,
                f"❌ <b>Неверный номер варианта:</b> {option_number}\n\n"
                f"Пожалуйста, выберите номер из предложенного списка (1-{len(options)})."
            )
    
    def handle_command(self, chat_id: int, command: str, args: str = "") -> bool:
        """Обработка команд"""
        commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/stats': self._handle_stats,
        }
        
        clean_command = command.split('@')[0]
        handler = commands.get(clean_command)
        
        if handler:
            return handler(chat_id, args)
        
        return self.telegram.send_message(
            chat_id,
            f"🤔 <b>Неизвестная команда:</b> {command}\n\nИспользуйте /help для просмотра доступных команд."
        )
    
    def handle_button_click(self, chat_id: int, button_text: str) -> bool:
        """Обработка нажатия кнопок меню"""
        session = self._update_user_session(chat_id)
        
        # Сбрасываем состояние уточнения при нажатии кнопки
        session['waiting_for_clarification'] = False
        session['clarification_options'] = {}
        
        button_lower = button_text.lower()
        
        # Обработка навигационных кнопок
        if button_lower == "⬅️ назад":
            session['current_menu'] = 'main'
            keyboard = self.formatter.create_main_keyboard()
            return self.telegram.send_message(
                chat_id,
                "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
                reply_markup=keyboard
            )
        
        elif button_lower == "🏠 в главное меню":
            session['current_menu'] = 'main'
            keyboard = self.formatter.create_main_keyboard()
            return self.telegram.send_message(
                chat_id,
                "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
                reply_markup=keyboard
            )
        
        # Обработка разделов меню
        elif "накладные" in button_lower or button_text == "📦 накладные":
            session['current_menu'] = 'invoices'
            keyboard = self.formatter.create_invoices_keyboard()
            return self.telegram.send_message(
                chat_id,
                "📦 <b>Раздел «Накладные»</b>\n\nВыберите действие или задайте вопрос:",
                reply_markup=keyboard
            )
        
        elif "отчеты" in button_lower or button_text == "📊 отчеты":
            session['current_menu'] = 'reports'
            keyboard = self.formatter.create_reports_keyboard()
            return self.telegram.send_message(
                chat_id,
                "📊 <b>Раздел «Отчеты»</b>\n\nВыберите тип отчета:",
                reply_markup=keyboard
            )
        
        elif "платежи" in button_lower or button_text == "💰 платежи":
            session['current_menu'] = 'payments'
            keyboard = self.formatter.create_payments_keyboard()
            return self.telegram.send_message(
                chat_id,
                "💰 <b>Раздел «Платежи»</b>\n\nВыберите действие:",
                reply_markup=keyboard
            )
        
        elif button_text == "📋 документы":
            session['current_menu'] = 'documents'
            keyboard = {
                "keyboard": [
                    [{"text": "📄 Счета"}, {"text": "📑 Акта"}],
                    [{"text": "📝 Договоры"}, {"text": "🏢 Организации"}],
                    [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
                ],
                "resize_keyboard": True
            }
            return self.telegram.send_message(
                chat_id,
                "📋 <b>Раздел «Документы»</b>\n\nВыберите тип документа:",
                reply_markup=keyboard
            )
        
        # Для остальных кнопок используем NLP-движок
        return self.handle_message(chat_id, button_text)
    
    def handle_message(self, chat_id: int, user_message: str) -> bool:
        """Обработка обычного сообщения с использованием NLP-движка"""
        # Показываем индикатор "печатает"
        self.telegram.send_chat_action(chat_id, "typing")
        
        # Обновляем сессию
        session = self._update_user_session(chat_id, user_message)
        
        # Проверяем, ожидаем ли мы уточнения от пользователя
        if session.get('waiting_for_clarification'):
            # Проверяем, является ли сообщение числом (выбор варианта)
            if user_message.isdigit():
                option_number = int(user_message)
                return self._handle_option_selection(chat_id, option_number)
            else:
                # Пользователь не выбрал номер, сбрасываем состояние
                session['waiting_for_clarification'] = False
                session['clarification_options'] = {}
        
        # Обрабатываем запрос через NLP-движок
        analysis = self.nlp_engine.process_message(user_message)
        
        # Если нашли ответ с низкой уверенностью, предлагаем уточнить
        if analysis['has_kb_answer'] and analysis['kb_confidence'] < 0.65:
            # Получаем уточняющий ответ с вариантами
            clarification_response = self.nlp_engine.get_clarification_response(analysis)
            
            # Если у движка есть текущие опции, сохраняем их в сессии
            if hasattr(self.nlp_engine, '_current_options') and self.nlp_engine._current_options:
                session['waiting_for_clarification'] = True
                session['clarification_options'] = self.nlp_engine._current_options.copy()
                session['original_query'] = user_message
            
            return self.telegram.send_message(chat_id, clarification_response, parse_mode="HTML")
        
        # Если уверенность высокая или ответ не найден, используем стандартную логику
        final_answer = self.nlp_engine.get_final_answer(user_message)
        return self.telegram.send_message(chat_id, final_answer, parse_mode="HTML")
    
    def process_update(self, update_data: Dict[str, Any]) -> bool:
        """Обработка входящего обновления от Telegram"""
        try:
            if 'message' not in update_data:
                return False
            
            message = update_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if not text:
                return False
            
            print(f"📨 Сообщение от {chat_id}: {text}")
            
            # Определяем тип сообщения
            if text.startswith('/'):
                return self.handle_command(chat_id, text)
            else:
                # Проверяем, не нажата ли кнопка меню
                button_texts = [
                    "📦", "📊", "💰", "📋", "📈", "👥", "⚙️", "🆘",
                    "Накладные", "Отчеты", "Платежи", "Документы",
                    "Финансы", "Контрагенты", "Настройки", "Помощь",
                    "⬅️", "🏠", "накладные", "отчеты", "платежи", "документы"
                ]
                
                if any(btn in text.lower() for btn in [b.lower() for b in button_texts]):
                    return self.handle_button_click(chat_id, text)
                else:
                    return self.handle_message(chat_id, text)
            
        except Exception as e:
            print(f"❌ Ошибка в process_update: {e}")
            return False

# Создаем глобальный экземпляр процессора
bot_processor = BotProcessor() 
