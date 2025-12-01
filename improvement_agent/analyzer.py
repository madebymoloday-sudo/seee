"""Анализатор ошибок и генератор исправлений через AI"""
import os
import json
from typing import Dict, List, Optional
from config_loader import get_our_settings
our_settings = get_our_settings()
AI_API_KEY = our_settings.AI_API_KEY
AI_MODEL = our_settings.AI_MODEL
from monitor.error_tracker import error_tracker


class ErrorAnalyzer:
    """Анализирует ошибки и генерирует предложения по исправлению"""
    
    def __init__(self):
        self.ai_api_key = AI_API_KEY
        self.ai_model = AI_MODEL
        
    async def analyze_errors(self) -> Dict:
        """Проанализировать все ошибки и предложить исправления"""
        error_summary = error_tracker.get_error_summary()
        
        if error_summary["total_errors"] == 0:
            return {
                "status": "no_errors",
                "message": "Ошибок не найдено"
            }
        
        # Отправить уведомление о начале анализа (если доступен web_chat_viewer)
        try:
            from web_server import web_chat_viewer
            web_chat_viewer.add_agent_notification(
                title="🧠 Генерация исправлений",
                message=f"Анализирую {error_summary['total_errors']} ошибок и генерирую предложения по исправлению кода...",
                notification_type="analyzing",
                details=f"Использую AI модель для анализа ошибок"
            )
        except:
            pass  # web_chat_viewer может быть недоступен
        
        # Собрать контекст ошибок
        errors_context = error_tracker.get_recent_errors(10)
        
        # Сформировать анализ
        analysis = {
            "error_summary": error_summary,
            "recommendations": await self._generate_recommendations(errors_context),
            "code_fixes": await self._generate_code_fixes(errors_context)
        }
        
        return analysis
    
    async def _generate_recommendations(self, errors: List) -> List[Dict]:
        """Сгенерировать рекомендации по улучшению"""
        recommendations = []
        
        # Простой анализ без AI (можно расширить)
        error_types = {}
        for error in errors:
            error_type = error.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Рекомендации на основе типов ошибок
        if "conversation_error" in error_types:
            recommendations.append({
                "type": "response_quality",
                "priority": "high",
                "description": "Бот часто не понимает сообщения или отвечает некорректно",
                "suggested_fix": "Расширить словарь распознавания и улучшить логику генерации ответов"
            })
        
        # Использовать AI для более глубокого анализа (если API ключ есть)
        if self.ai_api_key:
            ai_recommendations = await self._ask_ai_for_recommendations(errors)
            recommendations.extend(ai_recommendations)
        
        return recommendations
    
    async def _generate_code_fixes(self, errors: List) -> List[Dict]:
        """Сгенерировать исправления кода"""
        fixes = []
        
        # Проанализировать ошибки и сгенерировать исправления
        if self.ai_api_key:
            fixes = await self._ask_ai_for_code_fixes(errors)
        else:
            # Простые исправления без AI
            fixes = self._generate_simple_fixes(errors)
        
        return fixes
    
    async def _ask_ai_for_recommendations(self, errors: List) -> List[Dict]:
        """Спросить AI о рекомендациях"""
        # Здесь будет интеграция с OpenAI/Anthropic/etc
        # Пока возвращаем пустой список
        return []
    
    async def _ask_ai_for_code_fixes(self, errors: List) -> List[Dict]:
        """Попросить AI сгенерировать исправления кода"""
        try:
            # Читаем текущий код бота
            bot_code_path = "main_bot/bot.py"
            with open(bot_code_path, "r", encoding="utf-8") as f:
                current_code = f.read()
            
            # Формируем промпт для AI
            errors_text = "\n".join([
                f"- {err.error_type}: {err.error_message}"
                for err in errors[:5]
            ])
            
            prompt = f"""
Проанализируй ошибки бота и предложи исправления кода:

Текущий код бота:
```python
{current_code}
```

Ошибки:
{errors_text}

Предложи исправленный код функции _generate_response с улучшенной логикой обработки сообщений.
Верни только исправленный код функции, без объяснений.
"""
            
            # Вызов AI API (пример для OpenAI)
            if "openai" in self.ai_api_key.lower() or self.ai_api_key.startswith("sk-"):
                return await self._call_openai(prompt, current_code)
            else:
                return self._generate_simple_fixes(errors)
                
        except Exception as e:
            print(f"[Analyzer] Ошибка при генерации исправлений: {e}")
            return self._generate_simple_fixes(errors)
    
    async def _call_openai(self, prompt: str, current_code: str) -> List[Dict]:
        """Вызов OpenAI API"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.ai_api_key)
            
            response = client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по Python и разработке ботов. Анализируй ошибки и предлагай исправления кода."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            improved_code = response.choices[0].message.content
            
            return [{
                "file": "main_bot/bot.py",
                "function": "_generate_response",
                "improved_code": improved_code,
                "description": "Улучшенная логика генерации ответов на основе анализа ошибок"
            }]
            
        except Exception as e:
            print(f"[Analyzer] Ошибка при вызове OpenAI: {e}")
            return []
    
    def _generate_simple_fixes(self, errors: List) -> List[Dict]:
        """Простые исправления без AI"""
        fixes = []
        
        # Проверяем, есть ли ошибки с "не понял"
        has_understanding_errors = any(
            "не понял" in str(err.context) for err in errors
        )
        
        if has_understanding_errors:
            fixes.append({
                "file": "main_bot/bot.py",
                "function": "_generate_response",
                "improved_code": """async def _generate_response(self, text: str) -> str:
    \"\"\"Генерация ответа на сообщение\"\"\"
    # Расширенная логика
    text_lower = text.lower().strip()
    
    # Приветствия
    greetings = ["привет", "здравствуй", "добрый", "hello", "hi", "здарова"]
    if any(g in text_lower for g in greetings):
        return "Привет! Как дела? Чем могу помочь?"
    
    # Вопрос о делах
    if any(phrase in text_lower for phrase in ["как дела", "что нового", "как жизнь"]):
        return "Отлично! Работаю над улучшением себя. А у тебя как дела?"
    
    # Прощание
    if any(phrase in text_lower for phrase in ["пока", "до свидания", "увидимся", "bye"]):
        return "До свидания! Удачного дня! Был рад пообщаться!"
    
    # Помощь
    if any(phrase in text_lower for phrase in ["помощь", "help", "что ты умеешь", "команды"]):
        return "Я могу: поздороваться, ответить на вопрос 'как дела', попрощаться, и ответить на простые вопросы. Попробуйте написать 'привет' или 'помощь'!"
    
    # Вопросы (общая категория)
    if "?" in text or any(word in text_lower for word in ["что", "как", "почему", "где", "когда"]):
        return "Интересный вопрос! К сожалению, я еще учусь. Можете задать более простой вопрос?"
    
    # Если ничего не подошло, более дружелюбный ответ
    return "Извините, я еще только учусь понимать людей. Можете написать что-то проще, например 'привет' или 'помощь'?"
""",
                "description": "Расширенная логика с большим словарем и более дружелюбными ответами"
            })
        
        return fixes


# Глобальный экземпляр анализатора
error_analyzer = ErrorAnalyzer()

