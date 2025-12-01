"""Агент для обновления кода бота на основе анализа ошибок"""
import os
import shutil
import re
from datetime import datetime
from typing import Dict, List
from config_loader import get_our_settings
our_settings = get_our_settings()
MAIN_BOT_DIR = our_settings.MAIN_BOT_DIR
BACKUP_DIR = our_settings.BACKUP_DIR


class CodeUpdater:
    """Обновляет код бота на основе предложенных исправлений"""
    
    def __init__(self):
        self._ensure_backup_dir()
        
    def _ensure_backup_dir(self):
        """Создать директорию для бэкапов"""
        os.makedirs(BACKUP_DIR, exist_ok=True)
    
    async def apply_fixes(self, fixes: List[Dict]) -> Dict:
        """Применить исправления к коду"""
        # Отправить уведомление о начале применения исправлений
        try:
            from web_server import web_chat_viewer
            web_chat_viewer.add_agent_notification(
                title="💻 Применение кода",
                message=f"Применяю {len(fixes)} исправлений к файлам кода...",
                notification_type="applying",
                details=f"Файлов для обновления: {len(set(f['file'] for f in fixes))}"
            )
        except:
            pass  # web_chat_viewer может быть недоступен
        if not fixes:
            return {
                "status": "no_fixes",
                "message": "Нет исправлений для применения"
            }
        
        results = []
        
        for fix in fixes:
            result = await self._apply_single_fix(fix)
            results.append(result)
        
        return {
            "status": "completed",
            "fixes_applied": len([r for r in results if r["success"]]),
            "fixes_failed": len([r for r in results if not r["success"]]),
            "details": results
        }
    
    async def _apply_single_fix(self, fix: Dict) -> Dict:
        """Применить одно исправление"""
        try:
            file_path = fix["file"]
            function_name = fix.get("function", "")
            improved_code = fix.get("improved_code", "")
            
            # Создать бэкап
            backup_path = await self._create_backup(file_path)
            
            # Применить исправление
            if function_name:
                success = await self._replace_function(file_path, function_name, improved_code)
            else:
                success = await self._replace_file(file_path, improved_code)
            
            if success:
                return {
                    "success": True,
                    "file": file_path,
                    "function": function_name,
                    "backup": backup_path,
                    "message": "Исправление применено успешно"
                }
            else:
                return {
                    "success": False,
                    "file": file_path,
                    "message": "Не удалось применить исправление"
                }
                
        except Exception as e:
            return {
                "success": False,
                "file": fix.get("file", "unknown"),
                "message": f"Ошибка: {str(e)}"
            }
    
    async def _create_backup(self, file_path: str) -> str:
        """Создать резервную копию файла"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.basename(file_path)}_{timestamp}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    async def _replace_function(self, file_path: str, function_name: str, new_code: str) -> bool:
        """Заменить функцию в файле (для Python с отступами)"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Найти начало функции
            start_line = -1
            for i, line in enumerate(lines):
                # Ищем async def function_name или def function_name
                if re.match(rf'^\s*(async\s+)?def\s+{function_name}\s*\(', line):
                    start_line = i
                    break
            
            if start_line == -1:
                print(f"[Updater] Функция {function_name} не найдена в {file_path}")
                return False
            
            # Определить отступ функции
            function_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            
            # Найти конец функции (следующая строка с таким же или меньшим отступом)
            end_line = start_line + 1
            while end_line < len(lines):
                line = lines[end_line]
                # Пропустить пустые строки
                if not line.strip():
                    end_line += 1
                    continue
                # Пропустить комментарии
                if line.strip().startswith('#'):
                    end_line += 1
                    continue
                # Проверить отступ текущей строки
                current_indent = len(line) - len(line.lstrip())
                # Если отступ меньше или равен отступу функции - это конец функции
                if current_indent <= function_indent:
                    break
                end_line += 1
            
            # Извлечь части файла
            before = ''.join(lines[:start_line])
            after = ''.join(lines[end_line:])
            
            # Подготовить новый код с правильным отступом
            new_code_cleaned = new_code.strip()
            new_code_lines = new_code_cleaned.split('\n')
            
            # Применить отступ функции к первой строке
            # Остальные строки должны сохранить свои относительные отступы
            if new_code_lines:
                # Определить базовый отступ в новом коде (из первой строки с кодом)
                base_code_indent = 0
                for line in new_code_lines:
                    if line.strip() and not line.strip().startswith('def') and not line.strip().startswith('async'):
                        base_code_indent = len(line) - len(line.lstrip())
                        break
                
                # Нормализовать отступы: убрать базовый отступ, добавить отступ функции
                normalized_lines = []
                for line in new_code_lines:
                    if line.strip():
                        # Убрать базовый отступ из нового кода
                        stripped = line.lstrip()
                        original_indent = len(line) - len(stripped)
                        relative_indent = original_indent - base_code_indent
                        # Добавить отступ функции
                        normalized_lines.append(' ' * (function_indent + relative_indent) + stripped)
                    else:
                        normalized_lines.append('')
                
                indented_code = '\n'.join(normalized_lines)
                
                # Собрать новый файл
                new_content = before + indented_code + '\n' + after
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                print(f"[Updater] Функция {function_name} обновлена в {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[Updater] Ошибка при замене функции: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _replace_file(self, file_path: str, new_code: str) -> bool:
        """Заменить весь файл"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            return True
        except Exception as e:
            print(f"[Updater] Ошибка при замене файла: {e}")
            return False
    
    def rollback(self, backup_path: str, original_path: str) -> bool:
        """Откатить изменения из бэкапа"""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, original_path)
                return True
            return False
        except Exception as e:
            print(f"[Updater] Ошибка при откате: {e}")
            return False


# Глобальный экземпляр обновлятора
code_updater = CodeUpdater()

