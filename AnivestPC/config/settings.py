"""
🔧 ANIVEST DESKTOP - НАСТРОЙКИ ПРИЛОЖЕНИЯ
===========================================
Конфигурация API ключей, БД и других параметров
"""

import os
from pathlib import Path

# ===== ОСНОВНЫЕ НАСТРОЙКИ =====

# Информация о приложении
APP_NAME = "Anivest Desktop"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Десктопное приложение для просмотра аниме"

# Размеры окна
WINDOW_CONFIG = {
    "min_width": 1200,
    "min_height": 800,
    "default_width": 1400,
    "default_height": 900,
    "max_width": 1920,
    "max_height": 1080,
    "resizable": True
}

# ===== ПУТИ К ФАЙЛАМ =====

# Базовая директория проекта
BASE_DIR = Path(__file__).parent.parent

# Директория данных
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# База данных
DATABASE_PATH = DATA_DIR / "anivest.db"

# Кеш
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Постеры
POSTERS_CACHE_DIR = CACHE_DIR / "posters"
POSTERS_CACHE_DIR.mkdir(exist_ok=True)

# Логи
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ===== API НАСТРОЙКИ =====

# Shikimori API
SHIKIMORI_CONFIG = {
    "base_url": "https://shikimori.one/api",
    "user_agent": "Anivest Desktop/1.0 (https://anivest.local)",
    "timeout": 10,
    "cache_timeout": 600,  # 10 минут
    "rate_limit": 5  # RPS (requests per second)
}

# Kodik API
KODIK_CONFIG = {
    "base_url": "https://kodikapi.com",
    "timeout": 15,
    "cache_timeout": 300,  # 5 минут
    "test_tokens": [
        "447d179e875efe44217f20d1ee2146be",
        "73f8b92d87eb24e1a95e64e9d33d0a34", 
        "2f84e5c78ba6a64f7e3d91c45b0c12aa"
    ]
}

# ===== КЕШИРОВАНИЕ =====

CACHE_CONFIG = {
    "enabled": True,
    "max_size": 1000,  # Максимум записей в памяти
    "poster_cache_days": 7,  # Сколько дней хранить постеры
    "metadata_cache_hours": 24,  # Сколько часов хранить метаданные
    "cleanup_interval": 3600  # Очистка кеша каждый час (секунды)
}

# ===== БАЗА ДАННЫХ =====

DATABASE_CONFIG = {
    "path": str(DATABASE_PATH),
    "timeout": 30,
    "check_same_thread": False,
    "backup_enabled": True,
    "backup_interval": 86400  # Бекап каждые 24 часа
}

# ===== ЛОГИРОВАНИЕ =====

LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "file_path": LOGS_DIR / "anivest.log",
    "max_file_size": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# ===== ПОЛЬЗОВАТЕЛЬСКИЕ НАСТРОЙКИ =====

USER_SETTINGS = {
    "theme": "dark",  # dark, light
    "language": "ru",  # ru, en
    "auto_play": False,
    "notifications": True,
    "remember_position": True,
    "auto_mark_watched": True,
    "quality_preference": "720p",  # 480p, 720p, 1080p
    "player_volume": 0.8,
    "sidebar_width": 180
}

# ===== ГОРЯЧИЕ КЛАВИШИ =====

HOTKEYS = {
    "play_pause": "space",
    "next_episode": "ctrl+right", 
    "prev_episode": "ctrl+left",
    "volume_up": "up",
    "volume_down": "down",
    "fullscreen": "f",
    "search": "ctrl+f",
    "favorites": "ctrl+d",
    "home": "ctrl+h",
    "catalog": "ctrl+l"
}

# ===== ЛИМИТЫ И ОГРАНИЧЕНИЯ =====

LIMITS = {
    "search_results": 50,
    "popular_anime": 24,
    "seasonal_anime": 12,
    "comments_per_page": 20,
    "max_comment_length": 1000,
    "max_favorites": 1000,
    "max_watch_history": 5000
}

# ===== ФИЛЬТРЫ И ЖАНРЫ =====

ANIME_GENRES = [
    "Экшен", "Приключения", "Комедия", "Драма", "Фэнтези", 
    "Романтика", "Фантастика", "Сверхъестественное", "Психологическое",
    "Триллер", "Повседневность", "Школа", "Спорт", "Военное", "Исторический"
]

ANIME_TYPES = [
    {"value": "tv", "label": "TV Сериал"},
    {"value": "movie", "label": "Фильм"},
    {"value": "ova", "label": "OVA"},
    {"value": "ona", "label": "ONA"},
    {"value": "special", "label": "Спешл"}
]

ANIME_STATUSES = [
    {"value": "released", "label": "Вышел"},
    {"value": "ongoing", "label": "Выходит"},
    {"value": "anons", "label": "Анонс"}
]

# ===== СЕЗОНЫ =====

SEASONS = [
    {"value": "winter", "label": "Зима", "emoji": "❄️"},
    {"value": "spring", "label": "Весна", "emoji": "🌸"},
    {"value": "summer", "label": "Лето", "emoji": "☀️"},
    {"value": "fall", "label": "Осень", "emoji": "🍂"}
]

# ===== ФУНКЦИИ-ПОМОЩНИКИ =====

def get_user_setting(key: str, default=None):
    """Получение пользовательской настройки"""
    return USER_SETTINGS.get(key, default)

def set_user_setting(key: str, value):
    """Установка пользовательской настройки"""
    USER_SETTINGS[key] = value
    # TODO: Сохранение в файл настроек

def get_cache_path(cache_type: str) -> Path:
    """Получение пути к кешу определенного типа"""
    cache_paths = {
        "posters": POSTERS_CACHE_DIR,
        "metadata": CACHE_DIR / "metadata",
        "api": CACHE_DIR / "api"
    }
    
    path = cache_paths.get(cache_type, CACHE_DIR)
    path.mkdir(exist_ok=True)
    return path

def is_development() -> bool:
    """Проверка режима разработки"""
    return os.getenv("ANIVEST_DEV", "false").lower() == "true"

# ===== ENVIRONMENT VARIABLES =====

# Загружаем настройки из переменных окружения (если есть)
if os.getenv("SHIKIMORI_BASE_URL"):
    SHIKIMORI_CONFIG["base_url"] = os.getenv("SHIKIMORI_BASE_URL")

if os.getenv("KODIK_TOKEN"):
    KODIK_CONFIG["test_tokens"].insert(0, os.getenv("KODIK_TOKEN"))

if os.getenv("DATABASE_PATH"):
    DATABASE_CONFIG["path"] = os.getenv("DATABASE_PATH")

if is_development():
    LOGGING_CONFIG["level"] = "DEBUG"
    CACHE_CONFIG["cache_timeout"] = 60  # Короткий кеш в разработке

# ===== ЭКСПОРТ =====

__all__ = [
    "APP_NAME", "APP_VERSION", "WINDOW_CONFIG",
    "SHIKIMORI_CONFIG", "KODIK_CONFIG", "CACHE_CONFIG",
    "DATABASE_CONFIG", "LOGGING_CONFIG", "USER_SETTINGS",
    "HOTKEYS", "LIMITS", "ANIME_GENRES", "ANIME_TYPES",
    "ANIME_STATUSES", "SEASONS", "get_user_setting",
    "set_user_setting", "get_cache_path", "is_development"
]