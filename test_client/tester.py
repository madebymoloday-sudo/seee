"""Тестовый клиент - отправляет сообщения основному боту и проверяет ответы"""
import asyncio
import sys
import os
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем настройки через безопасный загрузчик
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_our_settings
our_settings = get_our_settings()
EMULATOR_MODE = our_settings.EMULATOR_MODE
USE_REAL_TELEGRAM = our_settings.USE_REAL_TELEGRAM
from emulator.telegram_emulator import emulator, Message
from test_client.gpt_client_generator import gpt_client_generator


class TestClient:
    """Клиент для тестирования основного бота"""
    
    def __init__(self, chat_id: str = "test_chat_1", use_gpt: bool = True):
        self.bot_id = "test_client"
        self.chat_id = chat_id
        self.conversations = []  # История всех диалогов
        self.errors_found = []  # Найденные ошибки
        self.use_gpt = use_gpt and gpt_client_generator.is_available()  # Использовать GPT если доступен
        self.conversation_history = []  # История для GPT
        
    async def send_test_message(self, text: str) -> Optional[Message]:
        """Отправить тестовое сообщение"""
        # Не печатать здесь - чат-вьювер покажет сообщение
        
        if USE_REAL_TELEGRAM and not EMULATOR_MODE:
            # Реальный Telegram (будущая реализация)
            pass
        else:
            # Эмулятор
            message = await emulator.send_message(
                self.bot_id,
                self.chat_id,
                text
            )
            
            # Подождать ответа от бота
            await asyncio.sleep(1.5)  # Больше времени для ответа бота
            
            return message
    
    async def run_test_scenario(self, scenario: Optional[List[str]] = None) -> Dict:
        """Запустить сценарий тестирования"""
        
        # Если используется GPT, генерируем динамический сценарий
        if self.use_gpt and scenario is None:
            scenario = await self._generate_gpt_scenario()
        
        # Если сценарий не передан, используем базовые
        if scenario is None:
            scenario = ["Привет! Мне нужна помощь"]
        
        conversation = {
            "scenario": scenario,
            "responses": [],
            "errors": [],
            "timestamp": asyncio.get_event_loop().time(),
            "uses_gpt": self.use_gpt
        }
        
        # Очистить историю для нового сценария
        self.conversation_history = []
        
        for i, test_message in enumerate(scenario):
            # Отправить сообщение клиента
            await self.send_test_message(test_message)
            
            # Добавить в историю для GPT
            self.conversation_history.append({"role": "user", "content": test_message})
            
            # Подождать немного больше для ответа бота
            await asyncio.sleep(2)
            
            # Получить все сообщения из чата
            messages = emulator.get_messages(self.chat_id)
            
            # Найти последний ответ основного бота на это сообщение
            if len(messages) >= 2:
                # Ищем последнее сообщение от main_bot после сообщения клиента
                client_msg_idx = -1
                for idx, msg in enumerate(messages):
                    if msg.from_bot_id == self.bot_id and msg.text == test_message:
                        client_msg_idx = idx
                        break
                
                if client_msg_idx >= 0:
                    # Ищем следующий ответ от main_bot
                    for msg in messages[client_msg_idx+1:]:
                        if msg.from_bot_id == "main_bot":
                            response = {
                                "test_message": test_message,
                                "response": msg.text,
                                "message_id": msg.message_id
                            }
                            conversation["responses"].append(response)
                            
                            # Добавить ответ бота в историю для GPT
                            self.conversation_history.append({"role": "assistant", "content": msg.text})
                            
                            # Проверить на ошибки
                            error = self._check_for_errors(test_message, msg.text)
                            if error:
                                conversation["errors"].append(error)
                                self.errors_found.append(error)
                            
                            # Если используется GPT, генерируем следующий вопрос динамически
                            if self.use_gpt and i < 2:  # Генерируем еще 2-3 вопроса максимум
                                next_message = await gpt_client_generator.generate_followup_message(
                                    msg.text,
                                    self.conversation_history.copy()
                                )
                                if next_message and next_message not in scenario:
                                    scenario.append(next_message)
                            
                            break
        
        # Небольшая пауза между сообщениями в сценарии
        await asyncio.sleep(0.5)
        
        self.conversations.append(conversation)
        return conversation
    
    async def _generate_gpt_scenario(self) -> List[str]:
        """Сгенерировать сценарий через GPT"""
        scenario = []
        
        # Первое сообщение
        first_message = await gpt_client_generator.generate_conversation_start()
        scenario.append(first_message)
        
        return scenario
    
    def _check_for_errors(self, test_message: str, response: str) -> Optional[Dict]:
        """Проверить ответ на ошибки"""
        errors = []
        
        # Проверка 1: Пустой ответ
        if not response or len(response.strip()) == 0:
            errors.append("Пустой ответ")
        
        # Проверка 2: Сообщение об ошибке
        if "ошибка" in response.lower() or "error" in response.lower():
            errors.append("Бот сообщил об ошибке")
        
        # Проверка 3: Нерелевантный ответ (очень простой анализ)
        if "не понял" in response.lower() and len(test_message) > 5:
            errors.append("Бот не понял простое сообщение")
        
        # Проверка 4: Слишком короткий ответ на длинный вопрос
        if len(test_message) > 20 and len(response) < 10:
            errors.append("Слишком короткий ответ на длинный вопрос")
        
        if errors:
            return {
                "test_message": test_message,
                "response": response,
                "errors": errors
            }
        
        return None
    
    def get_test_report(self) -> Dict:
        """Получить отчет о тестировании"""
        total_tests = sum(len(conv["scenario"]) for conv in self.conversations)
        total_errors = sum(len(conv["errors"]) for conv in self.conversations)
        
        return {
            "total_conversations": len(self.conversations),
            "total_tests": total_tests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_tests if total_tests > 0 else 0,
            "errors": self.errors_found
        }


# Сценарии тестирования - имитация клиентки с вопросами о здоровье и красоте
DEFAULT_TEST_SCENARIOS = [
    # Сценарий 1: Похудение
    [
        "Привет! Мне нужна помощь",
        "Я не могу похудеть уже полгода, пробовала диеты, но вес возвращается",
        "Что делать? Может быть проблема в гормонах?",
        "Как мне начать худеть правильно?"
    ],
    # Сценарий 2: Проблемы с кожей
    [
        "Здравствуйте",
        "У меня проблемы с кожей лица - высыпания и воспаления",
        "Кожа жирная и блестит, особенно на лбу и носу",
        "Что посоветуете? Может питание влияет?"
    ],
    # Сценарий 3: Проблемы с волосами
    [
        "Добрый день",
        "Мои волосы сильно выпадают и стали тусклыми",
        "Раньше были густые и блестящие, а сейчас как солома",
        "Может нужны витамины? Какие?"
    ],
    # Сценарий 4: Комплексные вопросы
    [
        "Привет, помогите пожалуйста",
        "Я хочу похудеть, но еще у меня кожа стала хуже и волосы выпадают",
        "Все это началось после того как я села на строгую диету",
        "Что вы посоветуете? Может мне нужно к врачу?"
    ],
    # Сценарий 5: Целлюлит
    [
        "Здравствуйте",
        "У меня целлюлит на бедрах и ногах",
        "Пробовала кремы, массажи, но не помогает",
        "Можно ли от него избавиться навсегда?"
    ],
    # Сценарий 6: Общее здоровье
    [
        "Добрый день!",
        "Я постоянно чувствую усталость и нет энергии",
        "Сплю плохо, просыпаюсь разбитой",
        "И еще аппетит плохой, хотя хочу похудеть"
    ],
    # Сценарий 7: Гормональные вопросы
    [
        "Привет",
        "Мне кажется у меня проблемы с гормонами",
        "У меня нерегулярный цикл и кожа стала хуже",
        "Может ли это влиять на вес?"
    ],
    # Сценарий 8: Быстрые вопросы
    [
        "Как быстро похудеть?",
        "Какие витамины для волос лучше?",
        "Что есть чтобы кожа была чистой?"
    ]
]


async def run_tests(use_gpt: bool = True):
    """Запустить набор тестов"""
    client = TestClient(use_gpt=use_gpt)
    
    # Если GPT доступен, используем смешанный подход: часть сценариев статическая, часть генерируется
    if client.use_gpt:
        print(f"\n[TestClient] 🤖 Используется GPT для генерации сообщений клиента (модель: {gpt_client_generator.model})")
        # Запускаем несколько GPT-сценариев
        for i in range(3):
            await client.run_test_scenario()  # Генерируем динамически
            await asyncio.sleep(1)
        
        # И несколько статических для сравнения
        for scenario in DEFAULT_TEST_SCENARIOS[:2]:
            await client.run_test_scenario(scenario)
            await asyncio.sleep(0.5)
    else:
        print(f"\n[TestClient] ⚠️  GPT недоступен, используются статические сценарии")
        for scenario in DEFAULT_TEST_SCENARIOS:
            await client.run_test_scenario(scenario)
            await asyncio.sleep(0.5)
    
    report = client.get_test_report()
    print(f"\n[TestClient] Отчет о тестировании:")
    print(f"  Тестов пройдено: {report['total_tests']}")
    print(f"  Ошибок найдено: {report['total_errors']}")
    print(f"  Процент ошибок: {report['error_rate']*100:.2f}%")
    
    return client


async def run_tests_sync():
    """Запустить набор тестов (синхронная версия для совместимости)"""
    return await run_tests()


if __name__ == "__main__":
    # Регистрация тестового клиента в эмуляторе (только для логирования)
    asyncio.run(run_tests())

