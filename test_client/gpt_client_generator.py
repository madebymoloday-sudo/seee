"""Генератор сообщений клиента через GPT API"""
import asyncio
from typing import Optional, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import get_our_settings
our_settings = get_our_settings()
AI_API_KEY = our_settings.AI_API_KEY
AI_MODEL = our_settings.AI_MODEL
AI_TEMPERATURE = our_settings.AI_TEMPERATURE


class GPTClientGenerator:
    """Генератор сообщений клиента через GPT API"""
    
    def __init__(self):
        self.api_key = AI_API_KEY
        self.model = AI_MODEL
        self.temperature = AI_TEMPERATURE
        self.openai_client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.api_key)
                print(f"[GPTClientGenerator] ✅ OpenAI API подключен (модель: {self.model})")
            except Exception as e:
                print(f"[GPTClientGenerator] ⚠️  Ошибка подключения к OpenAI: {e}")
    
    async def generate_client_message(
        self, 
        context: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None
    ) -> str:
        """Сгенерировать сообщение клиента через GPT"""
        
        if not self.openai_client:
            # Если GPT недоступен, использовать базовые сообщения
            return self._get_fallback_message()
        
        try:
            # Формируем промпт для GPT
            system_prompt = """Ты - девушка/женщина с типичными проблемами со здоровьем и красотой. 
Ты пишешь консультанту по здоровью, задаешь вопросы о своих проблемах.

Твои типичные проблемы:
- Проблемы с похудением (вес возвращается после диет)
- Проблемы с кожей лица (высыпания, воспаления, жирная кожа)
- Проблемы с волосами (выпадение, тусклость, ломкость)
- Целлюлит
- Усталость и недостаток энергии
- Гормональные проблемы
- Общее самочувствие

Пиши естественно, как настоящий клиент - короткими сообщениями, с эмоциями, задавай вопросы, рассказывай о своих проблемах.
НЕ пиши длинные тексты, пиши как обычный человек в мессенджере (1-2 предложения).
Используй эмодзи иногда, но не злоупотребляй."""
            
            user_prompt = "Напиши сообщение консультанту о своей проблеме со здоровьем или красотой."
            
            # Добавляем контекст, если есть
            if context:
                user_prompt += f"\nКонтекст: {context}"
            
            # Добавляем историю разговора, если есть
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            if conversation_history:
                # Добавляем последние несколько сообщений из истории
                for msg in conversation_history[-4:]:  # Последние 4 сообщения
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_prompt})
            
            # Вызов GPT API
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=150  # Короткие сообщения
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Очищаем текст от лишнего
            if generated_text:
                # Убираем кавычки если есть
                if generated_text.startswith('"') and generated_text.endswith('"'):
                    generated_text = generated_text[1:-1]
                return generated_text
            else:
                return self._get_fallback_message()
                
        except Exception as e:
            print(f"[GPTClientGenerator] ⚠️  Ошибка генерации через GPT: {e}")
            return self._get_fallback_message()
    
    async def generate_conversation_start(self) -> str:
        """Сгенерировать начало разговора"""
        return await self.generate_client_message(
            context="Начни разговор с консультантом. Представься или сразу расскажи о своей проблеме."
        )
    
    async def generate_followup_message(
        self, 
        bot_response: str,
        conversation_history: Optional[List[dict]] = None
    ) -> str:
        """Сгенерировать ответ на сообщение бота"""
        
        # Формируем историю для контекста
        if conversation_history is None:
            conversation_history = []
        
        # Добавляем ответ бота в историю
        conversation_history.append({"role": "assistant", "content": bot_response})
        
        return await self.generate_client_message(
            context=f"Бот ответил: {bot_response}. Ответь на его ответ - задай уточняющий вопрос или продолжай рассказывать о проблеме.",
            conversation_history=conversation_history
        )
    
    def _get_fallback_message(self) -> str:
        """Возвращает базовое сообщение, если GPT недоступен"""
        import random
        
        fallback_messages = [
            "Привет! Мне нужна помощь",
            "Здравствуйте, помогите пожалуйста",
            "У меня проблема с кожей",
            "Не могу похудеть, что делать?",
            "Волосы выпадают, помогите",
            "Чувствую постоянную усталость"
        ]
        
        return random.choice(fallback_messages)
    
    def is_available(self) -> bool:
        """Проверить, доступен ли GPT"""
        return self.openai_client is not None


# Глобальный экземпляр генератора
gpt_client_generator = GPTClientGenerator()

