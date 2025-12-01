"""Настройки для системы автоматического самосовершенствования бота"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Tokens
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "")
TEST_BOT_TOKEN = os.getenv("TEST_BOT_TOKEN", "")

# AI Agent Settings
AI_API_KEY = os.getenv("AI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
AI_MODEL = os.getenv("AI_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# Mode Settings
USE_REAL_TELEGRAM = os.getenv("USE_REAL_TELEGRAM", "false").lower() == "true"
EMULATOR_MODE = os.getenv("EMULATOR_MODE", "true").lower() == "true"

# Test Group ID (если используем реальный Telegram)
TEST_GROUP_ID = os.getenv("TEST_GROUP_ID", "")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/conversations.log")

# Directories
MAIN_BOT_DIR = "main_bot"
BACKUP_DIR = "backup"
LOGS_DIR = "logs"

