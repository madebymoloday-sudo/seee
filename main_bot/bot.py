"""Основной бот - тот, который мы будем улучшать автоматически"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ВАЖНО: Импортируем настройки через безопасный загрузчик
# Это гарантирует, что настройки будут доступны даже если config перезаписан
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import get_our_settings
our_settings = get_our_settings()

USE_REAL_TELEGRAM = our_settings.USE_REAL_TELEGRAM
EMULATOR_MODE = our_settings.EMULATOR_MODE
MAIN_BOT_TOKEN = our_settings.MAIN_BOT_TOKEN

from emulator.telegram_emulator import emulator, Message
from main_bot.instagram_bot_adapter import get_instagram_bot_structure, INSTAGRAM_BOT_AVAILABLE

if USE_REAL_TELEGRAM and not EMULATOR_MODE:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    import telegram
else:
    # Режим эмуляции
    USE_REAL_TELEGRAM = False


class MainBot:
    """Основной бот - цель для улучшения"""
    
    def __init__(self):
        self.bot_id = "main_bot"
        self.errors = []  # Список ошибок для анализа
        
        # Попытаться загрузить структуру Instagram бота
        self.data_loader = None
        self.workflow = None
        self.quick_responses = None
        self.use_instagram_structure = False
        
        if INSTAGRAM_BOT_AVAILABLE:
            try:
                print(f"[MainBot] 🔄 Загрузка структуры Instagram бота...")
                self.data_loader, self.workflow, self.quick_responses = get_instagram_bot_structure()
                if self.workflow is not None:
                    self.use_instagram_structure = True
                    print(f"[MainBot] ✅ Используется структура Instagram бота (WorkflowManager + промпты)")
                    print(f"[MainBot]   - WorkflowManager: {self.workflow}")
                    print(f"[MainBot]   - DataLoader: {self.data_loader}")
                    print(f"[MainBot]   - QuickResponses: {self.quick_responses}")
                else:
                    print(f"[MainBot] ⚠️  Не удалось загрузить WorkflowManager, используется простая логика")
                    self.use_instagram_structure = False
            except Exception as e:
                print(f"[MainBot] ❌ Ошибка загрузки структуры Instagram бота: {e}")
                import traceback
                traceback.print_exc()
                self.use_instagram_structure = False
        else:
            print(f"[MainBot] ⚠️  Instagram бот недоступен, используется простая логика")
        
    async def handle_message(self, message: Message):
        """Обработка входящего сообщения"""
        try:
            text = message.text.strip()
            user_id = message.chat_id  # Используем chat_id как user_id
            
            # Генерация ответа (использует структуру Instagram бота если доступна)
            response = await self._generate_response(text, user_id)
            
            # Очистить ответ от системных сообщений перед отправкой
            if response:
                response = self._clean_system_text(response)
                # Если после очистки остался только системный текст, не отправлять
                if not response or len(response.strip()) < 5:
                    print(f"[MainBot] ⚠️  После очистки ответ стал пустым, пропускаю отправку")
                    return
            
            # Отправить ответ
            if USE_REAL_TELEGRAM:
                await self._send_real_message(message.chat_id, response)
            else:
                await emulator.send_message(
                    self.bot_id,
                    message.chat_id,
                    response,
                    reply_to_message_id=message.message_id
                )
                
        except Exception as e:
            error_info = {
                "error": str(e),
                "message": message.text,
                "chat_id": message.chat_id,
                "timestamp": message.timestamp
            }
            self.errors.append(error_info)
            
            # Не показывать техническую ошибку пользователю, используем fallback
            error_str = str(e)
            if "403" in error_str or "unsupported_country" in error_str.lower() or "PermissionDenied" in error_str:
                print(f"[MainBot] ⚠️  OpenAI API недоступен (регион): {e}")
                # Используем fallback вместо технической ошибки
                try:
                    fallback_response = await self._generate_simple_response(text.lower().strip())
                    error_response = fallback_response
                except:
                    error_response = "Извините, произошла техническая ошибка. Попробуйте написать позже."
            else:
                print(f"[MainBot] ОШИБКА: {e}")
                import traceback
                traceback.print_exc()
                # Отправить сообщение об ошибке
                # Проверяем, это ли ошибка OpenAI API (403, регион не поддерживается)
            error_str = str(e)
            is_openai_403 = (
                "403" in error_str or 
                "unsupported_country" in error_str.lower() or 
                "PermissionDenied" in error_str or
                "PermissionDeniedError" in error_str
            )
            
            if is_openai_403:
                # Для ошибок OpenAI API используем fallback вместо технической ошибки
                print(f"[MainBot] ⚠️  OpenAI API недоступен в handle_message, используем fallback")
                try:
                    fallback_response = await self._generate_simple_response(message.text.lower().strip())
                    error_response = fallback_response
                except Exception as fallback_error:
                    print(f"[MainBot] ⚠️  Fallback тоже упал: {fallback_error}")
                    error_response = "Извините, произошла техническая ошибка. Попробуйте написать позже."
            else:
                error_response = f"Извините, произошла ошибка. Попробуйте переформулировать вопрос."
            if USE_REAL_TELEGRAM:
                await self._send_real_message(message.chat_id, error_response)
            else:
                await emulator.send_message(
                    self.bot_id,
                    message.chat_id,
                    error_response
                )
    
    async def _generate_response(self, text: str, user_id: str = "default_user") -> str:
        """Генерация ответа на сообщение - использует структуру Instagram бота если доступна"""
        
        # Если доступна структура Instagram бота, используем её
        if self.use_instagram_structure and self.workflow is not None:
            try:
                print(f"[MainBot] 🔄 Генерация ответа через WorkflowManager для user_id={user_id}")
                
                # Получить текущий этап пользователя
                current_stage = self.workflow.get_user_stage(user_id)
                print(f"[MainBot] 📍 Текущий этап пользователя {user_id}: {current_stage}")
                
                # Сначала проверить быстрые ответы
                if self.quick_responses is not None:
                    quick_response = self.quick_responses.get_response(text)
                    if quick_response:
                        # Очистить быстрый ответ от системных сообщений Google
                        quick_response = self._clean_system_text(quick_response)
                        
                        print(f"[MainBot] ⚡ Использован быстрый ответ")
                        # Добавить в историю
                        if hasattr(self.workflow, 'user_conversations'):
                            conversation_history = self.workflow.user_conversations.get(user_id, [])
                            conversation_history.append({"role": "user", "content": text})
                            conversation_history.append({"role": "assistant", "content": quick_response})
                            self.workflow.user_conversations[user_id] = conversation_history
                        return quick_response
                
                # Использовать WorkflowManager для генерации ответа
                print(f"[MainBot] 🤖 Генерация ответа через WorkflowManager.generate_response...")
                print(f"[MainBot]   - user_id: {user_id}")
                print(f"[MainBot]   - text: {text[:100] if len(text) > 100 else text}")
                print(f"[MainBot]   - current_stage: {current_stage}")
                
                try:
                    # WorkflowManager.generate_response - синхронная функция
                    response = self.workflow.generate_response(user_id, text)
                    
                    if response and len(response.strip()) > 0:
                        # Очистить ответ от системных сообщений Google
                        response = self._clean_system_text(response)
                        
                        print(f"[MainBot] ✅ Получен ответ от WorkflowManager (длина: {len(response)} символов)")
                        new_stage = self.workflow.get_user_stage(user_id)
                        print(f"[MainBot] 📍 Новый этап пользователя: {new_stage}")
                        print(f"[MainBot]   - Ответ: {response[:150]}...")
                        return response
                    else:
                        print(f"[MainBot] ⚠️  WorkflowManager вернул пустой ответ, используем fallback")
                        # Fallback на простую логику
                        return await self._generate_simple_response(text)
                
                except Exception as workflow_error:
                    # Если GPT API недоступен (ошибка региона или другая ошибка)
                    error_str = str(workflow_error)
                    error_type = type(workflow_error).__name__
                    
                    # Проверяем различные типы ошибок OpenAI API
                    is_openai_error = (
                        "403" in error_str or 
                        "unsupported_country" in error_str.lower() or 
                        "PermissionDenied" in error_str or
                        "PermissionDeniedError" in error_type or
                        "OpenAI" in error_type or
                        "openai" in error_str.lower()
                    )
                    
                    if is_openai_error:
                        print(f"[MainBot] ⚠️  OpenAI API недоступен: {error_type}")
                        print(f"[MainBot] ⚠️  Причина: {error_str[:200]}")
                        print(f"[MainBot] ⚠️  Используем fallback логику вместо GPT")
                        # Используем fallback, но сохраняем этап для следующего раза
                        # При этом не считаем это критической ошибкой
                        fallback_response = await self._generate_simple_response(text)
                        # Очистить fallback ответ тоже
                        return self._clean_system_text(fallback_response) if fallback_response else fallback_response
                    else:
                        # Другая ошибка - логируем и пробрасываем дальше
                        print(f"[MainBot] ⚠️  Ошибка WorkflowManager: {error_type}: {error_str[:200]}")
                        raise
                    
            except Exception as e:
                print(f"[MainBot] ❌ Ошибка при использовании структуры Instagram бота: {e}")
                import traceback
                traceback.print_exc()
                # Fallback на простую логику
                fallback_response = await self._generate_simple_response(text)
                # Очистить fallback ответ
                return self._clean_system_text(fallback_response) if fallback_response else fallback_response
        else:
            print(f"[MainBot] ⚠️  Используется простая логика (use_instagram_structure={self.use_instagram_structure}, workflow={self.workflow is not None})")
            # Использовать простую логику
            simple_response = await self._generate_simple_response(text)
            # Очистить ответ
            return self._clean_system_text(simple_response) if simple_response else simple_response
    
    async def _generate_simple_response(self, text: str) -> str:
        """Простая логика генерации ответа (fallback)"""
        text_lower = text.lower()
        
        # Приветствия
        if any(word in text_lower for word in ["привет", "здравствуй", "здравствуйте", "добрый день", "добрый", "здарова"]):
            return "Здравствуйте! Очень рада помочь вам с вопросами о здоровье и красоте. Расскажите, что вас беспокоит?"
        
        # Вопросы о похудении
        if any(word in text_lower for word in ["похудеть", "лишний вес", "диета", "вес возвращается", "не могу похудеть"]):
            return "Понимаю вашу ситуацию с весом. Важно подходить к этому комплексно: сбалансированное питание, регулярная физическая активность и достаточный сон. Резкие диеты часто дают временный эффект. Можете рассказать подробнее о вашем образе жизни?"
        
        # Проблемы с кожей
        if any(word in text_lower for word in ["кожа", "высыпания", "воспаления", "акне", "прыщи", "жирная кожа"]):
            return "Проблемы с кожей часто связаны с питанием, уходом и гормональным фоном. Важно использовать подходящие средства ухода и следить за питанием - меньше сладкого и обработанной пищи. Есть ли у вас проблемы с циклом или другими симптомами?"
        
        # Проблемы с волосами
        if any(word in text_lower for word in ["волосы", "выпадают", "тусклые", "витамины для волос", "волосы стали хуже"]):
            return "Выпадение и тусклость волос могут быть связаны с нехваткой витаминов группы B, железа, цинка или с гормональными изменениями. Важно проверить уровень витаминов и обеспечить полноценное питание. Как давно началась проблема?"
        
        # Целлюлит
        if "целлюлит" in text_lower:
            return "Целлюлит - это нормальное явление, связанное с особенностями соединительной ткани. Помогают регулярные физические упражнения, особенно для ног, массаж, достаточное потребление воды и здоровое питание. Полностью избавиться сложно, но можно значительно улучшить."
        
        # Усталость и энергия
        if any(word in text_lower for word in ["усталость", "нет энергии", "устаю", "нет сил", "постоянно усталая"]):
            return "Хроническая усталость может быть связана с нехваткой железа, витамина D, проблемами со сном или стрессом. Важно проверить уровень витаминов, наладить режим сна и обеспечить полноценное питание."
        
        # Гормоны
        if any(word in text_lower for word in ["гормоны", "гормональные", "цикл", "нерегулярный"]):
            return "Гормональные проблемы могут влиять и на вес, и на кожу, и на общее самочувствие. При нарушениях цикла и проблемах с кожей рекомендую обратиться к гинекологу-эндокринологу для проверки гормонального фона."
        
        # Быстро похудеть (может быть ошибкой - неправильный подход)
        if "быстро похудеть" in text_lower or "похудеть быстро" in text_lower:
            return "Быстрое похудение часто вредит здоровью и дает временный эффект. Лучше худеть постепенно - 0.5-1 кг в неделю, сочетая правильное питание и физическую активность. Это поможет сохранить результат."
        
        # Общие вопросы
        if "?" in text or any(word in text_lower for word in ["что делать", "как", "посоветуйте", "помогите"]):
            return "Я постараюсь помочь! Можете уточнить, что именно вас беспокоит? Это поможет дать более точные рекомендации."
        
        # Не понял вопрос
        return "Извините, я не совсем поняла ваш вопрос. Можете переформулировать? Я помогаю с вопросами о похудении, коже, волосах и общем здоровье."
    
    def _clean_system_text(self, text: str) -> str:
        """Очистить текст от системных сообщений Google Sheets и других служебных данных"""
        if not text:
            return ""
        
        import re
        
        text = str(text).strip()
        
        # Удаляем системные сообщения Google Sheets
        system_patterns = [
            r'ИИ[- ]?Коммуникатор\s*ИИ[- ]?Коммуникатор\s*\d{1,3}%',
            r'ИИ[- ]?Коммуникатор\s*\d{1,3}%',
            r'ИИ[- ]?Коммуникатор[^\n]*',
            r'\d{1,3}%\s*$',  # Процент в конце строки
            r'Включить программу чтения с экрана[^\n]*',
            r'Чтобы включить программу чтения с экрана[^\n]*',
            r'Для просмотра списка быстрых клавиш[^\n]*',
            r'⌘\+?Option\+?Z[^\n]*',
            r'⌘\+?Option[^\n]*',
            r'⌘косая черта[^\n]*',
            r'⌘[^\n]*',
            r'Option\+?Z[^\n]*',
            r'Option[^\n]*',
            r'Для просмотра[^\n]*',
            r'списка быстрых клавиш[^\n]*',
            r'нажмите[^\n]*⌘[^\n]*',
            r'нажмите[^\n]*Option[^\n]*',
            r'HYPERLINK[^\n]*',
            r'\[HYPERLINK[^\]]*\]',
            r'logger\.[^\n]*',
            r'print\([^\n]*\)',
            r'ERROR[^\n]*',
            r'WARNING[^\n]*',
            r'INFO[^\n]*',
        ]
        
        for pattern in system_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Сокращаем множественные переносы (больше 2 подряд) до двойных
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Удаляем пробелы в начале и конце каждой строки, но сохраняем структуру переносов
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped:
                cleaned_lines.append(line_stripped)
            else:
                # Сохраняем пустые строки для структуры, но не больше одной подряд
                if not cleaned_lines or cleaned_lines[-1]:
                    cleaned_lines.append('')
        
        text = '\n'.join(cleaned_lines)
        
        # Удаляем пробелы в начале и конце
        text = text.strip()
        
        # Если после очистки осталось меньше 10 символов, возможно это был только системный текст
        if len(text) < 10:
            return ""
        
        return text
    
    async def _send_real_message(self, chat_id: str, text: str):
        """Отправить сообщение через реальный Telegram API"""
        # Реализация для реального Telegram
        pass
    
    def get_errors(self):
        """Получить список ошибок"""
        return self.errors
    
    def clear_errors(self):
        """Очистить список ошибок"""
        self.errors = []


# Инициализация и запуск
async def run_bot():
    bot = MainBot()
    
    if USE_REAL_TELEGRAM and not EMULATOR_MODE:
        # Реальный Telegram
        application = Application.builder().token(MAIN_BOT_TOKEN).build()
        
        async def handle_real_message(update: Update, context):
            if update.message:
                # Преобразовать в формат Message для совместимости
                msg = Message(
                    message_id=update.message.message_id,
                    chat_id=str(update.message.chat.id),
                    from_bot_id="user",
                    text=update.message.text or ""
                )
                await bot.handle_message(msg)
        
        application.add_handler(MessageHandler(filters.TEXT, handle_real_message))
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
    else:
        # Режим эмуляции
        emulator.register_bot(bot.bot_id, bot.handle_message)
        print(f"[MainBot] Бот запущен в режиме эмуляции")
    
    return bot


if __name__ == "__main__":
    asyncio.run(run_bot())

