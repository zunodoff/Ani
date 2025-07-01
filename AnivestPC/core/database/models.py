"""
🗃️ ANIVEST DESKTOP - МОДЕЛИ БАЗЫ ДАННЫХ
======================================
SQLite модели пользователей, комментариев, избранного
(Перенесено из Flask сайта)
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

# ===== СХЕМЫ БД =====

DATABASE_SCHEMA = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            avatar_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            role VARCHAR(20) DEFAULT 'user'
        )
    """,
    
    "comments": """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id VARCHAR(100) NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_spoiler BOOLEAN DEFAULT 0,
            rating INTEGER CHECK(rating >= 1 AND rating <= 10),
            episode_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """,
    
    "comment_votes": """
        CREATE TABLE IF NOT EXISTS comment_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vote_type VARCHAR(10) CHECK(vote_type IN ('like', 'dislike')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(comment_id, user_id),
            FOREIGN KEY (comment_id) REFERENCES comments (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """,
    
    "favorites": """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_id VARCHAR(100) NOT NULL,
            anime_title VARCHAR(255),
            anime_poster_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """,
    
    "watch_history": """
        CREATE TABLE IF NOT EXISTS watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_id VARCHAR(100) NOT NULL,
            anime_title VARCHAR(255),
            anime_poster_url VARCHAR(500),
            episode_number INTEGER DEFAULT 1,
            season_number INTEGER DEFAULT 1,
            watch_time_seconds INTEGER DEFAULT 0,
            total_time_seconds INTEGER DEFAULT 0,
            last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0,
            UNIQUE(user_id, anime_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """,
    
    "user_settings": """
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            setting_key VARCHAR(100) NOT NULL,
            setting_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, setting_key),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """
}

# ===== МОДЕЛИ ДАННЫХ =====

@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    is_active: bool = True
    role: str = "user"
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Создание из словаря"""
        return cls(**data)
    
    def is_admin(self) -> bool:
        """Проверка админских прав"""
        return self.role == "admin"

@dataclass
class Comment:
    """Модель комментария"""
    id: Optional[int] = None
    anime_id: str = ""
    user_id: int = 0
    content: str = ""
    is_spoiler: bool = False
    rating: Optional[int] = None
    episode_number: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    likes: int = 0
    dislikes: int = 0
    
    # Дополнительные поля из JOIN
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    user_role: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """Создание из словаря"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def is_valid(self) -> bool:
        """Валидация комментария"""
        if not self.content or len(self.content.strip()) < 10:
            return False
        if self.rating and (self.rating < 1 or self.rating > 10):
            return False
        return True

@dataclass  
class Favorite:
    """Модель избранного аниме"""
    id: Optional[int] = None
    user_id: int = 0
    anime_id: str = ""
    anime_title: Optional[str] = None
    anime_poster_url: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Favorite':
        """Создание из словаря"""
        return cls(**data)

@dataclass
class WatchHistory:
    """Модель истории просмотра"""
    id: Optional[int] = None
    user_id: int = 0
    anime_id: str = ""
    anime_title: Optional[str] = None
    anime_poster_url: Optional[str] = None
    episode_number: int = 1
    season_number: int = 1
    watch_time_seconds: int = 0
    total_time_seconds: int = 0
    last_watched: Optional[str] = None
    is_completed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatchHistory':
        """Создание из словаря"""
        return cls(**data)
    
    def get_progress_percent(self) -> float:
        """Получение процента просмотра"""
        if self.total_time_seconds <= 0:
            return 0.0
        return min(100.0, (self.watch_time_seconds / self.total_time_seconds) * 100)

@dataclass
class UserSetting:
    """Модель пользовательской настройки"""
    id: Optional[int] = None
    user_id: int = 0
    setting_key: str = ""
    setting_value: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSetting':
        """Создание из словаря"""
        return cls(**data)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Проверка пароля"""
    return hash_password(password) == password_hash

def validate_email(email: str) -> bool:
    """Простая валидация email"""
    return "@" in email and "." in email.split("@")[1]

def validate_username(username: str) -> bool:
    """Валидация имени пользователя"""
    return len(username) >= 3 and username.isalnum()

def format_datetime(dt_string: Optional[str]) -> str:
    """Форматирование даты для отображения"""
    if not dt_string:
        return ""
    
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_string

def format_relative_time(dt_string: Optional[str]) -> str:
    """Относительное время (например, '2 часа назад')"""
    if not dt_string:
        return ""
    
    try:
        dt = datetime.fromisoformat(dt_string)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} ч. назад"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} мин. назад"
        else:
            return "только что"
    except:
        return dt_string

# ===== КОНСТАНТЫ =====

class UserRole:
    """Роли пользователей"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

class VoteType:
    """Типы голосов"""
    LIKE = "like"
    DISLIKE = "dislike"

class WatchStatus:
    """Статусы просмотра"""
    WATCHING = "watching"
    COMPLETED = "completed"
    PLAN_TO_WATCH = "plan_to_watch"
    DROPPED = "dropped"
    ON_HOLD = "on_hold"

# ===== ЭКСПОРТ =====

__all__ = [
    "DATABASE_SCHEMA", "User", "Comment", "Favorite", "WatchHistory", 
    "UserSetting", "hash_password", "verify_password", "validate_email",
    "validate_username", "format_datetime", "format_relative_time",
    "UserRole", "VoteType", "WatchStatus"
]