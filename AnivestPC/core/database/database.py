"""
🗃️ ANIVEST DESKTOP - УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ
===========================================
SQLite подключение и операции
(Перенесено и адаптировано из Flask сайта)
"""

import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

from config.settings import DATABASE_CONFIG
from .models import (
    DATABASE_SCHEMA, User, Comment, Favorite, WatchHistory, UserSetting,
    hash_password, verify_password, validate_email, validate_username
)

logger = logging.getLogger(__name__)

# ===== ОСНОВНОЙ КЛАСС ДЛЯ РАБОТЫ С БД =====

class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DATABASE_CONFIG["path"]
        self._ensure_db_directory()
        self.init_db()
    
    def _ensure_db_directory(self):
        """Создание директории для БД если не существует"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Получение соединения с БД"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=DATABASE_CONFIG.get("timeout", 30),
            check_same_thread=DATABASE_CONFIG.get("check_same_thread", False)
        )
        conn.row_factory = sqlite3.Row  # Для доступа к столбцам по имени
        return conn
    
    def init_db(self):
        """Инициализация базы данных - создание таблиц"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Создаем все таблицы
                for table_name, schema in DATABASE_SCHEMA.items():
                    logger.info(f"Создание таблицы: {table_name}")
                    cursor.execute(schema)
                
                conn.commit()
                logger.info("База данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    # ===== ОПЕРАЦИИ С ПОЛЬЗОВАТЕЛЯМИ =====
    
    def create_user(self, username: str, email: str, password: str, 
                   avatar_url: Optional[str] = None) -> Optional[int]:
        """Создание нового пользователя"""
        try:
            # Валидация
            if not validate_username(username):
                raise ValueError("Некорректное имя пользователя")
            if not validate_email(email):
                raise ValueError("Некорректный email")
            if len(password) < 6:
                raise ValueError("Пароль слишком короткий")
            
            password_hash = hash_password(password)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем уникальность
                existing = cursor.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?",
                    (username, email)
                ).fetchone()
                
                if existing:
                    raise ValueError("Пользователь с таким именем или email уже существует")
                
                # Создаем пользователя
                cursor.execute(
                    """INSERT INTO users (username, email, password_hash, avatar_url)
                       VALUES (?, ?, ?, ?)""",
                    (username, email, password_hash, avatar_url)
                )
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Создан пользователь: {username} (ID: {user_id})")
                return user_id
                
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                user_row = cursor.execute(
                    "SELECT * FROM users WHERE username = ? OR email = ?",
                    (username, username)
                ).fetchone()
                
                if not user_row:
                    return None
                
                user_dict = dict(user_row)
                
                # Проверяем пароль
                if not verify_password(password, user_dict["password_hash"]):
                    return None
                
                # Проверяем активность
                if not user_dict["is_active"]:
                    raise ValueError("Аккаунт заблокирован")
                
                user = User.from_dict(user_dict)
                logger.info(f"Успешная аутентификация: {user.username}")
                return user
                
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                user_row = cursor.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                ).fetchone()
                
                if user_row:
                    return User.from_dict(dict(user_row))
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Обновление данных пользователя"""
        try:
            allowed_fields = ["username", "email", "avatar_url", "is_active", "role"]
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                return False
            
            # Хешируем пароль если передан
            if "password" in kwargs:
                update_fields["password_hash"] = hash_password(kwargs["password"])
            
            # Формируем SQL
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [user_id]
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE users SET {set_clause} WHERE id = ?", values
                )
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
            return False

    # ===== ОПЕРАЦИИ С КОММЕНТАРИЯМИ =====
    
    def add_comment(self, anime_id: str, user_id: int, content: str,
                   is_spoiler: bool = False, rating: Optional[int] = None,
                   episode_number: Optional[int] = None) -> Optional[int]:
        """Добавление комментария"""
        try:
            comment = Comment(
                anime_id=anime_id,
                user_id=user_id,
                content=content.strip(),
                is_spoiler=is_spoiler,
                rating=rating,
                episode_number=episode_number
            )
            
            if not comment.is_valid():
                raise ValueError("Некорректный комментарий")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем, не оставлял ли пользователь уже комментарий к этому эпизоду
                if episode_number:
                    existing = cursor.execute(
                        """SELECT id FROM comments 
                           WHERE user_id = ? AND anime_id = ? AND episode_number = ?""",
                        (user_id, anime_id, episode_number)
                    ).fetchone()
                    
                    if existing:
                        raise ValueError("Вы уже оставили комментарий к этому эпизоду")
                
                cursor.execute(
                    """INSERT INTO comments 
                       (anime_id, user_id, content, is_spoiler, rating, episode_number)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (anime_id, user_id, content, is_spoiler, rating, episode_number)
                )
                
                comment_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Добавлен комментарий ID: {comment_id}")
                return comment_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления комментария: {e}")
            raise
    
    def get_comments(self, anime_id: str, episode: Optional[int] = None,
                    show_spoilers: bool = False, sort_by: str = "newest",
                    limit: int = 50) -> List[Comment]:
        """Получение комментариев к аниме"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Базовый запрос с JOIN для получения данных пользователя
                query = """
                    SELECT c.*, u.username, u.avatar_url, u.role as user_role,
                           COUNT(CASE WHEN cv.vote_type = 'like' THEN 1 END) as likes,
                           COUNT(CASE WHEN cv.vote_type = 'dislike' THEN 1 END) as dislikes
                    FROM comments c
                    LEFT JOIN users u ON c.user_id = u.id
                    LEFT JOIN comment_votes cv ON c.id = cv.comment_id
                    WHERE c.anime_id = ?
                """
                params = [anime_id]
                
                # Фильтр по эпизоду
                if episode:
                    query += " AND c.episode_number = ?"
                    params.append(episode)
                
                # Фильтр спойлеров
                if not show_spoilers:
                    query += " AND c.is_spoiler = 0"
                
                query += " GROUP BY c.id"
                
                # Сортировка
                if sort_by == "oldest":
                    query += " ORDER BY c.created_at ASC"
                elif sort_by == "rating":
                    query += " ORDER BY (likes - dislikes) DESC, c.created_at DESC"
                else:  # newest
                    query += " ORDER BY c.created_at DESC"
                
                query += f" LIMIT {limit}"
                
                rows = cursor.execute(query, params).fetchall()
                
                comments = []
                for row in rows:
                    comment_dict = dict(row)
                    comment = Comment.from_dict(comment_dict)
                    comments.append(comment)
                
                return comments
                
        except Exception as e:
            logger.error(f"Ошибка получения комментариев: {e}")
            return []
    
    def vote_comment(self, comment_id: int, user_id: int, vote_type: str) -> bool:
        """Лайк/дизлайк комментария"""
        try:
            if vote_type not in ["like", "dislike"]:
                raise ValueError("Неверный тип голоса")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем существование комментария
                comment_exists = cursor.execute(
                    "SELECT id FROM comments WHERE id = ?", (comment_id,)
                ).fetchone()
                
                if not comment_exists:
                    raise ValueError("Комментарий не найден")
                
                # Проверяем существующий голос
                existing_vote = cursor.execute(
                    "SELECT vote_type FROM comment_votes WHERE comment_id = ? AND user_id = ?",
                    (comment_id, user_id)
                ).fetchone()
                
                if existing_vote:
                    if existing_vote["vote_type"] == vote_type:
                        # Убираем голос
                        cursor.execute(
                            "DELETE FROM comment_votes WHERE comment_id = ? AND user_id = ?",
                            (comment_id, user_id)
                        )
                    else:
                        # Меняем голос
                        cursor.execute(
                            "UPDATE comment_votes SET vote_type = ? WHERE comment_id = ? AND user_id = ?",
                            (vote_type, comment_id, user_id)
                        )
                else:
                    # Добавляем новый голос
                    cursor.execute(
                        "INSERT INTO comment_votes (comment_id, user_id, vote_type) VALUES (?, ?, ?)",
                        (comment_id, user_id, vote_type)
                    )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка голосования: {e}")
            return False
    
    def delete_comment(self, comment_id: int, user_id: int, is_admin: bool = False) -> bool:
        """Удаление комментария"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем права на удаление
                comment_row = cursor.execute(
                    "SELECT user_id FROM comments WHERE id = ?", (comment_id,)
                ).fetchone()
                
                if not comment_row:
                    raise ValueError("Комментарий не найден")
                
                # Только автор или админ может удалить
                if comment_row["user_id"] != user_id and not is_admin:
                    raise ValueError("Недостаточно прав")
                
                # Удаляем голоса
                cursor.execute("DELETE FROM comment_votes WHERE comment_id = ?", (comment_id,))
                
                # Удаляем комментарий
                cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка удаления комментария: {e}")
            return False

    # ===== ОПЕРАЦИИ С ИЗБРАННЫМ =====
    
    def add_to_favorites(self, user_id: int, anime_id: str, 
                        anime_title: str, anime_poster_url: str = "") -> bool:
        """Добавление в избранное"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """INSERT OR REPLACE INTO favorites 
                       (user_id, anime_id, anime_title, anime_poster_url)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, anime_id, anime_title, anime_poster_url)
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")
            return False
    
    def remove_from_favorites(self, user_id: int, anime_id: str) -> bool:
        """Удаление из избранного"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM favorites WHERE user_id = ? AND anime_id = ?",
                    (user_id, anime_id)
                )
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Ошибка удаления из избранного: {e}")
            return False
    
    def get_user_favorites(self, user_id: int) -> List[Favorite]:
        """Получение избранного пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                rows = cursor.execute(
                    "SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                ).fetchall()
                
                return [Favorite.from_dict(dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения избранного: {e}")
            return []
    
    def is_in_favorites(self, user_id: int, anime_id: str) -> bool:
        """Проверка наличия в избранном"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                result = cursor.execute(
                    "SELECT id FROM favorites WHERE user_id = ? AND anime_id = ?",
                    (user_id, anime_id)
                ).fetchone()
                
                return result is not None
                
        except Exception as e:
            logger.error(f"Ошибка проверки избранного: {e}")
            return False

    # ===== ОПЕРАЦИИ С ИСТОРИЕЙ ПРОСМОТРА =====
    
    def update_watch_progress(self, user_id: int, anime_id: str, anime_title: str,
                            anime_poster_url: str = "", episode_number: int = 1,
                            season_number: int = 1, watch_time_seconds: int = 0,
                            total_time_seconds: int = 0) -> bool:
        """Обновление прогресса просмотра"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Определяем завершенность
                is_completed = False
                if total_time_seconds > 0:
                    progress = watch_time_seconds / total_time_seconds
                    is_completed = progress >= 0.95  # 95% считается завершенным
                
                cursor.execute(
                    """INSERT OR REPLACE INTO watch_history 
                       (user_id, anime_id, anime_title, anime_poster_url, 
                        episode_number, season_number, watch_time_seconds, 
                        total_time_seconds, is_completed, last_watched)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, anime_id, anime_title, anime_poster_url,
                     episode_number, season_number, watch_time_seconds,
                     total_time_seconds, is_completed)
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления прогресса: {e}")
            return False
    
    def get_user_watch_history(self, user_id: int, limit: int = 50) -> List[WatchHistory]:
        """Получение истории просмотра пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                rows = cursor.execute(
                    """SELECT * FROM watch_history 
                       WHERE user_id = ? 
                       ORDER BY last_watched DESC 
                       LIMIT ?""",
                    (user_id, limit)
                ).fetchall()
                
                return [WatchHistory.from_dict(dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения истории просмотра: {e}")
            return []
    
    def get_watch_progress(self, user_id: int, anime_id: str) -> Optional[WatchHistory]:
        """Получение прогресса просмотра конкретного аниме"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                row = cursor.execute(
                    "SELECT * FROM watch_history WHERE user_id = ? AND anime_id = ?",
                    (user_id, anime_id)
                ).fetchone()
                
                if row:
                    return WatchHistory.from_dict(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения прогресса: {e}")
            return None

    # ===== ОПЕРАЦИИ С НАСТРОЙКАМИ =====
    
    def set_user_setting(self, user_id: int, key: str, value: Any) -> bool:
        """Установка пользовательской настройки"""
        try:
            # Конвертируем значение в JSON строку
            value_str = json.dumps(value) if value is not None else None
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """INSERT OR REPLACE INTO user_settings 
                       (user_id, setting_key, setting_value, updated_at)
                       VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, key, value_str)
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка установки настройки: {e}")
            return False
    
    def get_user_setting(self, user_id: int, key: str, default: Any = None) -> Any:
        """Получение пользовательской настройки"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                row = cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = ?",
                    (user_id, key)
                ).fetchone()
                
                if row and row["setting_value"] is not None:
                    return json.loads(row["setting_value"])
                return default
                
        except Exception as e:
            logger.error(f"Ошибка получения настройки: {e}")
            return default
    
    def get_all_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получение всех настроек пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                rows = cursor.execute(
                    "SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?",
                    (user_id,)
                ).fetchall()
                
                settings = {}
                for row in rows:
                    key = row["setting_key"]
                    value = row["setting_value"]
                    try:
                        settings[key] = json.loads(value) if value else None
                    except:
                        settings[key] = value
                
                return settings
                
        except Exception as e:
            logger.error(f"Ошибка получения настроек: {e}")
            return {}

    # ===== СЛУЖЕБНЫЕ МЕТОДЫ =====
    
    def cleanup_old_data(self, days: int = 30):
        """Очистка старых данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Удаляем старые логи голосований (оставляем только результат)
                cursor.execute(
                    """DELETE FROM comment_votes 
                       WHERE created_at < datetime('now', '-{} days')""".format(days)
                )
                
                conn.commit()
                logger.info(f"Очищены старые данные (старше {days} дней)")
                
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики БД"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                tables = ["users", "comments", "favorites", "watch_history"]
                
                for table in tables:
                    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    stats[table] = count
                
                return stats
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}

# ===== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР =====

# Создаем глобальный экземпляр менеджера БД
db_manager = DatabaseManager()

# ===== ЭКСПОРТ =====

__all__ = [
    "DatabaseManager", "db_manager"
]