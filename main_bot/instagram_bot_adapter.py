"""Адаптер для интеграции структуры Instagram бота"""
import sys
import os
from pathlib import Path

# Путь к проекту Instagram бота
INSTAGRAM_BOT_PATH = "/Users/pavelgulo/Desktop/бот madebymoloday/bot_code"

# КРИТИЧЕСКИ ВАЖНО: Сохранить наш config перед импортом Instagram бота
# Потом восстановим его после импорта Instagram модулей
our_config_backup = None
our_config_modules_backup = {}
if 'config' in sys.modules:
    our_config = sys.modules['config']
    our_config_path = our_config.__file__ if hasattr(our_config, '__file__') else None
    # Проверяем, это наш config (из нашего проекта)
    if our_config_path and 'курсор' in our_config_path:
        print(f"[InstagramBotAdapter] 🔄 Сохраняю наш config перед импортом Instagram бота")
        our_config_backup = our_config
        # Сохранить все подмодули config
        for key in list(sys.modules.keys()):
            if key.startswith('config.'):
                our_config_modules_backup[key] = sys.modules[key]
        
        # Временно удалить для импорта Instagram config
        del sys.modules['config']
        for key in our_config_modules_backup.keys():
            if key in sys.modules:
                del sys.modules[key]

# Добавляем путь к Instagram боту в sys.path
if os.path.exists(INSTAGRAM_BOT_PATH):
    # ВАЖНО: добавляем ПЕРЕД текущим путём, чтобы Instagram бот мог импортировать свой config
    sys.path.insert(0, INSTAGRAM_BOT_PATH)
    
    try:
        print(f"[InstagramBotAdapter] 📁 Загружаю модули из: {INSTAGRAM_BOT_PATH}")
        
        # Проверяем наличие файлов
        required_files = [
            "file_data_loader.py",
            "workflow.py",
            "quick_responses.py",
            "config.py"
        ]
        for file in required_files:
            file_path = os.path.join(INSTAGRAM_BOT_PATH, file)
            if not os.path.exists(file_path):
                print(f"[InstagramBotAdapter] ⚠️  Файл не найден: {file_path}")
        
        # Импортируем модули Instagram бота (его config теперь будет найден первым)
        from file_data_loader import FileDataLoader
        from workflow import WorkflowManager
        from quick_responses import QuickResponses
        from config import OPENAI_CONFIG
        
        print(f"[InstagramBotAdapter] ✅ Модули Instagram бота загружены успешно")
        print(f"[InstagramBotAdapter]   - FileDataLoader: {FileDataLoader}")
        print(f"[InstagramBotAdapter]   - WorkflowManager: {WorkflowManager}")
        print(f"[InstagramBotAdapter]   - QuickResponses: {QuickResponses}")
        
        # ВАЖНО: Instagram config теперь в sys.modules как 'config'
        # Мы оставляем его там, так как он нужен для работы Instagram модулей
        # Наш config доступен через config_loader.py
        
        # Сохраняем Instagram config под отдельным именем для удобства (опционально)
        instagram_config = sys.modules.get('config')
        if instagram_config:
            sys.modules['instagram_bot_config'] = instagram_config
        
        print(f"[InstagramBotAdapter] ✅ Instagram config сохранен в sys.modules как 'config'")
        print(f"[InstagramBotAdapter] ℹ️  Наш config доступен через config_loader.get_our_settings()")
        
        # Флаг доступности
        INSTAGRAM_BOT_AVAILABLE = True
    except ImportError as e:
        print(f"[InstagramBotAdapter] ❌ Ошибка импорта модулей Instagram бота: {e}")
        import traceback
        traceback.print_exc()
        INSTAGRAM_BOT_AVAILABLE = False
        FileDataLoader = None
        WorkflowManager = None
        QuickResponses = None
        OPENAI_CONFIG = None
    except Exception as e:
        print(f"[InstagramBotAdapter] ❌ Неожиданная ошибка при загрузке модулей: {e}")
        import traceback
        traceback.print_exc()
        INSTAGRAM_BOT_AVAILABLE = False
        FileDataLoader = None
        WorkflowManager = None
        QuickResponses = None
        OPENAI_CONFIG = None
else:
    print(f"[InstagramBotAdapter] ⚠️  Путь к Instagram боту не найден: {INSTAGRAM_BOT_PATH}")
    INSTAGRAM_BOT_AVAILABLE = False
    FileDataLoader = None
    WorkflowManager = None
    QuickResponses = None
    OPENAI_CONFIG = None


def get_instagram_bot_structure():
    """Получить структуру Instagram бота"""
    if not INSTAGRAM_BOT_AVAILABLE:
        print("[InstagramBotAdapter] ❌ Instagram бот недоступен, возвращаю None")
        return None, None, None
    
    try:
        print("[InstagramBotAdapter] 🔧 Инициализация структуры Instagram бота...")
        
        # Инициализируем загрузчик данных
        print("[InstagramBotAdapter] 📂 Инициализация FileDataLoader...")
        data_loader = FileDataLoader()
        print(f"[InstagramBotAdapter] ✅ FileDataLoader инициализирован")
        print(f"[InstagramBotAdapter]   - Загружено этапов: {len(data_loader.workflow_stages) if hasattr(data_loader, 'workflow_stages') else 0}")
        print(f"[InstagramBotAdapter]   - Загружено БАДов: {len(data_loader.products_list) if hasattr(data_loader, 'products_list') else 0}")
        
        # Инициализируем WorkflowManager
        print("[InstagramBotAdapter] 🔄 Инициализация WorkflowManager...")
        workflow = WorkflowManager(data_loader)
        print(f"[InstagramBotAdapter] ✅ WorkflowManager инициализирован")
        print(f"[InstagramBotAdapter]   - OpenAI клиент: {'✅' if workflow.openai_client else '❌'}")
        
        # Инициализируем QuickResponses
        print("[InstagramBotAdapter] ⚡ Инициализация QuickResponses...")
        quick_responses = None
        try:
            # Пробуем сначала с data_loader
            quick_responses = QuickResponses(data_loader)
            print(f"[InstagramBotAdapter] ✅ QuickResponses инициализирован с data_loader")
        except (TypeError, AttributeError) as e:
            print(f"[InstagramBotAdapter] ⚠️  Не удалось инициализировать QuickResponses с data_loader: {e}")
            try:
                # Пробуем без параметров
                quick_responses = QuickResponses()
                print(f"[InstagramBotAdapter] ✅ QuickResponses инициализирован без параметров")
            except Exception as e2:
                # Если не получается, оставляем None
                quick_responses = None
                print(f"[InstagramBotAdapter] ⚠️  QuickResponses не инициализирован: {e2}")
                print("[InstagramBotAdapter] ⚠️  Это не критично, бот будет работать без быстрых ответов")
        
        print("[InstagramBotAdapter] ✅ Структура Instagram бота успешно инициализирована!")
        print(f"[InstagramBotAdapter]   - data_loader: {data_loader is not None}")
        print(f"[InstagramBotAdapter]   - workflow: {workflow is not None}")
        print(f"[InstagramBotAdapter]   - quick_responses: {quick_responses is not None}")
        
        return data_loader, workflow, quick_responses
    except Exception as e:
        print(f"[InstagramBotAdapter] ❌ Ошибка инициализации структуры Instagram бота: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

