"""Эмулятор Telegram API для локального тестирования ботов"""
import asyncio
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    """Модель сообщения в эмуляторе"""
    message_id: int
    chat_id: str
    from_bot_id: str
    text: str
    timestamp: float = field(default_factory=time.time)
    reply_to_message_id: Optional[int] = None

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "chat": {"id": self.chat_id},
            "from": {"id": self.from_bot_id, "is_bot": True},
            "text": self.text,
            "date": int(self.timestamp),
        }


class TelegramEmulator:
    """Эмулятор Telegram API - позволяет ботам общаться локально"""
    
    def __init__(self):
        self.messages: Dict[str, List[Message]] = {}  # chat_id -> messages
        self.bots: Dict[str, Callable] = {}  # bot_id -> handler function
        self.message_counter = 0
        self.handlers: List[Callable] = []  # Глобальные обработчики сообщений
        
    def register_bot(self, bot_id: str, handler: Callable):
        """Регистрация бота в эмуляторе"""
        self.bots[bot_id] = handler
        print(f"[Emulator] Зарегистрирован бот: {bot_id}")
    
    def add_message_handler(self, handler: Callable):
        """Добавить обработчик сообщений (для логирования)"""
        self.handlers.append(handler)
    
    async def send_message(
        self, 
        bot_id: str, 
        chat_id: str, 
        text: str,
        reply_to_message_id: Optional[int] = None
    ) -> Message:
        """Отправить сообщение от бота"""
        self.message_counter += 1
        message = Message(
            message_id=self.message_counter,
            chat_id=chat_id,
            from_bot_id=bot_id,
            text=text,
            reply_to_message_id=reply_to_message_id
        )
        
        # Сохранить сообщение
        if chat_id not in self.messages:
            self.messages[chat_id] = []
        self.messages[chat_id].append(message)
        
        # Вызвать обработчики
        for handler in self.handlers:
            try:
                await handler(message)
            except Exception as e:
                print(f"[Emulator] Ошибка в обработчике: {e}")
        
        # Если есть другой бот в этом чате, уведомить его
        await self._notify_other_bots(chat_id, message)
        
        # Не печатать здесь - веб-интерфейс или чат-вьювер покажет сообщение
        return message
    
    async def _notify_other_bots(self, chat_id: str, message: Message):
        """Уведомить других ботов о новом сообщении"""
        for other_bot_id, handler in self.bots.items():
            if other_bot_id != message.from_bot_id:
                try:
                    # Имитация получения сообщения от Telegram
                    await handler(message)
                except Exception as e:
                    print(f"[Emulator] Ошибка при уведомлении бота {other_bot_id}: {e}")
    
    def get_messages(self, chat_id: str) -> List[Message]:
        """Получить все сообщения в чате"""
        return self.messages.get(chat_id, [])
    
    def get_last_message(self, chat_id: str) -> Optional[Message]:
        """Получить последнее сообщение в чате"""
        messages = self.get_messages(chat_id)
        return messages[-1] if messages else None
    
    def clear_chat(self, chat_id: str):
        """Очистить историю чата"""
        if chat_id in self.messages:
            self.messages[chat_id] = []
            print(f"[Emulator] Чат {chat_id} очищен")
    
    def get_stats(self) -> Dict:
        """Получить статистику эмулятора"""
        total_messages = sum(len(msgs) for msgs in self.messages.values())
        return {
            "total_chats": len(self.messages),
            "total_messages": total_messages,
            "registered_bots": list(self.bots.keys())
        }


# Глобальный экземпляр эмулятора
emulator = TelegramEmulator()

