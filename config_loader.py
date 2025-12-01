"""Безопасный загрузчик настроек - обходит конфликт с Instagram bot config"""
import sys
import importlib.util
from pathlib import Path

_our_settings_cache = None

def get_our_settings():
    """Получить настройки нашего проекта (безопасно, обходя конфликт config)"""
    global _our_settings_cache
    
    if _our_settings_cache is not None:
        return _our_settings_cache
    
    # Импортируем настройки напрямую из файла
    config_settings_path = Path(__file__).parent / 'config' / 'settings.py'
    spec = importlib.util.spec_from_file_location("our_settings_module", config_settings_path)
    
    if spec and spec.loader:
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)
        _our_settings_cache = settings_module
        return settings_module
    else:
        raise ImportError(f"Не удалось загрузить настройки из {config_settings_path}")

