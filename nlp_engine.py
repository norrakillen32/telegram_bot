import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class NLPEngine:
    def __init__(self, kb_path="knowledge_base.json"):
        self.kb_path = kb_path
        self.questions = []
        self.answers = []
        # Настраиваем TF‑IDF для русскоязычных запросов по 1С
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=[
                "и", "в", "на", "о", "а", "но", "что", "как", "я",
                "вы", "мы", "они", "этот", "тот", "весь", "все"
            ],
            ngram_range=(1, 2),
            max_features=5000  # Ограничиваем размер матрицы
        )
        self.tfidf_matrix = None
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """Загружает базу знаний и строит TF‑IDF матрицу."""
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.questions = [item['question'] for item in data]
        self.answers = [item['answer'] for item in data]
        self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

    def add_example(self, question, answer):
        """Добавляет новый пример в базу знаний."""
        with open(self.kb_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data.append({"question": question, "answer": answer})
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
        self.load_knowledge_base()  # Перестраиваем векторы

    def find_best_answer(self, query, threshold=0.4):
        """Находит лучший ответ по TF‑IDF + косинусному сходству."""
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        best_idx = np.argmax(similarities)

        if similarities[best_idx] >= threshold:
            return self.answers[best_idx]
        else:
            return (
                "Я не нашёл точного ответа. Попробуйте уточнить вопрос или добавьте новый пример через /learn.\n\n"
                "Примеры запросов:\n"
                "- Как создать накладную?\n"
                "- Где отчёт о прибыли?\n"
                "- Как провести оплату поставщику?"
            )
