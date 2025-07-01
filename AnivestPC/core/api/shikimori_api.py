"""
🌸 ANIVEST DESKTOP - SHIKIMORI API
================================
Интеграция с Shikimori для получения информации об аниме
(Перенесено и адаптировано из Flask сайта)
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx

from config.settings import SHIKIMORI_CONFIG, CACHE_CONFIG

logger = logging.getLogger(__name__)

# ===== ОПРЕДЕЛЕНИЕ СЕЗОНОВ =====

def get_current_season() -> tuple[str, int]:
    """Определение текущего сезона аниме"""
    now = datetime.now()
    month = now.month
    year = now.year
    
    # Определяем сезон по месяцу
    if month in [1, 2, 3]:  # Зима: декабрь, январь, февраль
        season = 'winter'
        # Если декабрь, то это зима следующего года
        if month == 12:
            year += 1
    elif month in [4, 5, 6]:  # Весна: март, апрель, май
        season = 'spring'
    elif month in [7, 8, 9]:  # Лето: июнь, июль, август
        season = 'summer'
    else:  # Осень: сентябрь, октябрь, ноябрь
        season = 'fall'
    
    return season, year

def get_season_name_ru(season: str) -> str:
    """Получение русского названия сезона"""
    season_names = {
        'winter': 'зимнего',
        'spring': 'весеннего', 
        'summer': 'летнего',
        'fall': 'осеннего'
    }
    return season_names.get(season, 'текущего')

def get_season_emoji(season: str) -> str:
    """Получение эмодзи для сезона"""
    season_emojis = {
        'winter': '❄️',
        'spring': '🌸',
        'summer': '☀️', 
        'fall': '🍂'
    }
    return season_emojis.get(season, '🌟')

# ===== ОСНОВНОЙ КЛАСС API =====

class ShikimoriAPI:
    """Клиент для работы с Shikimori API"""
    
    def __init__(self):
        self.base_url = SHIKIMORI_CONFIG["base_url"]
        self.user_agent = SHIKIMORI_CONFIG["user_agent"]
        self.timeout = SHIKIMORI_CONFIG["timeout"]
        self.cache_timeout = SHIKIMORI_CONFIG["cache_timeout"]
        self.rate_limit = SHIKIMORI_CONFIG["rate_limit"]
        
        # Кеш запросов
        self.cache = {}
        self.last_request_time = 0
        
        # HTTP клиент
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Получение HTTP клиента"""
        if self.client is None or self.client.is_closed:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            self.client = httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            )
        
        return self.client
    
    async def _rate_limit_delay(self):
        """Контроль частоты запросов"""
        if self.rate_limit <= 0:
            return
            
        time_since_last = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            delay = min_interval - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Базовый метод для выполнения запросов к Shikimori API"""
        cache_key = f"shiki_{endpoint}_{str(params)}"
        
        # Проверяем кеш
        if CACHE_CONFIG["enabled"] and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                logger.debug(f"Shikimori cache hit: {endpoint}")
                return cached_data
        
        try:
            # Контроль частоты запросов
            await self._rate_limit_delay()
            
            client = await self._get_client()
            
            # Подготовка параметров
            full_params = {}
            if params:
                full_params.update(params)
            
            url = f"{self.base_url}/{endpoint}"
            logger.info(f"Shikimori request: {url} with params: {full_params}")
            
            # Выполнение запроса
            response = await client.get(url, params=full_params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Shikimori response: {len(data) if isinstance(data, list) else 1} items")
            
            # Логируем первый элемент для диагностики
            if isinstance(data, list) and data:
                first_item = data[0]
                logger.debug(f"Первый элемент: {first_item.get('name')} [{first_item.get('kind')}] - рейтинг: {first_item.get('score')}")
            
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
            logger.error(f"Ошибка Shikimori API запроса: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка Shikimori API: {e.response.status_code}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от Shikimori: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка Shikimori API: {e}")
            return None
    
    async def search_anime(self, query: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Поиск аниме в Shikimori"""
        params = {
            'limit': 50,
            'censored': 'true'  # Скрываем 18+ контент
        }
        
        if query:
            params['search'] = query
            
        if filters:
            # Маппинг наших фильтров на Shikimori параметры
            if filters.get('genre'):
                # Русские жанры → ID жанров для Shikimori
                genre_mapping = {
                    'Экшен': '1',          # Action
                    'Приключения': '2',    # Adventure
                    'Комедия': '4',        # Comedy
                    'Драма': '8',          # Drama
                    'Фэнтези': '10',       # Fantasy
                    'Романтика': '22',     # Romance
                    'Фантастика': '24',    # Sci-Fi
                    'Сверхъестественное': '37',  # Supernatural
                    'Психологическое': '40',     # Psychological
                    'Триллер': '41',       # Thriller
                    'Повседневность': '36', # Slice of Life
                    'Школа': '23',         # School
                    'Спорт': '30',         # Sports
                    'Военное': '38',       # Military
                    'Исторический': '13'   # Historical
                }
                genre = filters['genre']
                mapped_genre = genre_mapping.get(genre)
                if mapped_genre:
                    params['genre'] = mapped_genre
                    logger.debug(f"Маппинг жанра: {genre} → ID {mapped_genre}")
                    
            if filters.get('type'):
                # Маппинг типов
                type_mapping = {
                    'tv': 'tv',
                    'movie': 'movie', 
                    'ova': 'ova',
                    'ona': 'ona',
                    'special': 'special'
                }
                filter_type = filters['type']
                if filter_type in type_mapping:
                    params['kind'] = type_mapping[filter_type]
                    
            if filters.get('status'):
                # Маппинг статусов
                status_mapping = {
                    'released': 'released',
                    'ongoing': 'ongoing', 
                    'anons': 'anons'
                }
                if filters['status'] in status_mapping:
                    params['status'] = status_mapping[filters['status']]
            
            # Обработка сезонного фильтра
            if filters.get('season'):
                # Формат: "summer_2025"
                params['season'] = filters['season']
                logger.debug(f"Фильтр по сезону: {filters['season']}")
                    
            # Обработка диапазона годов
            elif filters.get('year_from') and filters.get('year_to'):
                year_from = filters['year_from']
                year_to = filters['year_to']
                
                # Если года одинаковые, используем season для конкретного года
                if year_from == year_to:
                    params['season'] = str(year_from)
                    logger.debug(f"Фильтр по году: {year_from}")
            elif filters.get('year_from'):
                # Только начальный год
                params['season'] = f"{filters['year_from']}"
            elif filters.get('year_to'):
                # Только конечный год
                params['season'] = f"{filters['year_to']}"
            elif filters.get('year'):
                # Старый параметр year для совместимости
                params['season'] = f"{filters['year']}"
                    
        # Сортировка по популярности по умолчанию
        if 'order' not in params:
            params['order'] = 'popularity'
        
        logger.info(f"Поиск аниме: query='{query}', params={params}")
        
        result = await self._make_request('animes', params)
        return result if result else []
    
    async def get_anime(self, anime_id: str) -> Optional[Dict]:
        """Получение информации об одном аниме"""
        result = await self._make_request(f'animes/{anime_id}')
        return result
    
    async def get_seasonal_anime(self, season: Optional[str] = None, 
                                year: Optional[int] = None, limit: int = 20) -> List[Dict]:
        """Получение популярных аниме текущего/указанного сезона"""
        if not season or not year:
            # Если сезон не указан, получаем текущий
            season, year = get_current_season()
        
        # Сначала пробуем строгие параметры
        params = {
            'limit': limit * 3,  # Запрашиваем больше для фильтрации
            'season': f'{season}_{year}',
            'order': 'popularity',
            'censored': 'true',
            'status': 'released,ongoing'  # Только вышедшие и онгоинги
        }
        
        logger.info(f"Запрос сезонных аниме: {season}_{year}")
        
        # Получаем данные от Shikimori
        all_results = await self._make_request('animes', params)
        
        if not all_results:
            logger.warning("Не удалось получить сезонные аниме, пробуем без фильтров сезона")
            # Fallback: получаем популярные аниме этого года
            fallback_params = {
                'limit': limit * 2,
                'order': 'popularity',
                'censored': 'true',
                'season': str(year)
            }
            all_results = await self._make_request('animes', fallback_params)
        
        if not all_results:
            logger.warning("Fallback тоже не сработал")
            return []
        
        # Фильтрация на стороне клиента для получения только аниме
        filtered_results = []
        for anime in all_results:
            anime_kind = anime.get('kind', '')
            anime_score = float(anime.get('score', 0) or 0)
            scored_by = int(anime.get('scored_by', 0) or 0)
            
            # ✅ Более мягкие фильтры для аниме:
            if (anime_kind in ['tv', 'movie', 'ova', 'ona', 'special'] and  # Только аниме
                (anime_score >= 5.0 or scored_by >= 500)):  # Либо хороший рейтинг, либо популярность
                
                # Добавляем показатель популярности для сортировки
                anime['popularity_score'] = (scored_by * 0.1) + (anime_score * 1000)
                filtered_results.append(anime)
        
        # Сортируем по популярности
        filtered_results.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
        
        # Возвращаем топ аниме
        top_results = filtered_results[:limit]
        
        logger.info(f"Возвращаем {len(top_results)} сезонных аниме для {season}_{year}")
        
        # Логируем топ-3 для проверки
        for i, anime in enumerate(top_results[:3], 1):
            score = anime.get('score', 'N/A')
            scored_by = anime.get('scored_by', 'N/A')
            kind = anime.get('kind', 'N/A')
            logger.debug(f"#{i}: {anime.get('name')} [{kind}] - Рейтинг: {score}, Оценок: {scored_by}")
        
        return top_results
    
    async def get_popular_anime(self, limit: int = 20) -> List[Dict]:
        """Получение популярных аниме всех времён"""
        params = {
            'limit': limit * 2,  # Запрашиваем больше для фильтрации
            'order': 'popularity',
            'censored': 'true'
        }
        
        logger.info(f"Запрос {limit} популярных аниме")
        
        # Получаем данные от Shikimori
        all_results = await self._make_request('animes', params)
        
        if not all_results:
            return []
        
        # Фильтрация популярных аниме
        filtered_results = []
        for anime in all_results:
            anime_kind = anime.get('kind', '')
            anime_score = float(anime.get('score', 0) or 0)
            scored_by = int(anime.get('scored_by', 0) or 0)
            
            # ✅ Более мягкие фильтры для популярных аниме:
            if (anime_kind in ['tv', 'movie', 'ova', 'ona', 'special'] and  # Только аниме
                (anime_score >= 6.0 or scored_by >= 1000)):  # Либо хороший рейтинг, либо много оценок
                
                filtered_results.append(anime)
        
        # Сортируем по рейтингу и популярности
        filtered_results.sort(key=lambda x: (float(x.get('score', 0) or 0), int(x.get('scored_by', 0) or 0)), reverse=True)
        
        # Возвращаем топ популярных аниме
        top_results = filtered_results[:limit]
        
        logger.info(f"Возвращаем {len(top_results)} популярных аниме")
        
        return top_results
    
    async def get_anime_characters(self, anime_id: str) -> List[Dict]:
        """Получение персонажей аниме"""
        result = await self._make_request(f'animes/{anime_id}/characters')
        return result if result else []
    
    async def get_anime_similar(self, anime_id: str) -> List[Dict]:
        """Получение похожих аниме"""
        result = await self._make_request(f'animes/{anime_id}/similar')
        return result if result else []
    
    async def get_anime_screenshots(self, anime_id: str) -> List[Dict]:
        """Получение скриншотов аниме"""
        result = await self._make_request(f'animes/{anime_id}/screenshots')
        return result if result else []
    
    async def close(self):
        """Закрытие HTTP клиента"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    def clear_cache(self):
        """Очистка кеша"""
        self.cache.clear()
        logger.info("Кеш Shikimori API очищен")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Статистика кеша"""
        return {
            "cache_size": len(self.cache),
            "max_size": CACHE_CONFIG["max_size"],
            "cache_timeout": self.cache_timeout,
            "rate_limit": self.rate_limit
        }

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def extract_year_from_date(date_string: Optional[str]) -> Optional[int]:
    """Извлечение года из даты"""
    if date_string:
        try:
            return int(date_string.split('-')[0])
        except:
            pass
    return None

def get_poster_url(shikimori_anime: Dict) -> str:
    """Получение URL постера из Shikimori с улучшенной обработкой ошибок"""
    image = shikimori_anime.get('image', {})
    
    if isinstance(image, dict):
        # Получаем URL и добавляем домен Shikimori если нужно
        poster_url = None
        
        # Пробуем разные размеры (от большего к меньшему)
        for size in ['original', 'preview', 'x96', 'x48']:
            if image.get(size):
                poster_url = image[size]
                break
        
        if poster_url:
            # Если URL относительный, добавляем домен Shikimori
            if poster_url.startswith('/'):
                poster_url = f"https://shikimori.one{poster_url}"
            elif not poster_url.startswith('http'):
                poster_url = f"https://shikimori.one{poster_url}"
            
            # *** ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: если URL содержит индикаторы ошибок ***
            if any(error_indicator in poster_url.lower() 
                   for error_indicator in ['404', 'not_found', 'notfound', 'error', 'missing', 'no+image']):
                logger.warning(f"Обнаружен проблемный URL постера: {poster_url}")
                return 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера'
            
            return poster_url
    
    # Fallback постер
    return 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера'

def convert_shikimori_format(shikimori_anime: Dict) -> Dict:
    """Конвертация формата Shikimori в наш формат"""
    # Мапим поля Shikimori на наш формат
    converted = {
        'id': f"shiki_{shikimori_anime['id']}",  # Префикс для различения
        'shikimori_id': shikimori_anime['id'],
        'title': shikimori_anime.get('russian') or shikimori_anime.get('name', ''),
        'title_orig': shikimori_anime.get('name', ''),
        'other_title': shikimori_anime.get('synonyms', []),
        'year': extract_year_from_date(shikimori_anime.get('aired_on')),
        'type': 'anime',
        'link': None,  # Будет заполнено из Kodik
        'kodik_id': None,
        'translation': None,
        'quality': None,
        'episodes_count': shikimori_anime.get('episodes'),
        'last_episode': None,
        'seasons': None,
        'screenshots': [],
        
        # Материальные данные (совместимость с шаблонами)
        'material_data': {
            'title': shikimori_anime.get('russian') or shikimori_anime.get('name', ''),
            'title_en': shikimori_anime.get('name', ''),
            'anime_title': shikimori_anime.get('russian') or shikimori_anime.get('name', ''),
            'description': shikimori_anime.get('description', ''),
            'anime_description': shikimori_anime.get('description', ''),
            'poster_url': get_poster_url(shikimori_anime),
            'anime_poster_url': get_poster_url(shikimori_anime),
            'shikimori_rating': shikimori_anime.get('score'),
            'shikimori_votes': shikimori_anime.get('scored_by'),
            'anime_kind': shikimori_anime.get('kind'),
            'anime_status': shikimori_anime.get('status'),
            'all_status': shikimori_anime.get('status'),
            'anime_genres': [g['russian'] for g in shikimori_anime.get('genres', []) if g.get('russian')],
            'all_genres': [g['russian'] for g in shikimori_anime.get('genres', []) if g.get('russian')],
            'episodes_total': shikimori_anime.get('episodes'),
            'episodes_aired': shikimori_anime.get('episodes_aired'),
            'anime_studios': [s['name'] for s in shikimori_anime.get('studios', [])],
            'rating_mpaa': shikimori_anime.get('rating'),
            'aired_at': shikimori_anime.get('aired_on'),
            'released_at': shikimori_anime.get('released_on'),
            'year': extract_year_from_date(shikimori_anime.get('aired_on'))
        }
    }
    
    return converted

# ===== ЭКСПОРТ =====

__all__ = [
    "ShikimoriAPI", "get_current_season", "get_season_name_ru", 
    "get_season_emoji", "extract_year_from_date", "get_poster_url",
    "convert_shikimori_format"
]