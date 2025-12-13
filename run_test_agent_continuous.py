#!/usr/bin/env python3
"""Скрипт для непрерывного запуска тест-агента AI-психолога"""
import asyncio
import sys
import os
import time
import signal

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_agent import run_psychologist_tests

# Флаг для корректного завершения
running = True

def signal_handler(sig, frame):
    """Обработчик сигнала для корректного завершения"""
    global running
    print("\n\n⚠️ Получен сигнал завершения. Завершаю работу...")
    running = False

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def run_continuous():
    """Запустить непрерывное тестирование"""
    iteration = 0
    
    print("=" * 60)
    print("🤖 Запуск тест-агента для AI-психолога (непрерывный режим)")
    print("=" * 60)
    print("\nАгент будет:")
    print("  1. Открывать браузер")
    print("  2. Входить в систему (или регистрироваться)")
    print("  3. Вести диалог с AI-психологом")
    print("  4. Отправлять логи в чат")
    print("  5. Находить ошибки в работе системы")
    print("  6. Повторять тесты каждые 5 минут")
    print("\nНажмите Ctrl+C для остановки")
    print("=" * 60 + "\n")
    
    while running:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"🔄 Итерация #{iteration} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        try:
            agent = await run_psychologist_tests(continuous_mode=True)
            
            if agent:
                print(f"\n✅ Итерация #{iteration} завершена успешно")
            else:
                print(f"\n❌ Итерация #{iteration} завершилась с ошибками")
            
            # Пауза между итерациями (5 минут)
            if running:
                print(f"\n⏳ Ожидание 5 минут до следующей итерации...")
                print("   (Нажмите Ctrl+C для остановки)\n")
                
                # Ждем 5 минут, но проверяем флаг каждую секунду
                for _ in range(300):  # 300 секунд = 5 минут
                    if not running:
                        break
                    time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Прервано пользователем")
            break
        except Exception as e:
            print(f"\n❌ Критическая ошибка в итерации #{iteration}: {e}")
            import traceback
            traceback.print_exc()
            
            # Небольшая пауза перед следующей попыткой
            if running:
                print("\n⏳ Ожидание 30 секунд перед следующей попыткой...")
                for _ in range(30):
                    if not running:
                        break
                    time.sleep(1)
    
    print("\n\n✅ Агент остановлен. До свидания!")


if __name__ == "__main__":
    try:
        asyncio.run(run_continuous())
    except KeyboardInterrupt:
        print("\n\n⚠️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

