"""Автоматическое обновление кода в Git после применения исправлений"""
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional
import json


class GitAutoUpdater:
    """Автоматически коммитит и пушит изменения в Git после применения исправлений"""
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()
        self.git_enabled = self._check_git_repo()
    
    def _check_git_repo(self) -> bool:
        """Проверить, является ли директория git репозиторием"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_git_command(self, command: list, description: str) -> Dict[str, any]:
        """Выполнить git команду"""
        if not self.git_enabled:
            return {
                "success": False,
                "error": "Git репозиторий не найден"
            }
        
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip(),
                    "description": description
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip(),
                    "description": description
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Таймаут выполнения команды",
                "description": description
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": description
            }
    
    def get_status(self) -> Dict[str, any]:
        """Получить статус git репозитория"""
        status_result = self._run_git_command(
            ['git', 'status', '--porcelain'],
            "Проверка статуса"
        )
        
        return status_result
    
    def has_changes(self) -> bool:
        """Проверить, есть ли изменения для коммита"""
        status_result = self.get_status()
        if not status_result["success"]:
            return False
        
        return len(status_result["output"]) > 0
    
    def auto_commit_and_push(self, fixes_applied: int, error_summary: str = "") -> Dict[str, any]:
        """
        Автоматически закоммитить и запушить изменения
        
        Args:
            fixes_applied: Количество примененных исправлений
            error_summary: Краткое описание исправленных ошибок
        """
        if not self.git_enabled:
            return {
                "success": False,
                "error": "Git репозиторий не найден"
            }
        
        # Проверить, есть ли изменения
        if not self.has_changes():
            return {
                "success": False,
                "error": "Нет изменений для коммита"
            }
        
        results = {
            "steps": [],
            "success": True
        }
        
        # 1. Добавить все изменения
        add_result = self._run_git_command(
            ['git', 'add', '-A'],
            "Добавление изменений в индекс"
        )
        results["steps"].append(add_result)
        
        if not add_result["success"]:
            results["success"] = False
            return results
        
        # 2. Создать коммит
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"🤖 Авто-исправление: применено {fixes_applied} исправлений ({timestamp})"
        
        if error_summary:
            commit_message += f"\n\nИсправлено: {error_summary[:200]}"
        
        commit_result = self._run_git_command(
            ['git', 'commit', '-m', commit_message],
            f"Создание коммита: {commit_message[:50]}..."
        )
        results["steps"].append(commit_result)
        
        if not commit_result["success"]:
            results["success"] = False
            return results
        
        # 3. Получить информацию о текущей ветке
        branch_result = self._run_git_command(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            "Получение имени текущей ветки"
        )
        
        branch_name = "main"
        if branch_result["success"]:
            branch_name = branch_result["output"] or "main"
        
        # 4. Push в remote (если настроен)
        remote_result = self._run_git_command(
            ['git', 'remote', 'get-url', 'origin'],
            "Проверка наличия remote"
        )
        
        has_remote = remote_result["success"]
        
        if has_remote:
            push_result = self._run_git_command(
                ['git', 'push', 'origin', branch_name],
                f"Отправка изменений в {branch_name}"
            )
            results["steps"].append(push_result)
            
            if push_result["success"]:
                results["pushed"] = True
                results["branch"] = branch_name
            else:
                results["pushed"] = False
                results["push_error"] = push_result.get("error", "Unknown error")
        else:
            results["pushed"] = False
            results["push_warning"] = "Remote 'origin' не настроен. Изменения закоммичены локально."
        
        return results
    
    def get_repo_info(self) -> Dict[str, any]:
        """Получить информацию о репозитории"""
        info = {
            "repo_path": self.repo_path,
            "git_enabled": self.git_enabled
        }
        
        if not self.git_enabled:
            return info
        
        # Получить текущую ветку
        branch_result = self._run_git_command(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            "Получение ветки"
        )
        if branch_result["success"]:
            info["branch"] = branch_result["output"]
        
        # Получить remote URL
        remote_result = self._run_git_command(
            ['git', 'remote', 'get-url', 'origin'],
            "Получение remote"
        )
        if remote_result["success"]:
            info["remote"] = remote_result["output"]
        
        # Получить последний коммит
        commit_result = self._run_git_command(
            ['git', 'log', '-1', '--pretty=format:%H|%s'],
            "Последний коммит"
        )
        if commit_result["success"]:
            parts = commit_result["output"].split('|', 1)
            if len(parts) == 2:
                info["last_commit_hash"] = parts[0]
                info["last_commit_message"] = parts[1]
        
        return info



