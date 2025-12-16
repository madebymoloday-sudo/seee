"""Главный файл - запускает цикл автоматического самосовершенствования"""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_bot.bot import run_bot as run_main_bot
from test_client.tester import run_tests, TestClient
from monitor.error_tracker import error_tracker
from improvement_agent.analyzer import error_analyzer
from improvement_agent.updater import code_updater
from emulator.telegram_emulator import emulator
from ui.chat_viewer import chat_viewer

# Глобальная переменная для основного бота
main_bot_instance = None


async def improvement_cycle():
    """Один цикл улучшения"""
    global main_bot_instance
    
    print("\n" + "="*60)
    print("🔄 ЗАПУСК ЦИКЛА УЛУЧШЕНИЯ")
    print("="*60)
    
    # 1. Запустить основной бот
    print("\n[1/5] Запуск основного бота...")
    main_bot_instance = await run_main_bot()
    
    # Подключить монитор к эмулятору
    async def monitor_handler(message):
        """Обработчик сообщений для мониторинга"""
        await error_tracker.handle_message(message)
    emulator.add_message_handler(monitor_handler)
    
    # Подключить чат-вьювер для отображения переписки
    async def chat_display_handler(message):
        """Обработчик для отображения сообщений в чате"""
        chat_viewer.display_update(message)
    emulator.add_message_handler(chat_display_handler)
    
    # Инициализировать отображение чата
    chat_viewer.clear_screen()
    chat_viewer.print_header()
    chat_viewer.display_info("Система запущена. Начинаем тестирование...")
    await asyncio.sleep(0.5)
    
    # 2. Запустить тесты
    print("\n[2/5] Запуск тестирования...")
    test_client = await run_tests()
    test_report = test_client.get_test_report()
    
    # 3. Логировать все диалоги
    print("\n[3/5] Логирование диалогов...")
    for conversation in test_client.conversations:
        await error_tracker.log_conversation(conversation)
    
    # Показать итоги тестирования в чате
    chat_viewer.display_info(f"Тестирование завершено. Найдено ошибок: {test_report['total_errors']}")
    await asyncio.sleep(1)
    
    # 4. Анализ ошибок
    print("\n[4/5] Анализ ошибок и генерация исправлений...")
    chat_viewer.display_info("Анализ ошибок и генерация исправлений...")
    analysis = await error_analyzer.analyze_errors()
    
    if analysis.get("status") == "no_errors":
        print("✅ Ошибок не найдено! Бот работает идеально.")
        return {
            "status": "no_errors",
            "message": "Ошибок не найдено"
        }
    
    # 5. Применить исправления
    print("\n[5/5] Применение исправлений...")
    fixes = analysis.get("code_fixes", [])
    if fixes:
        update_result = await code_updater.apply_fixes(fixes)
        print(f"\n✅ Применено исправлений: {update_result['fixes_applied']}")
        
        if update_result['fixes_applied'] > 0:
            print("\n⚠️  ВНИМАНИЕ: Код бота был обновлен!")
            print("   Перезапустите бота для применения изменений.")
            return {
                "status": "improved",
                "fixes_applied": update_result['fixes_applied'],
                "next_step": "restart_required"
            }
    else:
        print("❌ Исправления не были сгенерированы")
    
    return analysis


async def continuous_improvement(max_cycles: int = 5, delay_between_cycles: int = 5):
    """Непрерывный цикл улучшения"""
    print("\n🚀 ЗАПУСК СИСТЕМЫ АВТОМАТИЧЕСКОГО САМОСОВЕРШЕНСТВОВАНИЯ")
    print(f"   Максимум циклов: {max_cycles}")
    print(f"   Задержка между циклами: {delay_between_cycles} сек\n")
    
    for cycle in range(1, max_cycles + 1):
        print(f"\n{'='*60}")
        print(f"ЦИКЛ #{cycle}/{max_cycles} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            result = await improvement_cycle()
            
            if result.get("status") == "no_errors":
                print(f"\n🎉 Цикл {cycle}: Ошибок не найдено! Бот совершенен!")
                break
            
            if result.get("status") == "improved":
                print(f"\n✨ Цикл {cycle}: Бот улучшен! Применено {result.get('fixes_applied', 0)} исправлений")
            
            # Очистить чат для следующего цикла
            emulator.clear_chat("test_chat_1")
            if main_bot_instance:
                main_bot_instance.clear_errors()
            
            if cycle < max_cycles:
                print(f"\n⏳ Ожидание {delay_between_cycles} секунд до следующего цикла...")
                await asyncio.sleep(delay_between_cycles)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Остановка по запросу пользователя")
            break
        except Exception as e:
            print(f"\n❌ Ошибка в цикле {cycle}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("🏁 СИСТЕМА ОСТАНОВЛЕНА")
    print("="*60)
    
    # Финальная статистика
    error_summary = error_tracker.get_error_summary()
    print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
    print(f"   Всего ошибок зафиксировано: {error_summary['total_errors']}")
    print(f"   Типы ошибок: {error_summary['error_types']}")


async def single_test():
    """Однократное тестирование без улучшения"""
    print("\n🧪 ЗАПУСК ОДНОКРАТНОГО ТЕСТИРОВАНИЯ")
    
    main_bot = await run_main_bot()
    await asyncio.sleep(1)
    
    test_client = await run_tests()
    test_report = test_client.get_test_report()
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   Диалогов: {test_report['total_conversations']}")
    print(f"   Тестов: {test_report['total_tests']}")
    print(f"   Ошибок: {test_report['total_errors']}")
    print(f"   Процент ошибок: {test_report['error_rate']*100:.2f}%")
    
    if test_report['errors']:
        print("\n❌ НАЙДЕННЫЕ ОШИБКИ:")
        for error in test_report['errors'][:5]:
            print(f"   - {error.get('errors', 'Unknown')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Система автоматического самосовершенствования бота")
    parser.add_argument(
        "--mode",
        choices=["single", "continuous"],
        default="single",
        help="Режим работы: single (одно тестирование) или continuous (непрерывное улучшение)"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=5,
        help="Количество циклов для continuous режима"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Задержка между циклами в секундах"
    )
    
    args = parser.parse_args()
    
    if args.mode == "continuous":
        asyncio.run(continuous_improvement(max_cycles=args.cycles, delay_between_cycles=args.delay))
    else:
        asyncio.run(single_test())

