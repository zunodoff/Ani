"""
📺 ANIVEST DESKTOP - СТРАНИЦА КАТАЛОГА
====================================
Страница каталога с поиском и фильтрацией аниме
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from config.theme import colors, icons, spacing, typography
from config.settings import ANIME_GENRES, ANIME_TYPES, ANIME_STATUSES, SEASONS
from core.api.anime_service import anime_service

from ..components.anime_card import AnimeCard, CompactAnimeCard, ListAnimeCard
from ..components.search_bar import AnivesetSearchBar

logger = logging.getLogger(__name__)

class CatalogPage(ft.UserControl):
    """Страница каталога аниме"""
    
    def __init__(
        self,
        on_anime_click: Optional[Callable[[Dict], None]] = None,
        on_favorite_click: Optional[Callable[[Dict, bool], None]] = None,
        current_user: Optional[Dict] = None
    ):
        super().__init__()
        
        self.on_anime_click = on_anime_click
        self.on_favorite_click = on_favorite_click
        self.current_user = current_user
        
        # Данные
        self.search_results = []
        self.popular_anime = []
        self.is_search_active = False
        
        # Состояние
        self.is_loading = False
        self.current_query = ""
        self.current_filters = {}
        self.view_mode = "grid"  # grid, list, compact
        self.sort_mode = "popularity"  # popularity, rating, year, name
        
        # UI элементы
        self.search_bar = None
        self.results_container = None
        self.loading_indicator = None
        self.view_controls = None
        self.stats_container = None
        
        # Пагинация
        self.current_page = 1
        self.items_per_page = 24
        self.total_items = 0
    
    async def load_initial_data(self):
        """Загрузка начальных данных каталога"""
        try:
            await self._show_loading("Загрузка каталога...")
            
            # Загружаем популярные аниме как начальный контент
            logger.info("Загрузка популярных аниме для каталога...")
            self.popular_anime = await anime_service.get_popular_anime(48)
            self.search_results = self.popular_anime.copy()  # Показываем популярные по умолчанию
            self.total_items = len(self.search_results)
            
            await self._hide_loading()
            
            # Обновляем UI
            if self.page:
                self.update()
            
            logger.info(f"Каталог загружен: {len(self.popular_anime)} аниме")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки каталога: {e}")
            await self._hide_loading()
            
            if self.page:
                self.update()
    
    def _create_header(self) -> ft.Container:
        """Создание заголовка страницы"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "📺 Каталог аниме",
                                        size=typography.text_3xl,
                                        weight=typography.weight_bold,
                                        color=colors.text_primary,
                                    ),
                                    ft.Text(
                                        "Найдите своё идеальное аниме среди тысяч тайтлов",
                                        size=typography.text_lg,
                                        color=colors.text_secondary,
                                    ),
                                ],
                                spacing=spacing.sm,
                                expand=True,
                            ),
                            
                            # Быстрые фильтры
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.ElevatedButton(
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Text("🔥", size=typography.text_md),
                                                        ft.Text("Популярное", size=typography.text_sm),
                                                    ],
                                                    spacing=spacing.xs,
                                                    tight=True,
                                                ),
                                                bgcolor=colors.secondary if not self.is_search_active else colors.surface,
                                                color=colors.text_primary,
                                                on_click=self._show_popular,
                                                style=ft.ButtonStyle(
                                                    padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                                                ),
                                            ),
                                            
                                            ft.ElevatedButton(
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Text("🌟", size=typography.text_md),
                                                        ft.Text("Новинки", size=typography.text_sm),
                                                    ],
                                                    spacing=spacing.xs,
                                                    tight=True,
                                                ),
                                                bgcolor=colors.surface,
                                                color=colors.text_primary,
                                                on_click=self._show_seasonal,
                                                style=ft.ButtonStyle(
                                                    padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                                                ),
                                            ),
                                            
                                            ft.ElevatedButton(
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Text("⭐", size=typography.text_md),
                                                        ft.Text("Топ", size=typography.text_sm),
                                                    ],
                                                    spacing=spacing.xs,
                                                    tight=True,
                                                ),
                                                bgcolor=colors.surface,
                                                color=colors.text_primary,
                                                on_click=self._show_top_rated,
                                                style=ft.ButtonStyle(
                                                    padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                                                ),
                                            ),
                                        ],
                                        spacing=spacing.sm,
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=spacing.lg,
            ),
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_search_section(self) -> ft.Container:
        """Создание секции поиска"""
        self.search_bar = AnivesetSearchBar(
            width=800,
            on_search=self._on_search,
            on_filters_change=self._on_filters_change,
            placeholder="Поиск аниме по названию, жанру, году..."
        )
        
        return ft.Container(
            content=self.search_bar,
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_controls_bar(self) -> ft.Container:
        """Создание панели управления отображением"""
        
        # Режимы отображения
        view_modes = ft.Row(
            controls=[
                ft.Text(
                    "Вид:",
                    size=typography.text_md,
                    color=colors.text_secondary,
                ),
                
                ft.SegmentedButton(
                    segments=[
                        ft.Segment(
                            value="grid",
                            icon=ft.Icon(icons.movie),
                            label=ft.Text("Сетка", size=typography.text_sm),
                        ),
                        ft.Segment(
                            value="list",
                            icon=ft.Icon(icons.list),
                            label=ft.Text("Список", size=typography.text_sm),
                        ),
                        ft.Segment(
                            value="compact",
                            icon=ft.Icon(icons.view_list),
                            label=ft.Text("Компакт", size=typography.text_sm),
                        ),
                    ],
                    selected={self.view_mode},
                    on_change=self._on_view_mode_change,
                ),
            ],
            spacing=spacing.md,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        # Сортировка
        sort_controls = ft.Row(
            controls=[
                ft.Text(
                    "Сортировка:",
                    size=typography.text_md,
                    color=colors.text_secondary,
                ),
                
                ft.Dropdown(
                    value=self.sort_mode,
                    options=[
                        ft.dropdown.Option(key="popularity", text="По популярности"),
                        ft.dropdown.Option(key="rating", text="По рейтингу"),
                        ft.dropdown.Option(key="year", text="По году"),
                        ft.dropdown.Option(key="name", text="По названию"),
                    ],
                    width=180,
                    bgcolor=colors.surface,
                    border_color=colors.border,
                    focused_border_color=colors.primary,
                    color=colors.text_primary,
                    text_size=typography.text_sm,
                    on_change=self._on_sort_change,
                ),
            ],
            spacing=spacing.md,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        # Статистика результатов
        self.stats_container = ft.Container(
            content=self._create_results_stats(),
        )
        
        self.view_controls = ft.Container(
            content=ft.Row(
                controls=[
                    view_modes,
                    ft.VerticalDivider(width=1, color=colors.border),
                    sort_controls,
                    ft.Container(expand=True),  # Разделитель
                    self.stats_container,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_md,
            padding=spacing.md,
            margin=ft.margin.only(bottom=spacing.lg),
        )
        
        return self.view_controls
    
    def _create_results_stats(self) -> ft.Row:
        """Создание статистики результатов"""
        if not self.search_results:
            return ft.Row()
        
        start_item = (self.current_page - 1) * self.items_per_page + 1
        end_item = min(self.current_page * self.items_per_page, self.total_items)
        
        stats_text = f"Показано {start_item}-{end_item} из {self.total_items}"
        
        if self.is_search_active:
            stats_text += f" • Поиск: \"{self.current_query}\""
        
        return ft.Row(
            controls=[
                ft.Text(
                    stats_text,
                    size=typography.text_sm,
                    color=colors.text_muted,
                ),
                
                # Кнопка сброса поиска
                ft.IconButton(
                    icon=icons.close,
                    icon_color=colors.text_muted,
                    icon_size=spacing.icon_sm,
                    tooltip="Сбросить поиск",
                    on_click=self._clear_search,
                    visible=self.is_search_active,
                ),
            ],
            spacing=spacing.sm,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    def _create_results_grid(self) -> ft.Container:
        """Создание сетки результатов"""
        
        if not self.search_results:
            return self._create_empty_state()
        
        # Пагинация
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.search_results))
        page_results = self.search_results[start_idx:end_idx]
        
        # Создаем карточки в зависимости от режима отображения
        if self.view_mode == "list":
            cards = self._create_list_cards(page_results)
            content = ft.Column(
                controls=cards,
                spacing=spacing.md,
                scroll=ft.ScrollMode.AUTO,
            )
        elif self.view_mode == "compact":
            cards = self._create_compact_cards(page_results)
            # Группируем компактные карточки в ряды
            rows = []
            cards_per_row = 4
            for i in range(0, len(cards), cards_per_row):
                row_cards = cards[i:i + cards_per_row]
                row = ft.Row(
                    controls=row_cards,
                    spacing=spacing.md,
                    alignment=ft.MainAxisAlignment.START,
                )
                rows.append(row)
            
            content = ft.Column(
                controls=rows,
                spacing=spacing.md,
                scroll=ft.ScrollMode.AUTO,
            )
        else:  # grid
            cards = self._create_grid_cards(page_results)
            # Группируем в ряды
            rows = []
            cards_per_row = 5
            for i in range(0, len(cards), cards_per_row):
                row_cards = cards[i:i + cards_per_row]
                row = ft.Row(
                    controls=row_cards,
                    spacing=spacing.lg,
                    alignment=ft.MainAxisAlignment.START,
                )
                rows.append(row)
            
            content = ft.Column(
                controls=rows,
                spacing=spacing.lg,
                scroll=ft.ScrollMode.AUTO,
            )
        
        self.results_container = ft.Container(
            content=content,
            expand=True,
        )
        
        return self.results_container
    
    def _create_grid_cards(self, anime_list: List[Dict]) -> List[AnimeCard]:
        """Создание карточек для сеточного режима"""
        cards = []
        for anime in anime_list:
            card = AnimeCard(
                anime_data=anime,
                width=220,
                height=320,
                on_click=self.on_anime_click,
                on_favorite=self.on_favorite_click,
                current_user=self.current_user
            )
            cards.append(card)
        return cards
    
    def _create_list_cards(self, anime_list: List[Dict]) -> List[ListAnimeCard]:
        """Создание карточек для списочного режима"""
        cards = []
        for anime in anime_list:
            card = ListAnimeCard(
                anime_data=anime,
                width=800,
                height=140,
                on_click=self.on_anime_click,
                on_favorite=self.on_favorite_click,
                current_user=self.current_user
            )
            cards.append(card)
        return cards
    
    def _create_compact_cards(self, anime_list: List[Dict]) -> List[CompactAnimeCard]:
        """Создание карточек для компактного режима"""
        cards = []
        for anime in anime_list:
            card = CompactAnimeCard(
                anime_data=anime,
                on_click=self.on_anime_click,
                on_favorite=self.on_favorite_click,
                current_user=self.current_user
            )
            cards.append(card)
        return cards
    
    def _create_pagination(self) -> ft.Container:
        """Создание пагинации"""
        
        if self.total_items <= self.items_per_page:
            return ft.Container()
        
        total_pages = (self.total_items + self.items_per_page - 1) // self.items_per_page
        
        # Кнопки пагинации
        pagination_controls = []
        
        # Предыдущая страница
        pagination_controls.append(
            ft.IconButton(
                icon=icons.prev_track,
                icon_color=colors.text_secondary if self.current_page > 1 else colors.text_muted,
                tooltip="Предыдущая страница",
                on_click=lambda e: self._go_to_page(self.current_page - 1),
                disabled=self.current_page <= 1,
            )
        )
        
        # Номера страниц (показываем ±2 от текущей)
        start_page = max(1, self.current_page - 2)
        end_page = min(total_pages, self.current_page + 2)
        
        if start_page > 1:
            pagination_controls.append(
                ft.TextButton(
                    text="1",
                    on_click=lambda e: self._go_to_page(1),
                    style=ft.ButtonStyle(color=colors.text_secondary),
                )
            )
            if start_page > 2:
                pagination_controls.append(
                    ft.Text("...", color=colors.text_muted)
                )
        
        for page_num in range(start_page, end_page + 1):
            is_current = page_num == self.current_page
            pagination_controls.append(
                ft.ElevatedButton(
                    text=str(page_num),
                    bgcolor=colors.primary if is_current else colors.surface,
                    color=colors.text_primary,
                    on_click=lambda e, p=page_num: self._go_to_page(p),
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                    ),
                )
            )
        
        if end_page < total_pages:
            if end_page < total_pages - 1:
                pagination_controls.append(
                    ft.Text("...", color=colors.text_muted)
                )
            pagination_controls.append(
                ft.TextButton(
                    text=str(total_pages),
                    on_click=lambda e: self._go_to_page(total_pages),
                    style=ft.ButtonStyle(color=colors.text_secondary),
                )
            )
        
        # Следующая страница
        pagination_controls.append(
            ft.IconButton(
                icon=icons.next_track,
                icon_color=colors.text_secondary if self.current_page < total_pages else colors.text_muted,
                tooltip="Следующая страница",
                on_click=lambda e: self._go_to_page(self.current_page + 1),
                disabled=self.current_page >= total_pages,
            )
        )
        
        return ft.Container(
            content=ft.Row(
                controls=pagination_controls,
                spacing=spacing.sm,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            margin=ft.margin.symmetric(vertical=spacing.xl),
        )
    
    def _create_empty_state(self) -> ft.Container:
        """Создание состояния пустых результатов"""
        if self.is_search_active:
            # Нет результатов поиска
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.search, size=96, color=colors.text_muted),
                        ft.Text(
                            "Ничего не найдено",
                            size=typography.text_2xl,
                            weight=typography.weight_bold,
                            color=colors.text_muted,
                        ),
                        ft.Text(
                            f"По запросу \"{self.current_query}\" аниме не найдено",
                            size=typography.text_lg,
                            color=colors.text_muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Попробуйте изменить поисковый запрос или фильтры",
                            size=typography.text_md,
                            color=colors.text_muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.ElevatedButton(
                            text="Сбросить поиск",
                            bgcolor=colors.primary,
                            color=colors.text_primary,
                            on_click=self._clear_search,
                        ),
                    ],
                    spacing=spacing.lg,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                height=400,
            )
        else:
            # Общая ошибка загрузки
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.error, size=96, color=colors.error),
                        ft.Text(
                            "Ошибка загрузки каталога",
                            size=typography.text_2xl,
                            weight=typography.weight_bold,
                            color=colors.text_muted,
                        ),
                        ft.ElevatedButton(
                            text="Попробовать снова",
                            bgcolor=colors.primary,
                            color=colors.text_primary,
                            on_click=lambda e: asyncio.create_task(self.load_initial_data()),
                        ),
                    ],
                    spacing=spacing.lg,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                height=400,
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
                        "Поиск аниме...",
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
    
    async def _show_loading(self, message: str = "Загрузка..."):
        """Показать индикатор загрузки"""
        self.is_loading = True
        
        if self.loading_indicator:
            # Обновляем текст загрузки
            text_control = self.loading_indicator.content.controls[1]
            text_control.value = message
            self.loading_indicator.visible = True
        
        if self.results_container:
            self.results_container.visible = False
        
        if self.page:
            self.update()
    
    async def _hide_loading(self):
        """Скрыть индикатор загрузки"""
        self.is_loading = False
        
        if self.loading_indicator:
            self.loading_indicator.visible = False
        
        if self.results_container:
            self.results_container.visible = True
        
        if self.page:
            self.update()
    
    async def _on_search(self, query: str, filters: Dict):
        """Обработка поиска"""
        try:
            await self._show_loading("Поиск аниме...")
            
            self.current_query = query
            self.current_filters = filters
            self.is_search_active = bool(query or filters)
            self.current_page = 1  # Сбрасываем на первую страницу
            
            # Выполняем поиск
            if query or filters:
                self.search_results = await anime_service.search_anime(query, filters)
            else:
                # Если поиск пустой, показываем популярные
                self.search_results = self.popular_anime.copy()
                self.is_search_active = False
            
            self._sort_results()
            self.total_items = len(self.search_results)
            
            await self._hide_loading()
            
            # Обновляем UI
            if self.page:
                self.update()
            
            logger.info(f"Поиск выполнен: '{query}', найдено {len(self.search_results)} результатов")
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            await self._hide_loading()
    
    async def _on_filters_change(self, filters: Dict):
        """Обработка изменения фильтров"""
        # Фильтры обрабатываются в _on_search
        pass
    
    def _on_view_mode_change(self, e):
        """Обработка смены режима отображения"""
        if e.control.selected:
            self.view_mode = list(e.control.selected)[0]
            
            # Обновляем результаты
            if self.page:
                self.update()
    
    def _on_sort_change(self, e):
        """Обработка смены сортировки"""
        self.sort_mode = e.control.value
        self._sort_results()
        
        # Обновляем результаты
        if self.page:
            self.update()
    
    def _sort_results(self):
        """Сортировка результатов"""
        if not self.search_results:
            return
        
        if self.sort_mode == "rating":
            self.search_results.sort(
                key=lambda x: float(x.get('material_data', {}).get('shikimori_rating', 0) or 0),
                reverse=True
            )
        elif self.sort_mode == "year":
            self.search_results.sort(
                key=lambda x: int(x.get('material_data', {}).get('year', 0) or 0),
                reverse=True
            )
        elif self.sort_mode == "name":
            self.search_results.sort(
                key=lambda x: x.get('material_data', {}).get('title', '').lower()
            )
        else:  # popularity (по умолчанию)
            self.search_results.sort(
                key=lambda x: int(x.get('material_data', {}).get('shikimori_votes', 0) or 0),
                reverse=True
            )
    
    def _go_to_page(self, page_num: int):
        """Переход на указанную страницу"""
        if page_num < 1 or page_num > ((self.total_items + self.items_per_page - 1) // self.items_per_page):
            return
        
        self.current_page = page_num
        
        # Обновляем результаты
        if self.page:
            self.update()
    
    def _clear_search(self, e=None):
        """Очистка поиска"""
        self.current_query = ""
        self.current_filters = {}
        self.is_search_active = False
        self.current_page = 1
        self.search_results = self.popular_anime.copy()
        self.total_items = len(self.search_results)
        
        # Очищаем поисковую строку
        if self.search_bar:
            self.search_bar.set_search_query("")
            self.search_bar.set_filters({})
        
        # Обновляем UI
        if self.page:
            self.update()
    
    def _show_popular(self, e):
        """Показать популярные аниме"""
        asyncio.create_task(self._load_popular())
    
    def _show_seasonal(self, e):
        """Показать сезонные аниме"""
        asyncio.create_task(self._load_seasonal())
    
    def _show_top_rated(self, e):
        """Показать топ по рейтингу"""
        asyncio.create_task(self._load_top_rated())
    
    async def _load_popular(self):
        """Загрузка популярных аниме"""
        try:
            await self._show_loading("Загрузка популярных аниме...")
            
            self.search_results = await anime_service.get_popular_anime(48)
            self.is_search_active = False
            self.current_page = 1
            self.total_items = len(self.search_results)
            
            await self._hide_loading()
            
            if self.page:
                self.update()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки популярных: {e}")
            await self._hide_loading()
    
    async def _load_seasonal(self):
        """Загрузка сезонных аниме"""
        try:
            await self._show_loading("Загрузка новинок сезона...")
            
            self.search_results = await anime_service.get_seasonal_anime(limit=48)
            self.is_search_active = False
            self.current_page = 1
            self.total_items = len(self.search_results)
            
            await self._hide_loading()
            
            if self.page:
                self.update()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки сезонных: {e}")
            await self._hide_loading()
    
    async def _load_top_rated(self):
        """Загрузка топ аниме по рейтингу"""
        try:
            await self._show_loading("Загрузка топ аниме...")
            
            # Загружаем популярные и сортируем по рейтингу
            results = await anime_service.get_popular_anime(48)
            results.sort(
                key=lambda x: float(x.get('material_data', {}).get('shikimori_rating', 0) or 0),
                reverse=True
            )
            
            self.search_results = results
            self.is_search_active = False
            self.current_page = 1
            self.total_items = len(self.search_results)
            
            await self._hide_loading()
            
            if self.page:
                self.update()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки топ аниме: {e}")
            await self._hide_loading()
    
    def set_search_query(self, query: str, filters: Dict = None):
        """Установка поискового запроса извне"""
        if self.search_bar:
            self.search_bar.set_search_query(query)
            if filters:
                self.search_bar.set_filters(filters)
        
        asyncio.create_task(self._on_search(query, filters or {}))
    
    def update_user(self, user: Optional[Dict]):
        """Обновление информации о пользователе"""
        self.current_user = user
        
        # Обновляем все карточки с новым пользователем
        if self.page:
            self.update()
    
    def build(self):
        """Построение UI страницы каталога"""
        
        # Основной контент
        content_sections = [
            self._create_header(),
            self._create_search_section(),
            self._create_controls_bar(),
        ]
        
        # Результаты или загрузка
        if self.is_loading:
            content_sections.append(self._create_loading_indicator())
        else:
            content_sections.extend([
                self._create_results_grid(),
                self._create_pagination(),
            ])
        
        return ft.Container(
            content=ft.Column(
                controls=content_sections,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xxl,
            expand=True,
        )

# ===== ЭКСПОРТ =====

__all__ = ["CatalogPage"]