"""Интерфейс для просмотра переписки ботов в реальном времени"""
import os
import sys
from datetime import datetime
from typing import List
from emulator.telegram_emulator import Message


class ChatViewer:
    """Красивый интерфейс для просмотра переписки"""
    
    # ANSI коды для цветов
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Цвета для разных участников
    CLIENT_COLOR = "\033[94m"  # Синий
    BOT_COLOR = "\033[92m"     # Зеленый
    ERROR_COLOR = "\033[91m"   # Красный
    TIME_COLOR = "\033[90m"    # Серый
    
    def __init__(self, chat_id: str = "test_chat_1"):
        self.chat_id = chat_id
        self.displayed_messages = set()  # ID уже показанных сообщений
        
    def clear_screen(self):
        """Очистить экран"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self):
        """Печатать заголовок чата"""
        print("=" * 70)
        print(f"{self.BOLD}{'💬 ЧАТ БОТОВ - ЛОКАЛЬНЫЙ ЭМУЛЯТОР':^68}{self.RESET}")
        print("=" * 70)
        print(f"{self.TIME_COLOR}👤 Клиент (тестовый)  |  🤖 Бот (основной){self.RESET}")
        print("-" * 70)
        print()
    
    def format_message(self, message: Message) -> str:
        """Форматировать сообщение для отображения"""
        timestamp = datetime.fromtimestamp(message.timestamp).strftime("%H:%M:%S")
        
        if message.from_bot_id == "main_bot":
            # Сообщение от основного бота
            name = "🤖 Бот"
            color = self.BOT_COLOR
            indent = ""
        elif message.from_bot_id == "test_client":
            # Сообщение от клиента
            name = "👤 Клиент"
            color = self.CLIENT_COLOR
            indent = ""
        else:
            name = "❓ Неизвестный"
            color = self.RESET
            indent = ""
        
        # Форматирование текста сообщения
        text = message.text
        max_width = 60
        wrapped_text = self._wrap_text(text, max_width)
        
        # Собрать сообщение
        formatted = f"{self.TIME_COLOR}[{timestamp}]{self.RESET} "
        formatted += f"{color}{self.BOLD}{name}{self.RESET}\n"
        
        # Текст с отступом
        for line in wrapped_text:
            formatted += f"{' ' * 12}{color}{line}{self.RESET}\n"
        
        return formatted
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Разбить текст на строки по ширине"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += (word + " ") if current_line else word
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word
        if current_line:
            lines.append(current_line.strip())
        
        return lines if lines else [text]
    
    def display_message(self, message: Message):
        """Отобразить одно сообщение"""
        if message.message_id in self.displayed_messages:
            return  # Уже показано
        
        self.displayed_messages.add(message.message_id)
        formatted = self.format_message(message)
        print(formatted)
        print()  # Пустая строка между сообщениями
    
    def display_chat(self, messages: List[Message]):
        """Отобразить весь чат"""
        self.clear_screen()
        self.print_header()
        
        for message in messages:
            if message.message_id not in self.displayed_messages:
                self.display_message(message)
    
    def display_update(self, new_message: Message):
        """Обновить чат новым сообщением"""
        self.display_message(new_message)
    
    def display_error(self, error_text: str):
        """Отобразить ошибку"""
        print(f"{self.ERROR_COLOR}⚠️  {error_text}{self.RESET}\n")
    
    def display_info(self, info_text: str):
        """Отобразить информационное сообщение"""
        print(f"{self.TIME_COLOR}ℹ️  {info_text}{self.RESET}\n")
    
    def display_summary(self, total_messages: int, errors: int):
        """Отобразить итоговую статистику"""
        print("-" * 70)
        print(f"{self.BOLD}📊 Статистика:{self.RESET}")
        print(f"   Всего сообщений: {total_messages}")
        print(f"   Ошибок найдено: {errors}")
        print("=" * 70)


# Глобальный экземпляр просмотрщика
chat_viewer = ChatViewer()

