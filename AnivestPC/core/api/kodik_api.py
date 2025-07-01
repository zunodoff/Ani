"""
🎬 ANIVEST DESKTOP - KODIK API
============================
Интеграция с Kodik для получения ссылок на видео
(Перенесено и адаптировано из Flask сайта)
"""

import asyncio
import logging
import time
import json
from typing import Optional, List, Dict, Any
import httpx

from config.settings import KODIK_CONFIG, CACHE_CONFIG

logger = logging.getLogger(__name__)

# ===== ОСНОВНОЙ КЛАСС API =====

class KodikAPI:
    """Клиент для работы с Kodik API"""
    
    def __init__(self):
        self.base_url = KODIK_CONFIG["base_url"]
        self.timeout = KODIK_CONFIG["timeout"]
        self.cache_timeout = KODIK_CONFIG["cache_timeout"]
        self.test_tokens = KODIK_CONFIG["test_tokens"]
        
        # Текущий рабочий токен
        self.token = None
        
        # Кеш запросов
        self.cache = {}
        
        # HTTP клиент
        self.client = None
        
        # Инициализируем токен при создании
        asyncio.create_task(self._initialize_token())
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Получение HTTP клиента"""
        if self.client is None or self.client.is_closed:
            headers = {
                'User-Agent': 'Anivest Desktop/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            self.client = httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            )
        
        return self.client
    
    async def _initialize_token(self):
        """Инициализация токена при создании объекта"""
        await self.get_token()
    
    async def get_token(self) -> Optional[str]:
        """Получение рабочего токена для API"""
        if self.token:
            return self.token
            
        for token in self.test_tokens:
            try:
                client = await self._get_client()
                
                response = await client.post(
                    f"{self.base_url}/list",
                    data={"token": token, "limit": 1}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results') is not None:  # Проверяем структуру ответа
                        self.token = token
                        logger.info(f"Kodik токен найден: {token[:10]}...")
                        return token
                        
            except Exception as e:
                logger.debug(f"Ошибка при проверке Kodik токена {token[:10]}...: {e}")
                continue
        
        logger.warning("Не удалось найти рабочий Kodik токен!")
        return None
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Базовый метод для выполнения запросов к Kodik API"""
        if not self.token:
            await self.get_token()
            
        if not self.token:
            logger.error("Kodik токен недоступен")
            return None
        
        cache_key = f"kodik_{endpoint}_{str(params)}"
        
        # Проверяем кеш
        if CACHE_CONFIG["enabled"] and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                logger.debug(f"Kodik cache hit: {endpoint}")
                return cached_data
        
        try:
            client = await self._get_client()
            
            # Подготовка параметров
            full_params = {"token": self.token}
            if params:
                full_params.update(params)
                
            url = f"{self.base_url}/{endpoint}"
            logger.debug(f"Kodik request: {url} with params: {full_params}")
            
            # Kodik использует POST для всех запросов
            response = await client.post(url, data=full_params)
            response.raise_for_status()
            
            data = response.json()
            
            # Проверяем структуру ответа
            if 'results' not in data:
                logger.warning(f"Неожиданная структура ответа Kodik: {data}")
                return None
            
            logger.debug(f"Kodik response: {len(data.get('results', []))} results")
            
            # Кешируем результат
            if CACHE_CONFIG["enabled"]:
                self.cache[cache_key] = (data, time.time())
                
                # Ограничиваем размер кеша
                if len(self.cache) > CACHE_CONFIG["max_size"]:
                    # Удаляем самые старые записи
                    sorted_cache = sorted(self.cache.items(), key=lambda x: x[1][1])
                    for old_key, _ in sorted_cache[:len(self.cache) // 4]:
                        del self.cache[old_key]
            
            return data
            
        except httpx.RequestError as e:
            logger.error(f"Ошибка Kodik API запроса: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка Kodik API: {e.response.status_code}")
            # Если токен невалидный, сбрасываем его
            if e.response.status_code in [401, 403]:
                self.token = None
                logger.warning("Kodik токен сброшен из-за ошибки авторизации")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от Kodik: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка Kodik API: {e}")
            return None
    
    async def search_by_shikimori_id(self, shikimori_id: str) -> Optional[Dict]:
        """Поиск в Kodik по shikimori_id"""
        params = {
            "shikimori_id": shikimori_id,
            "with_material_data": "true",
            "limit": 20
        }
        
        logger.debug(f"Поиск в Kodik по Shikimori ID: {shikimori_id}")
        return await self._make_request("search", params)
    
    async def search_by_title(self, title: str) -> Optional[Dict]:
        """Поиск в Kodik по названию"""
        if not title.strip():
            return None
            
        params = {
            "title": title.strip(),
            "with_material_data": "true",
            "limit": 10
        }
        
        logger.debug(f"Поиск в Kodik по названию: {title}")
        return await self._make_request("search", params)
    
    async def search_by_kinopoisk_id(self, kinopoisk_id: str) -> Optional[Dict]:
        """Поиск в Kodik по kinopoisk_id"""
        params = {
            "kinopoisk_id": kinopoisk_id,
            "with_material_data": "true",
            "limit": 10
        }
        
        logger.debug(f"Поиск в Kodik по Kinopoisk ID: {kinopoisk_id}")
        return await self._make_request("search", params)
    
    async def search_by_imdb_id(self, imdb_id: str) -> Optional[Dict]:
        """Поиск в Kodik по imdb_id"""
        params = {
            "imdb_id": imdb_id,
            "with_material_data": "true",
            "limit": 10
        }
        
        logger.debug(f"Поиск в Kodik по IMDB ID: {imdb_id}")
        return await self._make_request("search", params)
    
    async def get_anime_list(self, limit: int = 50, page: int = 1) -> Optional[Dict]:
        """Получение списка аниме из Kodik"""
        params = {
            "types": "anime-serial,anime",
            "limit": min(limit, 100),  # Ограничиваем лимит
            "page": page,
            "with_material_data": "true",
            "sort": "updated_at"
        }
        
        logger.debug(f"Получение списка аниме: страница {page}, лимит {limit}")
        return await self._make_request("list", params)
    
    async def get_popular_anime(self, limit: int = 20) -> List[Dict]:
        """Получение популярных аниме из Kodik"""
        try:
            # Получаем несколько страниц для большего выбора
            all_anime = []
            
            for page in range(1, 4):  # Получаем первые 3 страницы
                result = await self.get_anime_list(limit=50, page=page)
                
                if result and result.get('results'):
                    all_anime.extend(result['results'])
                else:
                    break
            
            # Фильтруем и сортируем
            filtered_anime = []
            for anime in all_anime:
                material_data = anime.get('material_data', {})
                
                # Проверяем что это действительно аниме
                anime_kind = material_data.get('anime_kind', '')
                if anime_kind in ['tv', 'movie', 'ova', 'ona', 'special']:
                    
                    # Добавляем метрики для сортировки
                    rating = float(material_data.get('shikimori_rating', 0) or 0)
                    votes = int(material_data.get('shikimori_votes', 0) or 0)
                    
                    if rating > 0 or votes > 0:
                        anime['popularity_score'] = (votes * 0.1) + (rating * 1000)
                        filtered_anime.append(anime)
            
            # Сортируем по популярности
            filtered_anime.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
            
            # Возвращаем топ
            return filtered_anime[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка получения популярных аниме из Kodik: {e}")
            return []
    
    async def get_anime_episodes(self, kodik_id: str) -> List[Dict]:
        """Получение списка эпизодов аниме"""
        try:
            # Kodik возвращает информацию об эпизодах в основном запросе
            params = {
                "id": kodik_id,
                "with_episodes": "true",
                "with_material_data": "true"
            }
            
            result = await self._make_request("search", params)
            
            if result and result.get('results'):
                anime = result['results'][0]
                
                # Извлекаем эпизоды из объекта seasons
                episodes = []
                seasons_data = anime.get('seasons', {})
                
                for season_num, season_data in seasons_data.items():
                    season_episodes = season_data.get('episodes', {})
                    
                    for ep_num, ep_data in season_episodes.items():
                        episode = {
                            'season': int(season_num),
                            'episode': int(ep_num),
                            'title': ep_data.get('title', f"Эпизод {ep_num}"),
                            'link': ep_data.get('link', ''),
                            'screenshot': ep_data.get('screenshot', '')
                        }
                        episodes.append(episode)
                
                # Сортируем по сезону и эпизоду
                episodes.sort(key=lambda x: (x['season'], x['episode']))
                return episodes
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения эпизодов: {e}")
            return []
    
    async def get_video_link(self, kodik_id: str, season: int = 1, episode: int = 1) -> Optional[str]:
        """Получение прямой ссылки на видео"""
        try:
            episodes = await self.get_anime_episodes(kodik_id)
            
            # Ищем нужный эпизод
            for ep in episodes:
                if ep['season'] == season and ep['episode'] == episode:
                    return ep['link']
            
            # Если не нашли точное соответствие, возвращаем первый доступный
            if episodes:
                return episodes[0]['link']
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения ссылки на видео: {e}")
            return None
    
    async def close(self):
        """Закрытие HTTP клиента"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    def clear_cache(self):
        """Очистка кеша"""
        self.cache.clear()
        logger.info("Кеш Kodik API очищен")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Статистика кеша"""
        return {
            "cache_size": len(self.cache),
            "max_size": CACHE_CONFIG["max_size"],
            "cache_timeout": self.cache_timeout,
            "token_available": self.token is not None,
            "current_token": self.token[:10] + "..." if self.token else None
        }
    
    def reset_token(self):
        """Сброс токена (для принудительного обновления)"""
        self.token = None
        logger.info("Kodik токен сброшен")

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def extract_kodik_data(kodik_result: Dict) -> Dict:
    """Извлечение данных из результата Kodik"""
    if not kodik_result or 'results' not in kodik_result:
        return {}
    
    results = kodik_result['results']
    if not results:
        return {}
    
    # Берем первый результат
    anime = results[0]
    
    return {
        'kodik_id': anime.get('id'),
        'link': anime.get('link'),
        'translation': anime.get('translation', {}).get('title', 'Неизвестно'),
        'translation_id': anime.get('translation', {}).get('id'),
        'quality': anime.get('quality', 'SD'),
        'episodes_count': anime.get('episodes_count'),
        'seasons_count': anime.get('seasons_count'),
        'last_episode': anime.get('last_episode'),
        'last_season': anime.get('last_season'),
        'screenshots': anime.get('screenshots', []),
        'updated_at': anime.get('updated_at'),
        'created_at': anime.get('created_at'),
        
        # Материальные данные
        'material_data': anime.get('material_data', {}),
        
        # Информация о сезонах и эпизодах
        'seasons': anime.get('seasons', {}),
    }

def get_best_translation(kodik_results: List[Dict]) -> Optional[Dict]:
    """Выбор лучшего перевода из результатов Kodik"""
    if not kodik_results:
        return None
    
    # Приоритет переводов (от лучшего к худшему)
    translation_priority = [
        'AniDub', 'Animedia', 'AniLibria', 'AniStar',
        'Субтитры', 'Многоголосый', 'Дубляж',
        'Оригинал', 'Русский'
    ]
    
    # Сначала пробуем найти по приоритету
    for priority_translation in translation_priority:
        for result in kodik_results:
            translation = result.get('translation', {}).get('title', '')
            if priority_translation.lower() in translation.lower():
                return result
    
    # Если не нашли приоритетный, возвращаем первый
    return kodik_results[0] if kodik_results else None

def get_anime_quality_priority(quality: str) -> int:
    """Получение приоритета качества видео"""
    quality_priorities = {
        '2160p': 100,  # 4K
        '1440p': 90,   # 2K
        '1080p': 80,   # Full HD
        '720p': 70,    # HD
        '480p': 60,    # SD
        '360p': 50,    # Low
        'HD': 75,      # Общее HD
        'SD': 55,      # Общее SD
    }
    
    return quality_priorities.get(quality, 0)

def format_translation_info(translation_data: Dict) -> str:
    """Форматирование информации о переводе"""
    if not translation_data:
        return "Неизвестно"
    
    title = translation_data.get('title', 'Неизвестно')
    type_name = translation_data.get('type', '')
    
    if type_name:
        return f"{title} ({type_name})"
    
    return title

def format_quality_info(quality: str, episodes_count: Optional[int] = None) -> str:
    """Форматирование информации о качестве"""
    quality_text = quality or 'SD'
    
    if episodes_count:
        if episodes_count == 1:
            return f"{quality_text} • 1 эпизод"
        else:
            return f"{quality_text} • {episodes_count} эп."
    
    return quality_text

# ===== ЭКСПОРТ =====

__all__ = [
    "KodikAPI", "extract_kodik_data", "get_best_translation",
    "get_anime_quality_priority", "format_translation_info",
    "format_quality_info"
]