"""Запуск системы с красивым интерфейсом чата"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_bot.bot import run_bot as run_main_bot
from test_client.tester import TestClient
from test_client.tester import DEFAULT_TEST_SCENARIOS
from monitor.error_tracker import error_tracker
from improvement_agent.analyzer import error_analyzer
from improvement_agent.updater import code_updater
from emulator.telegram_emulator import emulator
from ui.chat_viewer import chat_viewer


async def run_with_chat_interface():
    """Запуск системы с интерфейсом чата"""
    
    print("\n🚀 Запуск системы автоматического самосовершенствования...")
    print("   Режим: Локальный эмулятор с интерфейсом чата\n")
    
    # 1. Запустить основной бот
    print("[1/5] Запуск основного бота...")
    main_bot = await run_main_bot()
    
    # Подключить монитор к эмулятору
    async def monitor_handler(message):
        await error_tracker.handle_message(message)
    emulator.add_message_handler(monitor_handler)
    
    # Подключить чат-вьювер для отображения переписки
    async def chat_display_handler(message):
        chat_viewer.display_update(message)
    emulator.add_message_handler(chat_display_handler)
    
    # Инициализировать отображение чата
    chat_viewer.clear_screen()
    chat_viewer.print_header()
    chat_viewer.display_info("💬 Система запущена. Начинаем тестирование...")
    await asyncio.sleep(1)
    
    # 2. Запустить тесты с отображением в чате
    print("\n[2/5] Запуск тестирования...")
    
    # Проверить доступность GPT
    from test_client.gpt_client_generator import gpt_client_generator
    use_gpt = gpt_client_generator.is_available()
    
    if use_gpt:
        chat_viewer.display_info(f"🤖 GPT генератор подключен (модель: {gpt_client_generator.model})")
        chat_viewer.display_info("💬 Сообщения клиента будут генерироваться динамически через GPT")
    else:
        chat_viewer.display_info("ℹ️  GPT недоступен, используются статические сценарии")
        chat_viewer.display_info("💡 Для GPT генерации добавьте OPENAI_API_KEY в .env")
    
    await asyncio.sleep(1)
    
    test_client = TestClient(use_gpt=use_gpt)
    
    # Если GPT доступен, запускаем смешанный подход
    if use_gpt:
        # Несколько динамических GPT-сценариев
        for i in range(3):
            chat_viewer.display_info(f"📋 GPT сценарий {i+1}/3 (динамическая генерация)")
            await asyncio.sleep(0.5)
            await test_client.run_test_scenario()
            await asyncio.sleep(1)
            chat_viewer.display_info("⏸  Пауза...")
            await asyncio.sleep(0.5)
        
        # И несколько статических для сравнения
        for scenario_num, scenario in enumerate(DEFAULT_TEST_SCENARIOS[:2], 4):
            chat_viewer.display_info(f"📋 Статический сценарий {scenario_num}")
            await asyncio.sleep(0.5)
            await test_client.run_test_scenario(scenario)
            await asyncio.sleep(1)
    else:
        # Только статические сценарии
        for scenario_num, scenario in enumerate(DEFAULT_TEST_SCENARIOS, 1):
            chat_viewer.display_info(f"📋 Сценарий {scenario_num}/{len(DEFAULT_TEST_SCENARIOS)}: {len(scenario)} сообщений")
            await asyncio.sleep(0.5)
            await test_client.run_test_scenario(scenario)
            await asyncio.sleep(1)
            if scenario_num < len(DEFAULT_TEST_SCENARIOS):
                chat_viewer.display_info("⏸  Пауза перед следующим сценарием...")
                await asyncio.sleep(0.5)
    
    test_report = test_client.get_test_report()
    
    # 3. Показать итоги
    chat_viewer.display_info(f"✅ Тестирование завершено!")
    chat_viewer.display_summary(
        total_messages=len(emulator.get_messages("test_chat_1")),
        errors=test_report['total_errors']
    )
    
    await asyncio.sleep(2)
    
    # 4. Логировать диалоги
    print("\n[3/5] Логирование диалогов...")
    for conversation in test_client.conversations:
        await error_tracker.log_conversation(conversation)
    
    # 5. Анализ ошибок (если есть)
    if test_report['total_errors'] > 0:
        print(f"\n[4/5] Анализ {test_report['total_errors']} ошибок...")
        chat_viewer.display_info(f"🔍 Анализ {test_report['total_errors']} найденных ошибок...")
        analysis = await error_analyzer.analyze_errors()
        
        # 6. Применить исправления (если есть)
        fixes = analysis.get("code_fixes", [])
        if fixes:
            print(f"\n[5/5] Применение {len(fixes)} исправлений...")
            chat_viewer.display_info(f"🔧 Применение {len(fixes)} исправлений к коду бота...")
            update_result = await code_updater.apply_fixes(fixes)
            
            if update_result['fixes_applied'] > 0:
                chat_viewer.display_info("✨ Код бота обновлен! Перезапустите систему для применения изменений.")
        else:
            print("\n[5/5] Исправления не были сгенерированы")
    else:
        print("\n✅ Ошибок не найдено! Бот работает отлично!")
        chat_viewer.display_info("🎉 Ошибок не найдено! Бот работает отлично!")
    
    # Финальная статистика
    await asyncio.sleep(2)
    print("\n" + "="*70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("="*70)
    print(f"   📝 Всего диалогов: {test_report['total_conversations']}")
    print(f"   💬 Всего сообщений: {test_report['total_tests']}")
    print(f"   ❌ Ошибок найдено: {test_report['total_errors']}")
    print(f"   📈 Процент ошибок: {test_report['error_rate']*100:.2f}%")
    print("="*70)
    
    print("\n💡 Нажмите Enter для завершения...")
    input()


if __name__ == "__main__":
    try:
        asyncio.run(run_with_chat_interface())
    except KeyboardInterrupt:
        print("\n\n⏹️  Остановка по запросу пользователя")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

