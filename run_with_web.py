"""Запуск системы с веб-интерфейсом и автоматическим циклом улучшения"""
import asyncio
import threading
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_bot.bot import run_bot as run_main_bot, MainBot
from test_client.tester import TestClient
try:
    from test_client.tester import DEFAULT_TEST_SCENARIOS
except ImportError:
    DEFAULT_TEST_SCENARIOS = []
from monitor.error_tracker import error_tracker
from improvement_agent.analyzer import error_analyzer
from improvement_agent.updater import code_updater
from emulator.telegram_emulator import emulator
from web_server import web_chat_viewer, improvement_status, run_web_server


async def improvement_cycle_with_restart(main_bot_instance=None):
    """Один цикл улучшения с автоматическим перезапуском бота"""
    
    print(f"[ImprovementCycle] 🔄 Начало цикла улучшения...")
    print(f"[ImprovementCycle] 📝 Логирование в консоль и веб-интерфейс")
    
    # 1. Запустить/перезапустить основной бот
    try:
        improvement_status.update({
            "status": "running",
            "errors_found": 0,
            "fixes_applied": 0
        })
        print(f"[ImprovementCycle] ✅ Статус обновлен на 'running'")
    except Exception as e:
        print(f"[ImprovementCycle] ⚠️  Ошибка обновления статуса: {e}")
    
    try:
        web_chat_viewer.add_info("🔄 Запуск/перезапуск основного бота...")
        print(f"[ImprovementCycle] ✅ Сообщение отправлено в веб-интерфейс")
    except Exception as e:
        print(f"[ImprovementCycle] ⚠️  Ошибка отправки сообщения в веб-интерфейс: {e}")
        import traceback
        traceback.print_exc()
    
    # Очистить старую регистрацию бота в эмуляторе
    if "main_bot" in emulator.bots:
        del emulator.bots["main_bot"]
    
    # Создать новый экземпляр бота (с обновленным кодом если были изменения)
    # Если код был изменен, Python автоматически перезагрузит модуль при следующем импорте
    main_bot = await run_main_bot()
    
    # Подключить обработчики
    async def monitor_handler(message):
        await error_tracker.handle_message(message)
    emulator.add_message_handler(monitor_handler)
    
    async def web_chat_handler(message):
        web_chat_viewer.add_message(message)
    emulator.add_message_handler(web_chat_handler)
    
    await asyncio.sleep(0.5)
    
    # 2. Запустить тесты
    print(f"[ImprovementCycle] 🧪 Запуск тестирования...")
    web_chat_viewer.add_info("🧪 Запуск тестирования...")
    
    from test_client.gpt_client_generator import gpt_client_generator
    use_gpt = gpt_client_generator.is_available()
    print(f"[ImprovementCycle] GPT доступен: {use_gpt}")
    
    if use_gpt:
        web_chat_viewer.add_info(f"🤖 GPT генератор подключен (модель: {gpt_client_generator.model})")
    else:
        web_chat_viewer.add_info("ℹ️  Используются статические сценарии")
    
    print(f"[ImprovementCycle] Создание TestClient...")
    test_client = TestClient(use_gpt=use_gpt)
    print(f"[ImprovementCycle] TestClient создан, запуск сценариев...")
    
    # Запустить сценарии тестирования
    if use_gpt:
        # GPT + статические сценарии
        for i in range(2):
            web_chat_viewer.add_info(f"📋 GPT сценарий {i+1}/2")
            await test_client.run_test_scenario()
            await asyncio.sleep(1)
        
        for scenario in DEFAULT_TEST_SCENARIOS[:2]:
            await test_client.run_test_scenario(scenario)
            await asyncio.sleep(1)
    else:
        # Только статические
        for scenario in DEFAULT_TEST_SCENARIOS[:3]:
            await test_client.run_test_scenario(scenario)
            await asyncio.sleep(1)
    
    test_report = test_client.get_test_report()
    
    # 3. Логировать диалоги
    for conversation in test_client.conversations:
        await error_tracker.log_conversation(conversation)
    
    improvement_status.update({
        "errors_found": test_report['total_errors']
    })
    
    # 4. Анализ ошибок
    if test_report['total_errors'] > 0:
        improvement_status.update({"status": "improving"})
        
        # Уведомление: Агент начал работу
        web_chat_viewer.add_agent_notification(
            title="🚀 Агент начал процесс улучшения",
            message=f"Найдено {test_report['total_errors']} ошибок. Начинаю анализ...",
            notification_type="starting",
            details=f"Всего ошибок: {test_report['total_errors']}"
        )
        
        web_chat_viewer.add_info(f"🔍 Анализ {test_report['total_errors']} найденных ошибок...")
        
        # Уведомление: Анализ начат
        web_chat_viewer.add_agent_notification(
            title="🔍 Анализ ошибок",
            message="Анализирую ошибки и генерирую предложения по исправлению...",
            notification_type="analyzing"
        )
        
        analysis = await error_analyzer.analyze_errors()
        
        # 5. Применить исправления
        fixes = analysis.get("code_fixes", [])
        if fixes:
            # Уведомление: Применение исправлений
            web_chat_viewer.add_agent_notification(
                title="🔧 Применение исправлений",
                message=f"Найдено {len(fixes)} исправлений. Начинаю применение...",
                notification_type="applying",
                details=f"Количество исправлений: {len(fixes)}"
            )
            
            web_chat_viewer.add_info(f"🔧 Применение {len(fixes)} исправлений...")
            update_result = await code_updater.apply_fixes(fixes)
            
            if update_result['fixes_applied'] > 0:
                improvement_status.update({
                    "fixes_applied": update_result['fixes_applied'],
                    "status": "success"
                })
                
                # Уведомление: Исправления применены успешно
                git_info = ""
                if update_result.get('git_committed'):
                    if update_result.get('git_pushed'):
                        git_info = f"\n📤 Изменения автоматически отправлены в Git ({update_result.get('git_branch', 'main')})"
                        web_chat_viewer.add_agent_notification(
                            title="📤 Изменения отправлены в Git",
                            message=f"Код автоматически закоммичен и отправлен в GitHub. Railway обновится автоматически.",
                            notification_type="success",
                            details=f"Ветка: {update_result.get('git_branch', 'main')}"
                        )
                    else:
                        git_info = "\n⚠️ Изменения закоммичены локально, но не отправлены в remote"
                else:
                    git_info = "\n⚠️ Автоматический коммит не выполнен"
                
                web_chat_viewer.add_agent_notification(
                    title="✅ Исправления применены!",
                    message=f"Успешно применено {update_result['fixes_applied']} исправлений в коде.{git_info}",
                    notification_type="success",
                    details=f"Перезапускаю бота с обновленным кодом..."
                )
                
                web_chat_viewer.add_info(f"✨ Применено {update_result['fixes_applied']} исправлений!")
                web_chat_viewer.add_info("🔄 Перезапуск бота с новым кодом...")
                return {
                    "status": "improved",
                    "fixes_applied": update_result['fixes_applied'],
                    "main_bot": main_bot,
                    "restart_needed": True
                }
            else:
                # Уведомление: Исправления не применены
                web_chat_viewer.add_agent_notification(
                    title="⚠️ Исправления не применены",
                    message="Не удалось применить исправления к коду.",
                    notification_type="error",
                    details="Проверьте логи для подробностей."
                )
    else:
        improvement_status.update({"status": "success"})
        
        # Уведомление: Ошибок не найдено
        web_chat_viewer.add_agent_notification(
            title="🎉 Ошибок не найдено!",
            message="Бот работает отлично, ошибок не обнаружено.",
            notification_type="success",
            details="Продолжаю мониторинг..."
        )
        
        web_chat_viewer.add_info("🎉 Ошибок не найдено! Бот работает отлично!")
        return {
            "status": "no_errors",
            "main_bot": main_bot,
            "restart_needed": False
        }
    
    return {
        "status": "completed",
        "main_bot": main_bot,
        "restart_needed": False
    }


async def continuous_improvement_loop(max_cycles: int = 10, delay_between_cycles: int = 5):
    """Непрерывный цикл улучшения с веб-интерфейсом"""
    
    print(f"[ContinuousLoop] 🚀 Запуск цикла улучшения (максимум {max_cycles} циклов)")
    print(f"[ContinuousLoop] 📝 Логирование в консоль и веб-интерфейс")
    
    try:
        improvement_status.update({
            "status": "idle",
            "current_cycle": 0,
            "total_cycles": max_cycles
        })
        print(f"[ContinuousLoop] ✅ Статус обновлен")
    except Exception as e:
        print(f"[ContinuousLoop] ⚠️  Ошибка обновления статуса: {e}")
    
    try:
        web_chat_viewer.add_info(f"🚀 Запуск автоматического цикла улучшения (максимум {max_cycles} циклов)")
        print(f"[ContinuousLoop] ✅ Сообщение отправлено в веб-интерфейс")
    except Exception as e:
        print(f"[ContinuousLoop] ⚠️  Ошибка отправки сообщения в веб-интерфейс: {e}")
        import traceback
        traceback.print_exc()
    
    main_bot_instance = None
    
    for cycle in range(1, max_cycles + 1):
        print(f"\n[ContinuousLoop] =========================================")
        print(f"[ContinuousLoop] ЦИКЛ #{cycle}/{max_cycles}")
        print(f"[ContinuousLoop] =========================================")
        improvement_status.update({"current_cycle": cycle})
        web_chat_viewer.add_info(f"\n{'='*60}")
        web_chat_viewer.add_info(f"ЦИКЛ #{cycle}/{max_cycles} - {datetime.now().strftime('%H:%M:%S')}")
        web_chat_viewer.add_info(f"{'='*60}")
        
        try:
            result = await improvement_cycle_with_restart(main_bot_instance)
            main_bot_instance = result.get("main_bot")
            
            if result.get("status") == "no_errors":
                print(f"[ContinuousLoop] 🎉 Цикл {cycle}: Ошибок не найдено! Бот совершенен!")
                web_chat_viewer.add_info(f"\n🎉 Цикл {cycle}: Ошибок не найдено! Бот совершенен!")
                improvement_status.update({"status": "success"})
                # НЕ останавливаться, продолжить тестирование
                # break  # Закомментировано - продолжаем циклы
            
            if result.get("status") == "improved" and result.get("restart_needed"):
                print(f"[ContinuousLoop] ✨ Цикл {cycle}: Бот улучшен! Применено {result.get('fixes_applied', 0)} исправлений")
                web_chat_viewer.add_info(f"\n✨ Цикл {cycle}: Бот улучшен! Применено {result.get('fixes_applied', 0)} исправлений")
                # Бот уже перезапущен в improvement_cycle_with_restart
                # Очистить чат для следующего цикла
                emulator.clear_chat("test_chat_1")
                if main_bot_instance:
                    main_bot_instance.clear_errors()
                
                # Небольшая пауза после улучшения
                if cycle < max_cycles:
                    print(f"[ContinuousLoop] ⏳ Пауза {delay_between_cycles} секунд перед следующим циклом...")
                    web_chat_viewer.add_info(f"⏳ Пауза {delay_between_cycles} секунд перед следующим циклом...")
                    await asyncio.sleep(delay_between_cycles)
                continue
            
            # Очистить чат для следующего цикла (если не было улучшения)
            print(f"[ContinuousLoop] Очистка чата и подготовка к следующему циклу...")
            emulator.clear_chat("test_chat_1")
            if main_bot_instance:
                main_bot_instance.clear_errors()
            
            if cycle < max_cycles:
                print(f"[ContinuousLoop] ⏳ Пауза {delay_between_cycles} секунд перед следующим циклом...")
                web_chat_viewer.add_info(f"⏳ Пауза {delay_between_cycles} секунд перед следующим циклом...")
                await asyncio.sleep(delay_between_cycles)
            else:
                print(f"[ContinuousLoop] ✅ Достигнут максимум циклов ({max_cycles}), завершаем...")
        
        except KeyboardInterrupt:
            web_chat_viewer.add_info("\n⏹️  Остановка по запросу пользователя")
            break
        except Exception as e:
            improvement_status.update({"status": "error"})
            error_msg = str(e)
            error_type = type(e).__name__
            
            print(f"[ContinuousLoop] ❌ Ошибка в цикле {cycle}: {error_type}: {error_msg[:200]}")
            
            # Игнорируем Broken pipe ошибки (это нормально при закрытии соединений)
            if "Broken pipe" in error_msg or "Errno 32" in error_msg:
                print(f"[ContinuousLoop] ⚠️  Broken pipe ошибка (нормально при закрытии соединений), продолжаю...")
                web_chat_viewer.add_info(f"⚠️  Временная ошибка соединения в цикле {cycle}, продолжаю...")
            else:
                web_chat_viewer.add_info(f"❌ Ошибка в цикле {cycle}: {error_type}: {error_msg[:100]}")
                import traceback
                traceback.print_exc()
            
            # Продолжить цикл даже при ошибке
            if cycle < max_cycles:
                print(f"[ContinuousLoop] ⚠️  Продолжаю цикл несмотря на ошибку...")
                if "Broken pipe" not in error_msg:
                    web_chat_viewer.add_info(f"⚠️  Продолжаю цикл несмотря на ошибку...")
                await asyncio.sleep(5)  # Пауза перед повтором
            else:
                print(f"[ContinuousLoop] ✅ Достигнут максимум циклов, завершаем...")
                break
    
    # Финальная статистика
    error_summary = error_tracker.get_error_summary()
    web_chat_viewer.add_info("\n" + "="*60)
    web_chat_viewer.add_info("🏁 СИСТЕМА ЗАВЕРШИЛА РАБОТУ")
    web_chat_viewer.add_info("="*60)
    web_chat_viewer.add_info(f"📊 Всего ошибок зафиксировано: {error_summary['total_errors']}")
    web_chat_viewer.add_info(f"📈 Типы ошибок: {error_summary['error_types']}")
    
    improvement_status.update({"status": "idle"})


def run_improvement_in_thread():
    """Запустить цикл улучшения в отдельном потоке"""
    import threading
    thread_name = threading.current_thread().name
    print(f"[{thread_name}] 🔄 Запуск цикла улучшения...")
    print(f"[{thread_name}] 📝 Поток ID: {threading.get_ident()}")
    
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print(f"[{thread_name}] ✅ Event loop создан")
        
        # Добавляем сообщение в веб-интерфейс сразу при запуске
        try:
            from web_server import web_chat_viewer
            web_chat_viewer.add_info("🔄 Цикл улучшения запускается...")
            print(f"[{thread_name}] ✅ Сообщение отправлено в веб-интерфейс")
        except Exception as e:
            print(f"[{thread_name}] ⚠️  Не удалось отправить сообщение в веб-интерфейс: {e}")
            import traceback
            traceback.print_exc()
        
        # Запускаем цикл с логированием
        print(f"[{thread_name}] 🚀 Запуск continuous_improvement_loop...")
        print(f"[{thread_name}] 📊 Параметры: max_cycles=10, delay=3")
        
        # Запускаем цикл
        result = loop.run_until_complete(continuous_improvement_loop(max_cycles=10, delay_between_cycles=3))
        
        print(f"[{thread_name}] ✅ Цикл улучшения завершен")
        print(f"[{thread_name}] 📊 Результат: {result}")
        
    except Exception as e:
        print(f"[{thread_name}] ❌ Ошибка в цикле улучшения: {e}")
        import traceback
        traceback.print_exc()
        
        # Пытаемся добавить ошибку в веб-интерфейс
        try:
            from web_server import web_chat_viewer
            error_msg = f"❌ Ошибка в цикле улучшения: {str(e)[:200]}"
            web_chat_viewer.add_info(error_msg)
            print(f"[{thread_name}] ✅ Ошибка отправлена в веб-интерфейс")
        except Exception as web_error:
            print(f"[{thread_name}] ⚠️  Не удалось отправить ошибку в веб-интерфейс: {web_error}")
            import traceback
            traceback.print_exc()
    
    finally:
        print(f"[{thread_name}] 🏁 Поток цикла улучшения завершен")


def main():
    """Главная функция - запускает веб-сервер и цикл улучшения"""
    import os
    
    # Сохраняем PID процесса
    pid_file = "/tmp/agent_improvement.pid"
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    print("\n" + "="*70)
    print("🚀 ЗАПУСК СИСТЕМЫ АВТОМАТИЧЕСКОГО САМОСОВЕРШЕНСТВОВАНИЯ")
    print("="*70)
    print(f"📝 PID процесса: {os.getpid()}")
    print("\n📡 Запуск веб-сервера...")
    print("🔄 Запуск цикла улучшения в фоне...\n")
    
    # Запустить веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Дать веб-серверу время запуститься
    import time
    time.sleep(2)
    
    # Запустить цикл улучшения в отдельном потоке
    print("[Main] 🔄 Создание потока для цикла улучшения...")
    print(f"[Main] 📝 Текущий поток: {threading.current_thread().name}")
    
    improvement_thread = threading.Thread(target=run_improvement_in_thread, daemon=True, name="ImprovementThread")
    print(f"[Main] 📝 Поток создан: {improvement_thread.name}")
    
    improvement_thread.start()
    print(f"[Main] ✅ Поток цикла улучшения запущен: {improvement_thread.name} (alive: {improvement_thread.is_alive()})")
    
    # Дать потоку время запуститься
    time.sleep(2)
    print(f"[Main] 📊 Статус потока после паузы: alive={improvement_thread.is_alive()}, ident={improvement_thread.ident}")
    
    if not improvement_thread.is_alive():
        print("[Main] ⚠️  ПРОБЛЕМА: Поток цикла улучшения не запустился или уже завершился!")
        print("[Main] 🔍 Проверяю логи на наличие ошибок...")
    
    print("✅ Система запущена!")
    print("\n💡 Откройте в браузере: http://localhost:5001")
    print("💡 Система работает в фоне. Нажмите Ctrl+C для остановки.\n")
    
    # Добавить информационное сообщение в веб-интерфейс
    from web_server import web_chat_viewer
    try:
        web_chat_viewer.add_info("🚀 Система запущена! Начинаем тестирование...")
        print("[Main] ✅ Сообщение отправлено в веб-интерфейс")
    except Exception as e:
        print(f"[Main] ❌ Ошибка отправки сообщения в веб-интерфейс: {e}")
    
    # Мониторинг флага перезапуска
    restart_flag_path = "/tmp/agent_restart_flag"
    
    # Держать программу запущенной
    try:
        while True:
            # Проверяем флаг перезапуска
            if os.path.exists(restart_flag_path):
                print("\n🔄 Обнаружен флаг перезапуска! Перезапускаю агента...")
                web_chat_viewer.add_info("🔄 Обнаружены обновления кода, перезапускаю агента...")
                
                # Удаляем флаг
                try:
                    os.remove(restart_flag_path)
                except:
                    pass
                
                # Перезапускаем процесс
                script_path = os.path.abspath(__file__)
                print(f"[Restart] Запуск нового процесса: {script_path}")
                
                # Запускаем новый процесс
                import subprocess
                subprocess.Popen(
                    [sys.executable, script_path],
                    cwd=os.path.dirname(script_path)
                )
                
                # Даем время новому процессу запуститься
                time.sleep(3)
                
                # Завершаем текущий процесс
                print("[Restart] Завершение текущего процесса...")
                sys.exit(0)
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Остановка системы...")
        # Удаляем PID файл
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()

