"""
🚀 ANIVEST DESKTOP - ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
===========================================
Основной класс приложения с навигацией и управлением состоянием
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Optional, List

from config.theme import colors, icons, spacing, typography, create_anivest_theme
from config.settings import APP_NAME, APP_VERSION, WINDOW_CONFIG, USER_SETTINGS, HOTKEYS
from core.database.database import db_manager
from core.api.anime_service import anime_service

# Импорт компонентов
from .components.anime_card import AnimeCard, LargeAnimeCard, CompactAnimeCard
from .components.sidebar import AnivesetSidebar
from .components.search_bar import AnivesetSearchBar

logger = logging.getLogger(__name__)

class AnivesetApp:
    """Главный класс приложения Anivest Desktop"""
    
    def __init__(self):
        # Состояние приложения
        self.current_page = "home"
        self.current_user = None
        self.is_loading = False
        self.search_query = ""
        self.search_filters = {}
        
        # Данные
        self.popular_anime = []
        self.seasonal_anime = []
        self.search_results = []
        self.user_favorites = []
        self.watch_history = []
        
        # UI элементы
        self.page = None
        self.sidebar = None
        self.main_content = None
        self.search_bar = None
        self.loading_overlay = None
        
        # Кеш страниц для быстрого переключения
        self.page_cache = {}
        
    async def main(self, page: ft.Page):
        """Главная функция приложения"""
        self.page = page
        
        # Настройка окна
        await self._setup_window()
        
        # Настройка темы
        await self._setup_theme()
        
        # Инициализация данных
        await self._initialize_data()
        
        # Создание UI
        await self._create_ui()
        
        # Настройка горячих клавиш
        await self._setup_hotkeys()
        
        logger.info(f"Приложение {APP_NAME} v{APP_VERSION} запущено")
    
    async def _setup_window(self):
        """Настройка окна приложения"""
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = colors.background
        self.page.padding = 0
        self.page.spacing = 0
        
        # Размеры окна
        try:
            # Новый API
            self.page.window.width = WINDOW_CONFIG["default_width"]
            self.page.window.height = WINDOW_CONFIG["default_height"]
            self.page.window.min_width = WINDOW_CONFIG["min_width"]
            self.page.window.min_height = WINDOW_CONFIG["min_height"]
            self.page.window.max_width = WINDOW_CONFIG["max_width"]
            self.page.window.max_height = WINDOW_CONFIG["max_height"]
            self.page.window.resizable = WINDOW_CONFIG["resizable"]
        except AttributeError:
            try:
                # Старый API
                self.page.window_width = WINDOW_CONFIG["default_width"]
                self.page.window_height = WINDOW_CONFIG["default_height"]
                self.page.window_min_width = WINDOW_CONFIG["min_width"]
                self.page.window_min_height = WINDOW_CONFIG["min_height"]
                self.page.window_max_width = WINDOW_CONFIG["max_width"]
                self.page.window_max_height = WINDOW_CONFIG["max_height"]
                self.page.window_resizable = WINDOW_CONFIG["resizable"]
            except:
                logger.warning("Не удалось настроить размеры окна")
    
    async def _setup_theme(self):
        """Настройка темы"""
        try:
            self.page.theme = create_anivest_theme()
        except Exception as e:
            logger.warning(f"Не удалось установить кастомную тему: {e}")
    
    async def _initialize_data(self):
        """Инициализация данных приложения"""
        try:
            await self._show_loading("Загрузка данных...")
            
            # Загружаем популярные аниме
            logger.info("Загрузка популярных аниме...")
            self.popular_anime = await anime_service.get_popular_anime(24)
            
            # Загружаем сезонные аниме
            logger.info("Загрузка сезонных аниме...")
            self.seasonal_anime = await anime_service.get_seasonal_anime(limit=12)
            
            # Загружаем данные пользователя (если авторизован)
            if self.current_user:
                await self._load_user_data()
            
            await self._hide_loading()
            
            logger.info(f"Данные загружены: {len(self.popular_anime)} популярных, {len(self.seasonal_anime)} сезонных")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации данных: {e}")
            await self._hide_loading()
            await self._show_error("Ошибка загрузки данных", str(e))
    
    async def _load_user_data(self):
        """Загрузка данных пользователя"""
        try:
            if not self.current_user:
                return
            
            user_id = self.current_user['id']
            
            # Загружаем избранное
            self.user_favorites = db_manager.get_user_favorites(user_id)
            
            # Загружаем историю просмотра
            self.watch_history = db_manager.get_user_watch_history(user_id, limit=20)
            
            logger.info(f"Загружены данные пользователя: {len(self.user_favorites)} избранных, {len(self.watch_history)} в истории")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных пользователя: {e}")
    
    async def _create_ui(self):
        """Создание пользовательского интерфейса"""
        
        # Сайдбар
        self.sidebar = AnivesetSidebar(
            current_page=self.current_page,
            on_navigate=self._on_navigate,
            current_user=self.current_user,
            width=USER_SETTINGS.get("sidebar_width", 180)
        )
        
        # Основной контент
        self.main_content = ft.Container(
            content=await self._create_page_content(),
            expand=True,
            bgcolor=colors.background,
        )
        
        # Overlay для загрузки
        self.loading_overlay = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=48, height=48, color=colors.primary),
                    ft.Text(
                        "Загрузка...",
                        size=typography.text_lg,
                        color=colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    )
                ],
                spacing=spacing.lg,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            bgcolor=colors.background + "CC",  # 80% непрозрачность
            visible=False,
        )
        
        # Главный контейнер
        main_layout = ft.Stack(
            controls=[
                # Основной интерфейс
                ft.Row(
                    controls=[
                        self.sidebar,
                        ft.VerticalDivider(width=2, color=colors.border),
                        self.main_content,
                    ],
                    spacing=0,
                    expand=True,
                ),
                
                # Overlay загрузки
                self.loading_overlay,
            ],
            expand=True,
        )
        
        self.page.add(main_layout)
        await self.page.update_async()
    
    async def _create_page_content(self) -> ft.Container:
        """Создание контента текущей страницы"""
        
        # Проверяем кеш
        if self.current_page in self.page_cache:
            logger.debug(f"Загрузка страницы из кеша: {self.current_page}")
            return self.page_cache[self.current_page]
        
        # Создаем контент в зависимости от страницы
        if self.current_page == "home":
            content = await self._create_home_page()
        elif self.current_page == "catalog":
            content = await self._create_catalog_page()
        elif self.current_page == "favorites":
            content = await self._create_favorites_page()
        elif self.current_page == "my_list":
            content = await self._create_my_list_page()
        elif self.current_page == "downloads":
            content = await self._create_downloads_page()
        elif self.current_page == "stats":
            content = await self._create_stats_page()
        elif self.current_page == "settings":
            content = await self._create_settings_page()
        elif self.current_page == "about":
            content = await self._create_about_page()
        elif self.current_page == "login":
            content = await self._create_login_page()
        else:
            content = await self._create_home_page()
        
        # Кешируем страницу
        self.page_cache[self.current_page] = content
        
        return content
    
    async def _create_home_page(self) -> ft.Container:
        """Создание главной страницы"""
        
        # Заголовок
        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Добро пожаловать в {APP_NAME}!",
                        size=typography.text_4xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        "Смотрите аниме в лучшем качестве с удобным десктопным интерфейсом",
                        size=typography.text_xl,
                        color=colors.text_secondary,
                    ),
                ],
                spacing=spacing.sm,
            ),
            margin=ft.margin.only(bottom=spacing.xxl),
        )
        
        # Секция популярных аниме
        popular_section = await self._create_anime_section(
            title="🔥 Популярные аниме",
            anime_list=self.popular_anime[:8],
            show_more_link=True
        )
        
        # Секция сезонных аниме
        seasonal_section = await self._create_anime_section(
            title="🌟 Новинки сезона",
            anime_list=self.seasonal_anime[:6],
            show_more_link=True
        )
        
        # История просмотра (если пользователь авторизован)
        history_section = ft.Container()
        if self.current_user and self.watch_history:
            history_section = await self._create_history_section()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    popular_section,
                    seasonal_section,
                    history_section,
                ],
                spacing=spacing.xxl,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_catalog_page(self) -> ft.Container:
        """Создание страницы каталога"""
        
        # Поисковая строка
        self.search_bar = AnivesetSearchBar(
            width=600,
            on_search=self._on_search,
            on_filters_change=self._on_filters_change,
            placeholder="Поиск аниме в каталоге..."
        )
        
        # Результаты поиска или популярные аниме
        anime_list = self.search_results if self.search_results else self.popular_anime
        
        # Сетка аниме
        anime_grid = await self._create_anime_grid(anime_list)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Заголовок и поиск
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "📺 Каталог аниме",
                                    size=typography.text_3xl,
                                    weight=typography.weight_bold,
                                    color=colors.text_primary,
                                ),
                                self.search_bar,
                            ],
                            spacing=spacing.lg,
                        ),
                        margin=ft.margin.only(bottom=spacing.xxl),
                    ),
                    
                    # Результаты
                    anime_grid,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_favorites_page(self) -> ft.Container:
        """Создание страницы избранного"""
        
        if not self.current_user:
            return await self._create_auth_required_page("избранного")
        
        # Конвертируем избранное в формат аниме
        favorites_anime = []
        for favorite in self.user_favorites:
            anime_data = {
                'id': favorite.anime_id,
                'title': favorite.anime_title,
                'material_data': {
                    'title': favorite.anime_title,
                    'poster_url': favorite.anime_poster_url or 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера',
                }
            }
            favorites_anime.append(anime_data)
        
        if not favorites_anime:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.favorite, size=96, color=colors.text_muted),
                        ft.Text(
                            "Избранное пусто",
                            size=typography.text_2xl,
                            weight=typography.weight_bold,
                            color=colors.text_muted,
                        ),
                        ft.Text(
                            "Добавляйте аниме в избранное, чтобы они появились здесь",
                            size=typography.text_lg,
                            color=colors.text_muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.ElevatedButton(
                            text="Перейти в каталог",
                            bgcolor=colors.primary,
                            color=colors.text_primary,
                            on_click=lambda e: self._on_navigate("catalog"),
                        )
                    ],
                    spacing=spacing.lg,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"⭐ Избранное ({len(favorites_anime)})",
                        size=typography.text_3xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    await self._create_anime_grid(favorites_anime),
                ],
                spacing=spacing.xxl,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_my_list_page(self) -> ft.Container:
        """Создание страницы 'Мой список'"""
        
        if not self.current_user:
            return await self._create_auth_required_page("списка")
        
        # История просмотра как основа для "моего списка"
        if not self.watch_history:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.list, size=96, color=colors.text_muted),
                        ft.Text(
                            "Список пуст",
                            size=typography.text_2xl,
                            weight=typography.weight_bold,
                            color=colors.text_muted,
                        ),
                        ft.Text(
                            "Начните смотреть аниме, чтобы они появились в вашем списке",
                            size=typography.text_lg,
                            color=colors.text_muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=spacing.lg,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        
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
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"📋 Мой список ({len(history_anime)})",
                        size=typography.text_3xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    await self._create_anime_grid(history_anime),
                ],
                spacing=spacing.xxl,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_downloads_page(self) -> ft.Container:
        """Создание страницы загрузок"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icons.download, size=96, color=colors.text_muted),
                    ft.Text(
                        "Загрузки недоступны",
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_muted,
                    ),
                    ft.Text(
                        "Функция загрузки будет добавлена в будущих версиях",
                        size=typography.text_lg,
                        color=colors.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=spacing.lg,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    async def _create_stats_page(self) -> ft.Container:
        """Создание страницы статистики"""
        
        if not self.current_user:
            return await self._create_auth_required_page("статистики")
        
        # Простая статистика
        stats = {
            "Избранное": len(self.user_favorites),
            "История просмотра": len(self.watch_history),
            "Завершенные аниме": len([h for h in self.watch_history if h.is_completed]),
        }
        
        stats_cards = []
        for stat_name, stat_value in stats.items():
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            str(stat_value),
                            size=typography.text_4xl,
                            weight=typography.weight_bold,
                            color=colors.primary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            stat_name,
                            size=typography.text_lg,
                            color=colors.text_secondary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=spacing.sm,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=200,
                height=120,
                bgcolor=colors.card,
                border_radius=spacing.border_radius_lg,
                padding=spacing.lg,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=colors.shadow,
                    offset=ft.Offset(0, 4)
                ),
            )
            stats_cards.append(card)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "📊 Статистика",
                        size=typography.text_3xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=stats_cards,
                            spacing=spacing.xl,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        margin=ft.margin.symmetric(vertical=spacing.xxl),
                    ),
                ],
                spacing=spacing.xl,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_settings_page(self) -> ft.Container:
        """Создание страницы настроек"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "⚙️ Настройки",
                        size=typography.text_3xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        "Настройки будут добавлены в будущих версиях",
                        size=typography.text_lg,
                        color=colors.text_muted,
                    ),
                ],
                spacing=spacing.lg,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_about_page(self) -> ft.Container:
        """Создание страницы 'О программе'"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"ℹ️ О программе",
                        size=typography.text_3xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        f"{APP_NAME} v{APP_VERSION}",
                        size=typography.text_xl,
                        weight=typography.weight_semibold,
                        color=colors.primary,
                    ),
                    ft.Text(
                        "Десктопное приложение для просмотра аниме",
                        size=typography.text_lg,
                        color=colors.text_secondary,
                    ),
                    ft.Text(
                        "• Интеграция с Shikimori API\n• Видео через Kodik\n• Современный интерфейс\n• Система избранного и истории",
                        size=typography.text_md,
                        color=colors.text_muted,
                    ),
                ],
                spacing=spacing.lg,
            ),
            padding=spacing.xxl,
            expand=True,
        )
    
    async def _create_login_page(self) -> ft.Container:
        """Создание страницы входа"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "🔐 Вход в систему",
                        size=typography.text_3xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        "Функция авторизации будет добавлена в будущих версиях",
                        size=typography.text_lg,
                        color=colors.text_muted,
                    ),
                ],
                spacing=spacing.lg,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    async def _create_auth_required_page(self, feature_name: str) -> ft.Container:
        """Создание страницы для неавторизованных пользователей"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icons.login, size=96, color=colors.text_muted),
                    ft.Text(
                        "Требуется авторизация",
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_muted,
                    ),
                    ft.Text(
                        f"Войдите в систему для доступа к {feature_name}",
                        size=typography.text_lg,
                        color=colors.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.ElevatedButton(
                        text="Войти",
                        bgcolor=colors.primary,
                        color=colors.text_primary,
                        on_click=lambda e: self._on_navigate("login"),
                    )
                ],
                spacing=spacing.lg,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    async def _create_anime_section(self, title: str, anime_list: List[Dict], show_more_link: bool = False) -> ft.Container:
        """Создание секции с аниме"""
        
        if not anime_list:
            return ft.Container()
        
        # Заголовок секции
        header_controls = [
            ft.Text(
                title,
                size=typography.text_2xl,
                weight=typography.weight_bold,
                color=colors.text_primary,
            )
        ]
        
        if show_more_link:
            header_controls.append(
                ft.TextButton(
                    text="Смотреть все →",
                    on_click=lambda e: self._on_navigate("catalog"),
                    style=ft.ButtonStyle(color=colors.primary),
                )
            )
        
        header = ft.Row(
            controls=header_controls,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # Горизонтальный список карточек
        cards = []
        for anime in anime_list:
            card = LargeAnimeCard(
                anime_data=anime,
                on_click=self._on_anime_click,
                on_favorite=self._on_favorite_click,
                current_user=self.current_user
            )
            cards.append(card)
        
        cards_row = ft.Container(
            content=ft.Row(
                controls=cards,
                spacing=spacing.xl,
                scroll=ft.ScrollMode.AUTO,
            ),
            margin=ft.margin.only(top=spacing.lg),
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[header, cards_row],
                spacing=0,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(0, 8)
            ),
        )
    
    async def _create_anime_grid(self, anime_list: List[Dict]) -> ft.Container:
        """Создание сетки аниме"""
        
        if not anime_list:
            return ft.Container(
                content=ft.Text(
                    "Аниме не найдено",
                    size=typography.text_lg,
                    color=colors.text_muted,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.alignment.center,
                height=200,
            )
        
        # Создаем карточки
        cards = []
        for anime in anime_list:
            card = AnimeCard(
                anime_data=anime,
                on_click=self._on_anime_click,
                on_favorite=self._on_favorite_click,
                current_user=self.current_user
            )
            cards.append(card)
        
        # Группируем в ряды
        rows = []
        cards_per_row = 5  # Количество карточек в ряду
        
        for i in range(0, len(cards), cards_per_row):
            row_cards = cards[i:i + cards_per_row]
            row = ft.Row(
                controls=row_cards,
                spacing=spacing.xl,
                alignment=ft.MainAxisAlignment.START,
            )
            rows.append(row)
        
        return ft.Container(
            content=ft.Column(
                controls=rows,
                spacing=spacing.xl,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )
    
    async def _create_history_section(self) -> ft.Container:
        """Создание секции истории просмотра"""
        
        if not self.watch_history:
            return ft.Container()
        
        # Конвертируем историю в формат аниме
        history_anime = []
        for history_item in self.watch_history[:6]:  # Показываем только первые 6
            anime_data = {
                'id': history_item.anime_id,
                'title': history_item.anime_title,
                'material_data': {
                    'title': history_item.anime_title,
                    'poster_url': history_item.anime_poster_url or 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера',
                }
            }
            history_anime.append(anime_data)
        
        return await self._create_anime_section(
            title="📖 Недавно просмотренное",
            anime_list=history_anime,
            show_more_link=True
        )
    
    async def _setup_hotkeys(self):
        """Настройка горячих клавиш"""
        # В Flet горячие клавиши настраиваются через page.on_keyboard_event
        def on_keyboard(e: ft.KeyboardEvent):
            try:
                # Проверяем различные комбинации
                if e.key == "F11":
                    # Полноэкранный режим
                    self.page.window.full_screen = not self.page.window.full_screen
                    self.page.update()
                elif e.ctrl and e.key == "F":
                    # Фокус на поиск
                    if self.search_bar and hasattr(self.search_bar, 'search_field'):
                        self.search_bar.search_field.focus()
                elif e.ctrl and e.key == "H":
                    # Домой
                    asyncio.create_task(self._on_navigate_async("home"))
                elif e.ctrl and e.key == "L":
                    # Каталог
                    asyncio.create_task(self._on_navigate_async("catalog"))
                elif e.ctrl and e.key == "D":
                    # Избранное
                    asyncio.create_task(self._on_navigate_async("favorites"))
            except Exception as ex:
                logger.error(f"Ошибка обработки горячих клавиш: {ex}")
        
        self.page.on_keyboard_event = on_keyboard
    
    async def _show_loading(self, message: str = "Загрузка..."):
        """Показать индикатор загрузки"""
        if self.loading_overlay:
            # Обновляем текст
            text_control = self.loading_overlay.content.controls[1]
            text_control.value = message
            
            self.loading_overlay.visible = True
            await self.page.update_async()
        
        self.is_loading = True
    
    async def _hide_loading(self):
        """Скрыть индикатор загрузки"""
        if self.loading_overlay:
            self.loading_overlay.visible = False
            await self.page.update_async()
        
        self.is_loading = False
    
    async def _show_error(self, title: str, message: str):
        """Показать сообщение об ошибке"""
        # В будущем можно реализовать через ft.AlertDialog
        logger.error(f"{title}: {message}")
        
        # Пока просто показываем в консоли
        print(f"ОШИБКА: {title}\n{message}")
    
    def _on_navigate(self, page_name: str):
        """Обработка навигации (синхронная версия)"""
        asyncio.create_task(self._on_navigate_async(page_name))
    
    async def _on_navigate_async(self, page_name: str):
        """Обработка навигации между страницами"""
        if page_name == self.current_page:
            return
        
        try:
            # Очищаем кеш для динамических страниц
            if page_name in ["favorites", "my_list", "stats"]:
                self.page_cache.pop(page_name, None)
            
            self.current_page = page_name
            
            # Обновляем сайдбар
            if self.sidebar:
                self.sidebar.update_page(page_name)
            
            # Обновляем контент
            new_content = await self._create_page_content()
            self.main_content.content = new_content
            
            await self.page.update_async()
            
            logger.info(f"Навигация на страницу: {page_name}")
            
        except Exception as e:
            logger.error(f"Ошибка навигации: {e}")
            await self._show_error("Ошибка навигации", str(e))
    
    async def _on_search(self, query: str, filters: Dict):
        """Обработка поиска"""
        try:
            await self._show_loading("Поиск аниме...")
            
            self.search_query = query
            self.search_filters = filters
            
            # Выполняем поиск
            if query or filters:
                self.search_results = await anime_service.search_anime(query, filters)
            else:
                self.search_results = []
            
            # Обновляем страницу каталога если мы на ней
            if self.current_page == "catalog":
                self.page_cache.pop("catalog", None)  # Очищаем кеш
                new_content = await self._create_page_content()
                self.main_content.content = new_content
                await self.page.update_async()
            
            await self._hide_loading()
            
            logger.info(f"Поиск выполнен: '{query}', найдено {len(self.search_results)} результатов")
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            await self._hide_loading()
            await self._show_error("Ошибка поиска", str(e))
    
    async def _on_filters_change(self, filters: Dict):
        """Обработка изменения фильтров"""
        # Фильтры обрабатываются в _on_search
        pass
    
    async def _on_anime_click(self, anime_data: Dict):
        """Обработка клика по аниме"""
        try:
            anime_id = anime_data.get('id', '')
            shikimori_id = anime_data.get('shikimori_id', '')
            
            logger.info(f"Открытие аниме: {anime_data.get('title', 'Неизвестно')} (ID: {anime_id})")
            
            # В будущем здесь будет переход на страницу просмотра
            # А пока просто логируем
            print(f"Открытие аниме: {anime_data.get('title', 'Неизвестно')}")
            
        except Exception as e:
            logger.error(f"Ошибка при открытии аниме: {e}")
    
    async def _on_favorite_click(self, anime_data: Dict, is_favorite: bool):
        """Обработка клика по избранному"""
        try:
            if not self.current_user:
                return
            
            # Обновляем локальные данные
            await self._load_user_data()
            
            # Обновляем сайдбар (количество избранного)
            if self.sidebar:
                self.sidebar.update_favorites_count()
            
            # Очищаем кеш страницы избранного
            self.page_cache.pop("favorites", None)
            
            action = "добавлено в" if is_favorite else "удалено из"
            logger.info(f"Аниме {anime_data.get('title', 'Неизвестно')} {action} избранного")
            
        except Exception as e:
            logger.error(f"Ошибка при работе с избранным: {e}")
    
    async def close(self):
        """Закрытие приложения"""
        try:
            # Закрываем API клиенты
            await anime_service.close()
            
            logger.info("Приложение закрыто")
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии приложения: {e}")

# ===== ЭКСПОРТ =====

__all__ = ["AnivesetApp"]