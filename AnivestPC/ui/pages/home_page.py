"""
🏠 ANIVEST DESKTOP - ГЛАВНАЯ СТРАНИЦА
===================================
Домашняя страница с популярными и сезонными аниме
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from config.theme import colors, icons, spacing, typography
from config.settings import APP_NAME, APP_VERSION
from core.api.anime_service import anime_service
from core.api.shikimori_api import get_current_season, get_season_name_ru, get_season_emoji

from ..components.anime_card import LargeAnimeCard, AnimeCard

logger = logging.getLogger(__name__)

class HomePage(ft.UserControl):
    """Главная страница приложения"""
    
    def __init__(
        self,
        on_anime_click: Optional[Callable[[Dict], None]] = None,
        on_favorite_click: Optional[Callable[[Dict, bool], None]] = None,
        on_navigate: Optional[Callable[[str], None]] = None,
        current_user: Optional[Dict] = None
    ):
        super().__init__()
        
        self.on_anime_click = on_anime_click
        self.on_favorite_click = on_favorite_click
        self.on_navigate = on_navigate
        self.current_user = current_user
        
        # Данные
        self.popular_anime = []
        self.seasonal_anime = []
        self.watch_history = []
        self.user_favorites = []
        
        # Состояние
        self.is_loading = False
        self.error_message = ""
        
        # UI элементы
        self.loading_indicator = None
        self.error_container = None
        self.content_container = None
        
        # Информация о сезоне
        self.current_season, self.current_year = get_current_season()
        self.season_name_ru = get_season_name_ru(self.current_season)
        self.season_emoji = get_season_emoji(self.current_season)
    
    async def load_data(self):
        """Загрузка данных для главной страницы"""
        try:
            await self._show_loading()
            
            # Загружаем популярные аниме
            logger.info("Загрузка популярных аниме для главной страницы...")
            self.popular_anime = await anime_service.get_popular_anime(24)
            
            # Загружаем сезонные аниме
            logger.info(f"Загрузка аниме {self.season_name_ru} сезона {self.current_year}...")
            self.seasonal_anime = await anime_service.get_seasonal_anime(
                self.current_season, 
                self.current_year, 
                12
            )
            
            # Загружаем данные пользователя если авторизован
            if self.current_user:
                await self._load_user_data()
            
            await self._hide_loading()
            
            # Обновляем UI
            if self.page:
                self.update()
            
            logger.info(f"Данные главной страницы загружены: {len(self.popular_anime)} популярных, {len(self.seasonal_anime)} сезонных")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных главной страницы: {e}")
            self.error_message = f"Ошибка загрузки: {str(e)}"
            await self._hide_loading()
            
            if self.page:
                self.update()
    
    async def _load_user_data(self):
        """Загрузка данных пользователя"""
        try:
            if not self.current_user:
                return
            
            from core.database.database import db_manager
            
            user_id = self.current_user['id']
            
            # Загружаем избранное
            self.user_favorites = db_manager.get_user_favorites(user_id)
            
            # Загружаем историю просмотра (последние 6 для главной)
            self.watch_history = db_manager.get_user_watch_history(user_id, limit=6)
            
            logger.info(f"Загружены данные пользователя: {len(self.user_favorites)} избранных, {len(self.watch_history)} в истории")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных пользователя: {e}")
    
    def _create_welcome_header(self) -> ft.Container:
        """Создание приветственного заголовка"""
        welcome_text = f"Добро пожаловать в {APP_NAME}!"
        
        if self.current_user:
            welcome_text = f"Добро пожаловать, {self.current_user.get('username', 'Пользователь')}!"
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        welcome_text,
                        size=typography.text_4xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Смотрите аниме в лучшем качестве с удобным десктопным интерфейсом",
                        size=typography.text_xl,
                        color=colors.text_secondary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    
                    # Быстрые действия
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(icons.search, size=spacing.icon_md),
                                            ft.Text("Поиск аниме", size=typography.text_md),
                                        ],
                                        spacing=spacing.sm,
                                        tight=True,
                                    ),
                                    bgcolor=colors.primary,
                                    color=colors.text_primary,
                                    on_click=lambda e: self.on_navigate("catalog") if self.on_navigate else None,
                                    style=ft.ButtonStyle(
                                        padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
                                    ),
                                ),
                                
                                ft.ElevatedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(icons.trending_up, size=spacing.icon_md),
                                            ft.Text("Популярное", size=typography.text_md),
                                        ],
                                        spacing=spacing.sm,
                                        tight=True,
                                    ),
                                    bgcolor=colors.secondary,
                                    color=colors.text_primary,
                                    on_click=lambda e: self._scroll_to_popular(),
                                    style=ft.ButtonStyle(
                                        padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
                                    ),
                                ),
                                
                                ft.ElevatedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Text(self.season_emoji, size=spacing.icon_md),
                                            ft.Text(f"{self.season_name_ru.title()} {self.current_year}", size=typography.text_md),
                                        ],
                                        spacing=spacing.sm,
                                        tight=True,
                                    ),
                                    bgcolor=colors.accent,
                                    color=colors.text_primary,
                                    on_click=lambda e: self._scroll_to_seasonal(),
                                    style=ft.ButtonStyle(
                                        padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
                                    ),
                                ),
                            ],
                            spacing=spacing.md,
                            alignment=ft.MainAxisAlignment.CENTER,
                            wrap=True,
                        ),
                        margin=ft.margin.only(top=spacing.xl),
                    )
                ],
                spacing=spacing.md,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            margin=ft.margin.only(bottom=spacing.xxl),
            padding=spacing.xl,
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(0, 8)
            ),
        )
    
    def _create_anime_section(
        self, 
        title: str, 
        anime_list: List[Dict], 
        show_more_action: Optional[str] = None,
        description: Optional[str] = None
    ) -> ft.Container:
        """Создание секции с аниме"""
        
        if not anime_list:
            return ft.Container()
        
        # Заголовок секции
        header_controls = [
            ft.Column(
                controls=[
                    ft.Text(
                        title,
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        description,
                        size=typography.text_md,
                        color=colors.text_secondary,
                    ) if description else ft.Container(),
                ],
                spacing=spacing.xs,
                expand=True,
            )
        ]
        
        if show_more_action:
            header_controls.append(
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Text("Смотреть все", size=typography.text_sm),
                            ft.Icon(icons.trending_up, size=spacing.icon_sm),
                        ],
                        spacing=spacing.xs,
                        tight=True,
                    ),
                    bgcolor=colors.surface_light,
                    color=colors.text_primary,
                    on_click=lambda e: self.on_navigate(show_more_action) if self.on_navigate else None,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                    ),
                )
            )
        
        header = ft.Row(
            controls=header_controls,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        
        # Горизонтальный список карточек
        cards = []
        display_count = min(len(anime_list), 8)  # Показываем максимум 8 карточек
        
        for anime in anime_list[:display_count]:
            card = LargeAnimeCard(
                anime_data=anime,
                on_click=self.on_anime_click,
                on_favorite=self.on_favorite_click,
                current_user=self.current_user
            )
            cards.append(card)
        
        # Контейнер с горизонтальным скроллом
        cards_container = ft.Container(
            content=ft.Row(
                controls=cards,
                spacing=spacing.xl,
                scroll=ft.ScrollMode.AUTO,
            ),
            margin=ft.margin.only(top=spacing.lg),
            height=400,  # Фиксированная высота для лучшего отображения
        )
        
        # Статистика секции
        stats_text = f"Показано {display_count} из {len(anime_list)} аниме"
        if len(anime_list) > display_count:
            stats_text += f" • Еще {len(anime_list) - display_count} доступно в каталоге"
        
        stats = ft.Container(
            content=ft.Text(
                stats_text,
                size=typography.text_sm,
                color=colors.text_muted,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.alignment.center,
            margin=ft.margin.only(top=spacing.md),
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[header, cards_container, stats],
                spacing=0,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            margin=ft.margin.symmetric(vertical=spacing.lg),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(0, 8)
            ),
        )
    
    def _create_watch_history_section(self) -> ft.Container:
        """Создание секции истории просмотра"""
        
        if not self.current_user or not self.watch_history:
            return ft.Container()
        
        # Конвертируем историю в формат аниме
        history_anime = []
        for history_item in self.watch_history:
            anime_data = {
                'id': history_item.anime_id,
                'title': history_item.anime_title,
                'material_data': {
                    'title': history_item.anime_title,
                    'poster_url': history_item.anime_poster_url or 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера',
                },
                'watch_progress': history_item.get_progress_percent(),
                'current_episode': history_item.episode_number,
                'last_watched': history_item.last_watched,
            }
            history_anime.append(anime_data)
        
        return self._create_anime_section(
            title="📖 Продолжить просмотр",
            anime_list=history_anime,
            show_more_action="my_list",
            description="Недавно просмотренные аниме"
        )
    
    def _create_favorites_section(self) -> ft.Container:
        """Создание секции избранного"""
        
        if not self.current_user or not self.user_favorites:
            return ft.Container()
        
        # Конвертируем избранное в формат аниме (показываем только первые 6)
        favorites_anime = []
        for favorite in self.user_favorites[:6]:
            anime_data = {
                'id': favorite.anime_id,
                'title': favorite.anime_title,
                'material_data': {
                    'title': favorite.anime_title,
                    'poster_url': favorite.anime_poster_url or 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера',
                }
            }
            favorites_anime.append(anime_data)
        
        return self._create_anime_section(
            title="⭐ Избранное",
            anime_list=favorites_anime,
            show_more_action="favorites",
            description="Ваши любимые аниме"
        )
    
    def _create_quick_stats(self) -> ft.Container:
        """Создание секции быстрой статистики"""
        
        if not self.current_user:
            return ft.Container()
        
        # Статистика
        stats = [
            {
                "title": "Избранное",
                "value": len(self.user_favorites),
                "icon": icons.favorite,
                "color": colors.secondary,
                "action": "favorites"
            },
            {
                "title": "В процессе",
                "value": len([h for h in self.watch_history if not h.is_completed]),
                "icon": icons.play_circle,
                "color": colors.primary,
                "action": "my_list"
            },
            {
                "title": "Завершено",
                "value": len([h for h in self.watch_history if h.is_completed]),
                "icon": icons.check_circle,
                "color": colors.success,
                "action": "stats"
            },
        ]
        
        stat_cards = []
        for stat in stats:
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            stat["icon"],
                            size=32,
                            color=stat["color"],
                        ),
                        ft.Text(
                            str(stat["value"]),
                            size=typography.text_3xl,
                            weight=typography.weight_bold,
                            color=colors.text_primary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            stat["title"],
                            size=typography.text_md,
                            color=colors.text_secondary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=spacing.sm,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                width=150,
                height=120,
                bgcolor=colors.card,
                border_radius=spacing.border_radius_lg,
                padding=spacing.md,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=colors.shadow,
                    offset=ft.Offset(0, 4)
                ),
                on_click=lambda e, action=stat["action"]: self.on_navigate(action) if self.on_navigate else None,
                ink=True,
            )
            stat_cards.append(card)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "📊 Ваша статистика",
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=stat_cards,
                            spacing=spacing.xl,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        margin=ft.margin.only(top=spacing.lg),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            margin=ft.margin.symmetric(vertical=spacing.lg),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(0, 8)
            ),
        )
    
    def _create_loading_indicator(self) -> ft.Container:
        """Создание индикатора загрузки"""
        self.loading_indicator = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=48,
                        height=48,
                        color=colors.primary,
                    ),
                    ft.Text(
                        "Загрузка популярных аниме...",
                        size=typography.text_lg,
                        color=colors.text_secondary,
                        text_align=ft.TextAlign.CENTER,
                    )
                ],
                spacing=spacing.lg,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            height=400,
            visible=self.is_loading,
        )
        
        return self.loading_indicator
    
    def _create_error_container(self) -> ft.Container:
        """Создание контейнера ошибки"""
        self.error_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icons.error,
                        size=64,
                        color=colors.error,
                    ),
                    ft.Text(
                        "Ошибка загрузки данных",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        self.error_message,
                        size=typography.text_md,
                        color=colors.text_secondary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.ElevatedButton(
                        text="Попробовать снова",
                        bgcolor=colors.primary,
                        color=colors.text_primary,
                        on_click=lambda e: asyncio.create_task(self.load_data()),
                    ),
                ],
                spacing=spacing.lg,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            height=400,
            visible=bool(self.error_message),
        )
        
        return self.error_container
    
    async def _show_loading(self):
        """Показать индикатор загрузки"""
        self.is_loading = True
        self.error_message = ""
        
        if self.loading_indicator:
            self.loading_indicator.visible = True
        
        if self.error_container:
            self.error_container.visible = False
        
        if self.content_container:
            self.content_container.visible = False
        
        if self.page:
            self.update()
    
    async def _hide_loading(self):
        """Скрыть индикатор загрузки"""
        self.is_loading = False
        
        if self.loading_indicator:
            self.loading_indicator.visible = False
        
        if self.content_container:
            self.content_container.visible = True
        
        if self.page:
            self.update()
    
    def _scroll_to_popular(self):
        """Скролл к секции популярных аниме"""
        # В будущем можно реализовать плавный скролл
        logger.info("Скролл к популярным аниме")
    
    def _scroll_to_seasonal(self):
        """Скролл к секции сезонных аниме"""
        # В будущем можно реализовать плавный скролл  
        logger.info("Скролл к сезонным аниме")
    
    def update_user(self, user: Optional[Dict]):
        """Обновление информации о пользователе"""
        self.current_user = user
        
        # Перезагружаем данные пользователя
        if user:
            asyncio.create_task(self._load_user_data())
        else:
            self.user_favorites = []
            self.watch_history = []
        
        if self.page:
            self.update()
    
    def refresh_data(self):
        """Обновление данных страницы"""
        asyncio.create_task(self.load_data())
    
    def build(self):
        """Построение UI главной страницы"""
        
        # Основной контент
        content_sections = [
            self._create_welcome_header(),
        ]
        
        # Персональные секции (если пользователь авторизован)
        if self.current_user:
            quick_stats = self._create_quick_stats()
            if quick_stats.content:  # Проверяем что секция не пустая
                content_sections.append(quick_stats)
            
            watch_history = self._create_watch_history_section()
            if watch_history.content:
                content_sections.append(watch_history)
            
            favorites = self._create_favorites_section()
            if favorites.content:
                content_sections.append(favorites)
        
        # Общие секции
        if self.popular_anime:
            popular_section = self._create_anime_section(
                title="🔥 Популярные аниме",
                anime_list=self.popular_anime,
                show_more_action="catalog",
                description="Самые популярные аниме всех времен"
            )
            content_sections.append(popular_section)
        
        if self.seasonal_anime:
            seasonal_section = self._create_anime_section(
                title=f"{self.season_emoji} Аниме {self.season_name_ru} сезона {self.current_year}",
                anime_list=self.seasonal_anime,
                show_more_action="catalog",
                description="Новинки текущего сезона"
            )
            content_sections.append(seasonal_section)
        
        # Контейнер контента
        self.content_container = ft.Container(
            content=ft.Column(
                controls=content_sections,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            visible=not self.is_loading and not self.error_message,
            expand=True,
        )
        
        # Главный контейнер страницы
        return ft.Container(
            content=ft.Stack(
                controls=[
                    self.content_container,
                    self._create_loading_indicator(),
                    self._create_error_container(),
                ],
                expand=True,
            ),
            padding=spacing.xxl,
            expand=True,
        )

# ===== ЭКСПОРТ =====

__all__ = ["HomePage"]