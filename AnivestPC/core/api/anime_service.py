"""
🔥 ANIVEST DESKTOP - ГИБРИДНЫЙ СЕРВИС АНИМЕ
=========================================
Объединение данных из Shikimori и Kodik API
(Перенесено и адаптировано из Flask сайта)
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
import httpx

from .shikimori_api import ShikimoriAPI, convert_shikimori_format, extract_year_from_date
from .kodik_api import KodikAPI, extract_kodik_data, get_best_translation
from config.settings import CACHE_CONFIG

logger = logging.getLogger(__name__)

# ===== ОСНОВНОЙ ГИБРИДНЫЙ СЕРВИС =====

class HybridAnimeService:
    """Гибридный сервис, использующий Shikimori для поиска и Kodik для плеера"""
    
    def __init__(self):
        self.shikimori = ShikimoriAPI()
        self.kodik = KodikAPI()
        self.poster_cache = {}  # Кеш проверок доступности постеров
        self.merge_cache = {}   # Кеш объединенных данных
        
    async def _check_image_availability(self, url: str, timeout: int = 3) -> bool:
        """Проверка доступности изображения по URL"""
        if not url:
            return False
            
        # Проверяем кеш
        if url in self.poster_cache:
            return self.poster_cache[url]
        
        try:
            # Делаем HEAD запрос для проверки без загрузки всего изображения
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.head(url, follow_redirects=True)
                
                # Проверяем статус код и тип контента
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    # Проверяем, что это действительно изображение
                    if any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'gif', 'webp']):
                        self.poster_cache[url] = True
                        return True
                
                logger.warning(f"Изображение недоступно: {url} (статус: {response.status_code})")
                self.poster_cache[url] = False
                return False
                
        except Exception as e:
            logger.warning(f"Ошибка при проверке изображения {url}: {e}")
            self.poster_cache[url] = False
            return False
    
    async def search_anime(self, query: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Основной поиск аниме"""
        try:
            # 1. Ищем в Shikimori (основной поиск)
            logger.info(f"Поиск в Shikimori: query='{query}', filters={filters}")
            shikimori_results = await self.shikimori.search_anime(query, filters)
            
            if not shikimori_results:
                logger.warning("Shikimori не вернул результатов")
                return []
            
            # 2. Фильтрация на стороне клиента для исключения дорам
            anime_results = []
            for anime in shikimori_results:
                anime_kind = anime.get('kind', '')
                # Исключаем дорамы, но оставляем все виды аниме
                if anime_kind in ['tv', 'movie', 'ova', 'ona', 'special', 'music']:
                    anime_results.append(anime)
                else:
                    logger.debug(f"Исключаем не-аниме: {anime.get('name')} [{anime_kind}]")
            
            # 3. Фильтрация по диапазону годов на стороне клиента (если нужно)
            if filters and filters.get('year_from') and filters.get('year_to'):
                year_from = int(filters['year_from'])
                year_to = int(filters['year_to'])
                
                if year_from != year_to:
                    year_filtered_results = []
                    for anime in anime_results:
                        anime_year = extract_year_from_date(anime.get('aired_on'))
                        if anime_year and year_from <= anime_year <= year_to:
                            year_filtered_results.append(anime)
                    anime_results = year_filtered_results
                    logger.info(f"После фильтрации по годам {year_from}-{year_to}: {len(anime_results)} аниме")
            
            # 4. Обогащаем данными из Kodik (плееры) - только первые 20 для производительности
            enriched_results = []
            for anime in anime_results[:20]:
                enriched_anime = await self._enrich_with_kodik(anime)
                enriched_results.append(enriched_anime)
                
            logger.info(f"Найдено {len(enriched_results)} аниме (исключены дорамы)")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске аниме: {e}")
            return []
    
    async def get_seasonal_anime(self, season: Optional[str] = None, 
                                year: Optional[int] = None, limit: int = 20) -> List[Dict]:
        """Получение аниме текущего/указанного сезона"""
        try:
            logger.info(f"Получение сезонных аниме: {season}_{year} (лимит: {limit})")
            shikimori_results = await self.shikimori.get_seasonal_anime(season, year, limit)
            
            if not shikimori_results:
                logger.warning("Shikimori не вернул сезонных аниме")
                # Fallback: получаем просто популярные аниме
                logger.info("Используем fallback: популярные аниме")
                return await self.get_popular_anime(limit)
            
            # Обогащаем данными из Kodik
            enriched_results = []
            for anime in shikimori_results:
                enriched_anime = await self._enrich_with_kodik(anime)
                enriched_results.append(enriched_anime)
                
            logger.info(f"Найдено {len(enriched_results)} сезонных аниме")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Ошибка при получении сезонных аниме: {e}")
            # В случае ошибки возвращаем популярные аниме
            logger.info("Ошибка, используем fallback: популярные аниме")
            return await self.get_popular_anime(limit)
    
    async def get_popular_anime(self, limit: int = 20) -> List[Dict]:
        """Получение популярных аниме"""
        try:
            logger.info(f"Получение {limit} популярных аниме")
            shikimori_results = await self.shikimori.get_popular_anime(limit)
            
            if not shikimori_results:
                logger.warning("Не удалось получить популярные аниме")
                return []
            
            enriched_results = []
            for anime in shikimori_results:
                enriched_anime = await self._enrich_with_kodik(anime)
                enriched_results.append(enriched_anime)
                
            logger.info(f"Найдено {len(enriched_results)} популярных аниме")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Ошибка при получении популярных аниме: {e}")
            return []
    
    async def get_anime_details(self, anime_id: str, shikimori_id: Optional[str] = None) -> Optional[Dict]:
        """Получение детальной информации об аниме"""
        try:
            # Если есть shikimori_id, используем его для получения полной информации
            if shikimori_id:
                logger.info(f"Получение деталей аниме из Shikimori: {shikimori_id}")
                shikimori_anime = await self.shikimori.get_anime(shikimori_id)
                if shikimori_anime:
                    enriched = await self._enrich_with_kodik(shikimori_anime)
                    return enriched
            
            # Если anime_id имеет префикс shiki_, извлекаем shikimori_id
            if anime_id.startswith('shiki_'):
                extracted_shikimori_id = anime_id.replace('shiki_', '')
                logger.info(f"Извлечен Shikimori ID из anime_id: {extracted_shikimori_id}")
                shikimori_anime = await self.shikimori.get_anime(extracted_shikimori_id)
                if shikimori_anime:
                    enriched = await self._enrich_with_kodik(shikimori_anime)
                    return enriched
            
            # Fallback: поиск в Kodik по ID (если это Kodik ID)
            logger.info(f"Fallback поиск в Kodik: {anime_id}")
            kodik_results = await self.kodik.search_by_title("")  # Получаем любые результаты
            if kodik_results and kodik_results.get('results'):
                for anime in kodik_results['results']:
                    if anime.get('id') == anime_id:
                        # Конвертируем формат Kodik в наш
                        return self._convert_kodik_only_format(anime)
                        
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении деталей аниме: {e}")
            return None
    
    async def get_anime_episodes(self, anime_id: str, kodik_id: Optional[str] = None) -> List[Dict]:
        """Получение списка эпизодов аниме"""
        try:
            # Определяем Kodik ID
            target_kodik_id = kodik_id
            
            if not target_kodik_id:
                # Пытаемся найти через Shikimori ID
                if anime_id.startswith('shiki_'):
                    shikimori_id = anime_id.replace('shiki_', '')
                    kodik_data = await self.kodik.search_by_shikimori_id(shikimori_id)
                    if kodik_data and kodik_data.get('results'):
                        target_kodik_id = kodik_data['results'][0].get('id')
                else:
                    target_kodik_id = anime_id
            
            if target_kodik_id:
                episodes = await self.kodik.get_anime_episodes(target_kodik_id)
                return episodes
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения эпизодов: {e}")
            return []
    
    async def get_video_link(self, anime_id: str, season: int = 1, episode: int = 1, 
                           kodik_id: Optional[str] = None) -> Optional[str]:
        """Получение ссылки на видео"""
        try:
            # Определяем Kodik ID
            target_kodik_id = kodik_id
            
            if not target_kodik_id:
                # Пытаемся найти через Shikimori ID
                if anime_id.startswith('shiki_'):
                    shikimori_id = anime_id.replace('shiki_', '')
                    kodik_data = await self.kodik.search_by_shikimori_id(shikimori_id)
                    if kodik_data and kodik_data.get('results'):
                        target_kodik_id = kodik_data['results'][0].get('id')
                else:
                    target_kodik_id = anime_id
            
            if target_kodik_id:
                link = await self.kodik.get_video_link(target_kodik_id, season, episode)
                return link
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения ссылки на видео: {e}")
            return None
    
    async def _enrich_with_kodik(self, shikimori_anime: Dict) -> Dict:
        """Обогащение аниме из Shikimori данными из Kodik"""
        try:
            # Проверяем кеш объединенных данных
            cache_key = f"merge_{shikimori_anime['id']}"
            if CACHE_CONFIG["enabled"] and cache_key in self.merge_cache:
                cached_data, timestamp = self.merge_cache[cache_key]
                if time.time() - timestamp < 300:  # 5 минут кеш для объединенных данных
                    return cached_data
            
            # Ищем в Kodik по shikimori_id
            kodik_results = await self.kodik.search_by_shikimori_id(str(shikimori_anime['id']))
            
            # Если не нашли по ID, пробуем по названию
            if not kodik_results or not kodik_results.get('results'):
                title = shikimori_anime.get('russian') or shikimori_anime.get('name', '')
                if title:
                    kodik_results = await self.kodik.search_by_title(title)
            
            # Объединяем данные
            enriched = await self._merge_anime_data(shikimori_anime, kodik_results)
            
            # Кешируем результат
            if CACHE_CONFIG["enabled"]:
                self.merge_cache[cache_key] = (enriched, time.time())
            
            return enriched
            
        except Exception as e:
            logger.error(f"Ошибка при обогащении аниме {shikimori_anime.get('id')}: {e}")
            # Возвращаем только данные Shikimori
            return convert_shikimori_format(shikimori_anime)
    
    async def _merge_anime_data(self, shikimori_anime: Dict, kodik_results: Optional[Dict]) -> Dict:
        """Объединение данных из Shikimori и Kodik"""
        # Начинаем с данных Shikimori
        merged = convert_shikimori_format(shikimori_anime)
        
        # Добавляем данные Kodik если есть
        if kodik_results and kodik_results.get('results'):
            kodik_anime = kodik_results['results'][0]  # Берем первый результат
            
            # Извлекаем данные Kodik
            kodik_data = extract_kodik_data(kodik_results)
            
            # Добавляем важные поля из Kodik
            merged.update({
                'kodik_id': kodik_data.get('kodik_id'),
                'link': kodik_data.get('link'),
                'translation': kodik_data.get('translation'),
                'quality': kodik_data.get('quality'),
                'episodes_count': kodik_data.get('episodes_count') or merged.get('episodes_count'),
                'seasons': kodik_data.get('seasons'),
                'screenshots': kodik_data.get('screenshots', [])
            })
            
            # *** ИСПРАВЛЕНИЕ: Улучшенная проверка постеров ***
            shikimori_poster = merged.get('material_data', {}).get('poster_url', '')
            kodik_material = kodik_anime.get('material_data', {})
            kodik_poster = kodik_material.get('poster_url', '')
            
            # Проверяем, нужно ли заменить постер Shikimori на Kodik
            should_replace_poster = (
                # Если постер - placeholder
                shikimori_poster.startswith('https://via.placeholder.com') or
                # Если в URL есть "404" (индикатор недоступности)
                '404' in shikimori_poster.lower() or
                # Если постер пустой
                not shikimori_poster or
                # Если URL содержит типичные индикаторы ошибок
                any(error_indicator in shikimori_poster.lower() 
                    for error_indicator in ['not_found', 'notfound', 'error', 'missing', 'no+image'])
            )
            
            if should_replace_poster and kodik_poster:
                logger.info(f"Заменяем проблемный постер Shikimori на Kodik для аниме {shikimori_anime.get('id')}")
                logger.debug(f"Старый URL: {shikimori_poster}")
                logger.debug(f"Новый URL: {kodik_poster}")
                
                merged['material_data']['poster_url'] = kodik_poster
                merged['material_data']['anime_poster_url'] = kodik_poster
            
            # Если постер выглядит нормально, но все же может быть недоступен, проверяем доступность
            elif shikimori_poster and not shikimori_poster.startswith('https://via.placeholder.com'):
                if not await self._check_image_availability(shikimori_poster):
                    if kodik_poster and await self._check_image_availability(kodik_poster):
                        logger.info(f"HTTP проверка: заменяем недоступный постер Shikimori на Kodik для аниме {shikimori_anime.get('id')}")
                        merged['material_data']['poster_url'] = kodik_poster
                        merged['material_data']['anime_poster_url'] = kodik_poster
                    else:
                        logger.warning(f"Постер Shikimori недоступен, Kodik также не подходит: {shikimori_anime.get('id')}")
                        merged['material_data']['poster_url'] = 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера'
                        merged['material_data']['anime_poster_url'] = 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера'
        
        return merged
    
    def _convert_kodik_only_format(self, kodik_anime: Dict) -> Dict:
        """Конвертация данных только из Kodik в наш формат"""
        material_data = kodik_anime.get('material_data', {})
        
        return {
            'id': f"kodik_{kodik_anime.get('id')}",
            'kodik_id': kodik_anime.get('id'),
            'shikimori_id': material_data.get('shikimori_id'),
            'title': material_data.get('title', 'Неизвестно'),
            'title_orig': material_data.get('title_en', ''),
            'other_title': [],
            'year': material_data.get('year'),
            'type': 'anime',
            'link': kodik_anime.get('link'),
            'translation': kodik_anime.get('translation', {}).get('title', ''),
            'quality': kodik_anime.get('quality'),
            'episodes_count': kodik_anime.get('episodes_count'),
            'last_episode': kodik_anime.get('last_episode'),
            'seasons': kodik_anime.get('seasons'),
            'screenshots': kodik_anime.get('screenshots', []),
            
            'material_data': {
                'title': material_data.get('title', 'Неизвестно'),
                'title_en': material_data.get('title_en', ''),
                'anime_title': material_data.get('anime_title', material_data.get('title', '')),
                'description': material_data.get('description', ''),
                'anime_description': material_data.get('anime_description', ''),
                'poster_url': material_data.get('poster_url', 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера'),
                'anime_poster_url': material_data.get('anime_poster_url', material_data.get('poster_url', '')),
                'shikimori_rating': material_data.get('shikimori_rating'),
                'shikimori_votes': material_data.get('shikimori_votes'),
                'anime_kind': material_data.get('anime_kind'),
                'anime_status': material_data.get('anime_status'),
                'all_status': material_data.get('all_status'),
                'anime_genres': material_data.get('anime_genres', []),
                'all_genres': material_data.get('all_genres', []),
                'episodes_total': material_data.get('episodes_total'),
                'episodes_aired': material_data.get('episodes_aired'),
                'anime_studios': material_data.get('anime_studios', []),
                'rating_mpaa': material_data.get('rating_mpaa'),
                'aired_at': material_data.get('aired_at'),
                'released_at': material_data.get('released_at'),
                'year': material_data.get('year')
            }
        }
    
    async def get_alternative_poster(self, anime_id: str, shikimori_id: Optional[str] = None) -> Dict:
        """Получение альтернативного постера от Kodik для аниме"""
        try:
            # Извлекаем shikimori_id если anime_id имеет префикс
            target_shikimori_id = shikimori_id
            if not target_shikimori_id and anime_id.startswith('shiki_'):
                target_shikimori_id = anime_id.replace('shiki_', '')
            
            # Ищем в Kodik
            kodik_results = None
            if target_shikimori_id:
                kodik_results = await self.kodik.search_by_shikimori_id(target_shikimori_id)
            
            # Если не нашли по ID, пробуем поиск по названию
            if not kodik_results or not kodik_results.get('results'):
                # Получаем информацию об аниме из Shikimori для поиска по названию
                if target_shikimori_id:
                    shikimori_anime = await self.shikimori.get_anime(target_shikimori_id)
                    if shikimori_anime:
                        title = shikimori_anime.get('russian') or shikimori_anime.get('name', '')
                        if title:
                            kodik_results = await self.kodik.search_by_title(title)
            
            # Проверяем результаты
            if kodik_results and kodik_results.get('results'):
                kodik_anime = kodik_results['results'][0]
                kodik_material = kodik_anime.get('material_data', {})
                kodik_poster = kodik_material.get('poster_url')
                
                if kodik_poster:
                    # Проверяем доступность постера от Kodik
                    if await self._check_image_availability(kodik_poster):
                        return {
                            'success': True,
                            'poster_url': kodik_poster,
                            'source': 'kodik'
                        }
            
            # Если не нашли постер от Kodik, возвращаем placeholder
            return {
                'success': True,
                'poster_url': 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера',
                'source': 'placeholder'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении альтернативного постера для {anime_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_poster_stats(self, sample_size: int = 20) -> Dict:
        """Статистика по постерам (для отладки)"""
        try:
            # Получаем небольшую выборку аниме для анализа
            sample_anime = await self.get_popular_anime(sample_size)
            
            stats = {
                'total_checked': 0,
                'shikimori_ok': 0,
                'shikimori_failed': 0,
                'kodik_available': 0,
                'placeholder_used': 0,
                'problems_detected': []
            }
            
            for anime in sample_anime:
                stats['total_checked'] += 1
                poster_url = anime.get('material_data', {}).get('poster_url', '')
                
                if poster_url.startswith('https://via.placeholder.com'):
                    stats['placeholder_used'] += 1
                elif '404' in poster_url.lower() or any(error in poster_url.lower() for error in ['not_found', 'notfound', 'error', 'missing']):
                    stats['shikimori_failed'] += 1
                    stats['problems_detected'].append({
                        'anime': anime.get('title', 'Unknown'),
                        'url': poster_url,
                        'issue': '404 or error indicator in URL'
                    })
                elif poster_url and await self._check_image_availability(poster_url):
                    stats['shikimori_ok'] += 1
                else:
                    stats['shikimori_failed'] += 1
                    stats['problems_detected'].append({
                        'anime': anime.get('title', 'Unknown'),
                        'url': poster_url,
                        'issue': 'HTTP check failed'
                    })
                    
                    # Проверяем наличие альтернативы от Kodik
                    if anime.get('kodik_id'):
                        stats['kodik_available'] += 1
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики постеров: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close(self):
        """Закрытие всех HTTP клиентов"""
        await self.shikimori.close()
        await self.kodik.close()
    
    def clear_cache(self):
        """Очистка всех кешей"""
        self.shikimori.clear_cache()
        self.kodik.clear_cache()
        self.poster_cache.clear()
        self.merge_cache.clear()
        logger.info("Все кеши очищены")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Общая статистика сервиса"""
        return {
            'shikimori': self.shikimori.get_cache_stats(),
            'kodik': self.kodik.get_cache_stats(),
            'poster_cache_size': len(self.poster_cache),
            'merge_cache_size': len(self.merge_cache)
        }

# ===== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР =====

# Создаем глобальный экземпляр сервиса
anime_service = HybridAnimeService()

# ===== ЭКСПОРТ =====

__all__ = [
    "HybridAnimeService", "anime_service"
]