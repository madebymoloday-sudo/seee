"""Система мониторинга и отслеживания ошибок"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from config_loader import get_our_settings
our_settings = get_our_settings()
LOGS_DIR = our_settings.LOGS_DIR
LOG_FILE = our_settings.LOG_FILE


@dataclass
class ErrorRecord:
    """Запись об ошибке"""
    error_type: str
    error_message: str
    context: Dict
    timestamp: str
    conversation_id: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class ErrorTracker:
    """Отслеживание и логирование ошибок"""
    
    def __init__(self):
        self.errors: List[ErrorRecord] = []
        self._ensure_log_dir()
        
    def _ensure_log_dir(self):
        """Создать директорию для логов если её нет"""
        os.makedirs(LOGS_DIR, exist_ok=True)
    
    async def handle_message(self, message):
        """Обработчик сообщений от эмулятора для логирования"""
        # Можно добавить дополнительную логику логирования всех сообщений
        pass
        
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict,
        conversation_id: Optional[str] = None
    ):
        """Записать ошибку"""
        error_record = ErrorRecord(
            error_type=error_type,
            error_message=error_message,
            context=context,
            timestamp=datetime.now().isoformat(),
            conversation_id=conversation_id
        )
        
        self.errors.append(error_record)
        
        # Сохранить в файл
        await self._save_to_file(error_record)
        
        print(f"[ErrorTracker] Ошибка зафиксирована: {error_type} - {error_message}")
    
    async def _save_to_file(self, error_record: ErrorRecord):
        """Сохранить ошибку в файл"""
        log_path = os.path.join(LOGS_DIR, "errors.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_record.to_dict(), ensure_ascii=False) + "\n")
    
    async def log_conversation(self, conversation: Dict):
        """Логировать полный диалог"""
        log_path = os.path.join(LOGS_DIR, "conversations.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(conversation, ensure_ascii=False) + "\n")
        
        # Проверить диалог на ошибки
        if "errors" in conversation and conversation["errors"]:
            for error in conversation["errors"]:
                await self.log_error(
                    error_type="conversation_error",
                    error_message=str(error.get("errors", "Unknown error")),
                    context={
                        "test_message": error.get("test_message"),
                        "response": error.get("response")
                    },
                    conversation_id=str(conversation.get("timestamp"))
                )
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorRecord]:
        """Получить последние ошибки"""
        return self.errors[-limit:]
    
    def get_error_summary(self) -> Dict:
        """Получить сводку по ошибкам"""
        if not self.errors:
            return {
                "total_errors": 0,
                "error_types": {},
                "recent_errors": []
            }
        
        error_types = {}
        for error in self.errors:
            error_type = error.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "recent_errors": [err.to_dict() for err in self.get_recent_errors(5)]
        }


# Глобальный экземпляр трекера
error_tracker = ErrorTracker()

