#!/usr/bin/env python3
"""Скрипт для перезапуска агента после обновления кода"""
import os
import sys
import signal
import subprocess
import time
from pathlib import Path

AGENT_PID_FILE = "/tmp/agent_improvement.pid"
RESTART_FLAG_FILE = "/tmp/agent_restart_flag"

def get_agent_pid():
    """Получить PID процесса агента"""
    if os.path.exists(AGENT_PID_FILE):
        try:
            with open(AGENT_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                # Проверяем, что процесс еще существует
                try:
                    os.kill(pid, 0)  # Проверка существования процесса
                    return pid
                except OSError:
                    return None
        except (ValueError, FileNotFoundError):
            return None
    return None

def restart_agent():
    """Перезапустить агента"""
    print("[RestartAgent] 🔄 Перезапуск агента...")
    
    # Получаем PID текущего процесса
    pid = get_agent_pid()
    
    if pid:
        print(f"[RestartAgent] Остановка процесса {pid}...")
        try:
            # Отправляем SIGTERM для корректного завершения
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Если процесс еще жив, отправляем SIGKILL
            try:
                os.kill(pid, 0)
                print(f"[RestartAgent] Процесс не завершился, отправляю SIGKILL...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            except OSError:
                pass  # Процесс уже завершен
        except OSError as e:
            print(f"[RestartAgent] ⚠️  Ошибка при остановке процесса: {e}")
    
    # Запускаем новый процесс
    script_dir = Path(__file__).parent
    run_script = script_dir / "run_with_web.py"
    
    print(f"[RestartAgent] Запуск нового процесса...")
    process = subprocess.Popen(
        [sys.executable, str(run_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(script_dir)
    )
    
    # Сохраняем PID
    with open(AGENT_PID_FILE, 'w') as f:
        f.write(str(process.pid))
    
    print(f"[RestartAgent] ✅ Агент перезапущен (PID: {process.pid})")
    return process.pid

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restart":
        restart_agent()
    else:
        print("Использование: python3 restart_agent.py restart")



