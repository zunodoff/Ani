"""
🔍 ANIVEST DESKTOP - СТРОКА ПОИСКА С ФИЛЬТРАМИ
============================================
Компонент поиска аниме с расширенными фильтрами
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime, timedelta

from config.theme import colors, icons, spacing, typography, get_input_style, get_button_style
from config.settings import ANIME_GENRES, ANIME_TYPES, ANIME_STATUSES, SEASONS

logger = logging.getLogger(__name__)

class SearchFilters:
    """Класс для хранения фильтров поиска"""
    
    def __init__(self):
        self.query: str = ""
        self.genre: str = ""
        self.year_from: str = ""
        self.year_to: str = ""
        self.status: str = ""
        self.anime_type: str = ""
        self.season: str = ""
        self.year: str = ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        filters = {}
        
        if self.genre:
            filters["genre"] = self.genre
        if self.year_from:
            filters["year_from"] = self.year_from
        if self.year_to:
            filters["year_to"] = self.year_to
        if self.status:
            filters["status"] = self.status
        if self.anime_type:
            filters["type"] = self.anime_type
        if self.season and self.year:
            filters["season"] = f"{self.season}_{self.year}"
            
        return filters
    
    def clear(self):
        """Очистка всех фильтров"""
        self.query = ""
        self.genre = ""
        self.year_from = ""
        self.year_to = ""
        self.status = ""
        self.anime_type = ""
        self.season = ""
        self.year = ""
    
    def has_filters(self) -> bool:
        """Проверка наличия активных фильтров"""
        return bool(
            self.genre or self.year_from or self.year_to or 
            self.status or self.anime_type or (self.season and self.year)
        )

class AnivesetSearchBar(ft.UserControl):
    """Строка поиска с расширенными фильтрами"""
    
    def __init__(
        self,
        width: int = 600,
        on_search: Optional[Callable[[str, Dict], None]] = None,
        on_filters_change: Optional[Callable[[Dict], None]] = None,
        placeholder: str = "Поиск аниме...",
        show_filters: bool = True,
        compact_mode: bool = False
    ):
        super().__init__()
        
        self.width = width
        self.on_search = on_search
        self.on_filters_change = on_filters_change
        self.placeholder = placeholder
        self.show_filters = show_filters
        self.compact_mode = compact_mode
        
        # Состояние
        self.filters = SearchFilters()
        self.filters_expanded = False
        self.search_debounce_timer = None
        self.debounce_delay = 0.5  # 500ms задержка для поиска
        
        # UI элементы
        self.search_field = None
        self.filters_container = None
        self.filters_button = None
        self.clear_button = None
        
        # Элементы фильтров
        self.genre_dropdown = None
        self.year_from_field = None
        self.year_to_field = None
        self.status_dropdown = None
        self.type_dropdown = None
        self.season_dropdown = None
        self.season_year_dropdown = None
    
    def _create_search_field(self) -> ft.TextField:
        """Создание поля поиска"""
        self.search_field = ft.TextField(
            hint_text=self.placeholder,
            prefix_icon=icons.search,
            border_color=colors.border,
            focused_border_color=colors.primary,
            bgcolor=colors.surface,
            color=colors.text_primary,
            border_radius=spacing.border_radius_md,
            height=45,
            text_size=typography.text_md,
            content_padding=ft.padding.symmetric(
                horizontal=spacing.md,
                vertical=spacing.sm
            ),
            on_change=self._on_search_change,
            on_submit=self._on_search_submit,
            expand=True,
        )
        
        return self.search_field
    
    def _create_action_buttons(self) -> ft.Row:
        """Создание кнопок действий"""
        buttons = []
        
        # Кнопка фильтров
        if self.show_filters:
            self.filters_button = ft.IconButton(
                icon=icons.filter_list,
                icon_color=colors.primary if self.filters.has_filters() else colors.text_muted,
                tooltip="Фильтры",
                on_click=self._toggle_filters,
            )
            buttons.append(self.filters_button)
        
        # Кнопка очистки
        self.clear_button = ft.IconButton(
            icon=icons.close,
            icon_color=colors.text_muted,
            tooltip="Очистить",
            on_click=self._clear_search,
            visible=False,
        )
        buttons.append(self.clear_button)
        
        # Кнопка поиска
        search_button = ft.IconButton(
            icon=icons.search,
            icon_color=colors.primary,
            tooltip="Поиск",
            on_click=self._perform_search,
        )
        buttons.append(search_button)
        
        return ft.Row(
            controls=buttons,
            spacing=spacing.xs,
            tight=True,
        )
    
    def _create_filters_section(self) -> ft.Container:
        """Создание секции фильтров"""
        
        # Dropdown для жанров
        self.genre_dropdown = ft.Dropdown(
            hint_text="Жанр",
            options=[ft.dropdown.Option(genre) for genre in ANIME_GENRES],
            width=160,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_filter_change,
        )
        
        # Поля для диапазона годов
        current_year = datetime.now().year
        
        self.year_from_field = ft.TextField(
            hint_text="От года",
            width=100,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            text_size=typography.text_sm,
            content_padding=ft.padding.all(spacing.sm),
            on_change=self._on_filter_change,
            input_filter=ft.NumbersOnlyInputFilter(),
        )
        
        self.year_to_field = ft.TextField(
            hint_text="До года",
            width=100,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            text_size=typography.text_sm,
            content_padding=ft.padding.all(spacing.sm),
            on_change=self._on_filter_change,
            input_filter=ft.NumbersOnlyInputFilter(),
        )
        
        # Dropdown для статуса
        self.status_dropdown = ft.Dropdown(
            hint_text="Статус",
            options=[
                ft.dropdown.Option(
                    key=status["value"],
                    text=status["label"]
                ) for status in ANIME_STATUSES
            ],
            width=140,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_filter_change,
        )
        
        # Dropdown для типа
        self.type_dropdown = ft.Dropdown(
            hint_text="Тип",
            options=[
                ft.dropdown.Option(
                    key=anime_type["value"],
                    text=anime_type["label"]
                ) for anime_type in ANIME_TYPES
            ],
            width=140,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_filter_change,
        )
        
        # Dropdown для сезона
        self.season_dropdown = ft.Dropdown(
            hint_text="Сезон",
            options=[
                ft.dropdown.Option(
                    key=season["value"],
                    text=f"{season['emoji']} {season['label']}"
                ) for season in SEASONS
            ],
            width=120,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_filter_change,
        )
        
        # Dropdown для года сезона
        season_years = [str(year) for year in range(current_year - 10, current_year + 2)]
        self.season_year_dropdown = ft.Dropdown(
            hint_text="Год",
            options=[ft.dropdown.Option(year) for year in season_years],
            width=100,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_filter_change,
        )
        
        # Группируем фильтры
        filters_row1 = ft.Row(
            controls=[
                self.genre_dropdown,
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.year_from_field,
                            ft.Text("—", color=colors.text_muted),
                            self.year_to_field,
                        ],
                        spacing=spacing.xs,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    tooltip="Диапазон лет",
                ),
                self.status_dropdown,
            ],
            spacing=spacing.md,
            wrap=True,
        )
        
        filters_row2 = ft.Row(
            controls=[
                self.type_dropdown,
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.season_dropdown,
                            self.season_year_dropdown,
                        ],
                        spacing=spacing.xs,
                    ),
                    tooltip="Аниме определенного сезона",
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icons.close, size=spacing.icon_sm),
                            ft.Text("Сбросить", size=typography.text_sm),
                        ],
                        spacing=spacing.xs,
                        tight=True,
                    ),
                    bgcolor=colors.surface,
                    color=colors.text_muted,
                    on_click=self._clear_filters,
                ),
            ],
            spacing=spacing.md,
            wrap=True,
        )
        
        self.filters_container = ft.Container(
            content=ft.Column(
                controls=[
                    filters_row1,
                    filters_row2,
                ],
                spacing=spacing.md,
            ),
            bgcolor=colors.background,
            border=ft.border.all(1, colors.border),
            border_radius=spacing.border_radius_md,
            padding=spacing.md,
            margin=ft.margin.only(top=spacing.sm),
            visible=self.filters_expanded,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )
        
        return self.filters_container
    
    def _on_search_change(self, e):
        """Обработка изменения текста поиска с debounce"""
        self.filters.query = e.control.value
        
        # Показываем/скрываем кнопку очистки
        if self.clear_button:
            self.clear_button.visible = bool(e.control.value)
            self.clear_button.update()
        
        # Отменяем предыдущий таймер
        if self.search_debounce_timer:
            self.search_debounce_timer.cancel()
        
        # Устанавливаем новый таймер
        self.search_debounce_timer = asyncio.create_task(
            self._debounced_search()
        )
    
    async def _debounced_search(self):
        """Поиск с задержкой"""
        try:
            await asyncio.sleep(self.debounce_delay)
            await self._perform_search_async()
        except asyncio.CancelledError:
            pass
    
    def _on_search_submit(self, e):
        """Обработка отправки формы поиска"""
        # Отменяем debounce и выполняем поиск немедленно
        if self.search_debounce_timer:
            self.search_debounce_timer.cancel()
        
        asyncio.create_task(self._perform_search_async())
    
    def _on_filter_change(self, e):
        """Обработка изменения фильтров"""
        # Обновляем состояние фильтров
        if self.genre_dropdown and e.control == self.genre_dropdown:
            self.filters.genre = e.control.value or ""
        elif self.year_from_field and e.control == self.year_from_field:
            self.filters.year_from = e.control.value or ""
        elif self.year_to_field and e.control == self.year_to_field:
            self.filters.year_to = e.control.value or ""
        elif self.status_dropdown and e.control == self.status_dropdown:
            self.filters.status = e.control.value or ""
        elif self.type_dropdown and e.control == self.type_dropdown:
            self.filters.anime_type = e.control.value or ""
        elif self.season_dropdown and e.control == self.season_dropdown:
            self.filters.season = e.control.value or ""
        elif self.season_year_dropdown and e.control == self.season_year_dropdown:
            self.filters.year = e.control.value or ""
        
        # Обновляем кнопку фильтров
        if self.filters_button:
            self.filters_button.icon_color = colors.primary if self.filters.has_filters() else colors.text_muted
            self.filters_button.update()
        
        # Вызываем callback изменения фильтров
        if self.on_filters_change:
            self.on_filters_change(self.filters.to_dict())
        
        # Автоматический поиск при изменении фильтров
        asyncio.create_task(self._perform_search_async())
    
    def _toggle_filters(self, e):
        """Переключение видимости фильтров"""
        self.filters_expanded = not self.filters_expanded
        
        if self.filters_container:
            self.filters_container.visible = self.filters_expanded
            self.filters_container.update()
        
        # Обновляем иконку кнопки
        if self.filters_button:
            self.filters_button.icon = icons.filter_list if not self.filters_expanded else icons.close
            self.filters_button.update()
    
    def _clear_search(self, e):
        """Очистка поискового запроса"""
        if self.search_field:
            self.search_field.value = ""
            self.search_field.update()
        
        self.filters.query = ""
        
        if self.clear_button:
            self.clear_button.visible = False
            self.clear_button.update()
        
        # Выполняем поиск с пустым запросом
        asyncio.create_task(self._perform_search_async())
    
    def _clear_filters(self, e):
        """Очистка всех фильтров"""
        # Очищаем состояние
        self.filters.clear()
        
        # Очищаем UI элементы
        if self.genre_dropdown:
            self.genre_dropdown.value = None
            self.genre_dropdown.update()
        
        if self.year_from_field:
            self.year_from_field.value = ""
            self.year_from_field.update()
        
        if self.year_to_field:
            self.year_to_field.value = ""
            self.year_to_field.update()
        
        if self.status_dropdown:
            self.status_dropdown.value = None
            self.status_dropdown.update()
        
        if self.type_dropdown:
            self.type_dropdown.value = None
            self.type_dropdown.update()
        
        if self.season_dropdown:
            self.season_dropdown.value = None
            self.season_dropdown.update()
        
        if self.season_year_dropdown:
            self.season_year_dropdown.value = None
            self.season_year_dropdown.update()
        
        # Обновляем кнопку фильтров
        if self.filters_button:
            self.filters_button.icon_color = colors.text_muted
            self.filters_button.update()
        
        # Вызываем callbacks
        if self.on_filters_change:
            self.on_filters_change({})
        
        # Выполняем поиск
        asyncio.create_task(self._perform_search_async())
    
    def _perform_search(self, e=None):
        """Выполнение поиска (синхронная версия)"""
        asyncio.create_task(self._perform_search_async())
    
    async def _perform_search_async(self):
        """Выполнение поиска (асинхронная версия)"""
        try:
            if self.on_search:
                await self.on_search(self.filters.query, self.filters.to_dict())
                
            logger.info(f"Поиск: '{self.filters.query}' с фильтрами: {self.filters.to_dict()}")
        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {e}")
    
    def set_search_query(self, query: str):
        """Установка поискового запроса программно"""
        self.filters.query = query
        
        if self.search_field:
            self.search_field.value = query
            self.search_field.update()
        
        if self.clear_button:
            self.clear_button.visible = bool(query)
            self.clear_button.update()
    
    def set_filters(self, filters_dict: Dict[str, Any]):
        """Установка фильтров программно"""
        # Обновляем состояние
        if "genre" in filters_dict:
            self.filters.genre = filters_dict["genre"]
        if "year_from" in filters_dict:
            self.filters.year_from = str(filters_dict["year_from"])
        if "year_to" in filters_dict:
            self.filters.year_to = str(filters_dict["year_to"])
        if "status" in filters_dict:
            self.filters.status = filters_dict["status"]
        if "type" in filters_dict:
            self.filters.anime_type = filters_dict["type"]
        if "season" in filters_dict:
            # Разбираем формат "season_year"
            season_data = filters_dict["season"].split("_")
            if len(season_data) == 2:
                self.filters.season = season_data[0]
                self.filters.year = season_data[1]
        
        # Обновляем UI (если уже построен)
        if self.page:
            self._update_filters_ui()
    
    def _update_filters_ui(self):
        """Обновление UI фильтров"""
        if self.genre_dropdown:
            self.genre_dropdown.value = self.filters.genre or None
            self.genre_dropdown.update()
        
        if self.year_from_field:
            self.year_from_field.value = self.filters.year_from
            self.year_from_field.update()
        
        if self.year_to_field:
            self.year_to_field.value = self.filters.year_to
            self.year_to_field.update()
        
        if self.status_dropdown:
            self.status_dropdown.value = self.filters.status or None
            self.status_dropdown.update()
        
        if self.type_dropdown:
            self.type_dropdown.value = self.filters.anime_type or None
            self.type_dropdown.update()
        
        if self.season_dropdown:
            self.season_dropdown.value = self.filters.season or None
            self.season_dropdown.update()
        
        if self.season_year_dropdown:
            self.season_year_dropdown.value = self.filters.year or None
            self.season_year_dropdown.update()
        
        # Обновляем кнопку фильтров
        if self.filters_button:
            self.filters_button.icon_color = colors.primary if self.filters.has_filters() else colors.text_muted
            self.filters_button.update()
    
    def build(self):
        """Построение UI компонента поиска"""
        # Основная строка поиска
        search_row = ft.Container(
            content=ft.Row(
                controls=[
                    self._create_search_field(),
                    self._create_action_buttons(),
                ],
                spacing=spacing.sm,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=colors.surface,
            border=ft.border.all(1, colors.border),
            border_radius=spacing.border_radius_md,
            padding=ft.padding.symmetric(
                horizontal=spacing.sm,
                vertical=spacing.xs
            ),
        )
        
        # Главный контейнер
        main_content = ft.Column(
            controls=[
                search_row,
                self._create_filters_section() if self.show_filters else ft.Container(),
            ],
            spacing=0,
            width=self.width,
        )
        
        return main_content

# ===== УПРОЩЕННАЯ ВЕРСИЯ =====

class SimpleSearchBar(AnivesetSearchBar):
    """Упрощенная версия строки поиска без фильтров"""
    
    def __init__(self, **kwargs):
        super().__init__(show_filters=False, **kwargs)

# ===== КОМПАКТНАЯ ВЕРСИЯ =====

class CompactSearchBar(AnivesetSearchBar):
    """Компактная версия строки поиска"""
    
    def __init__(self, **kwargs):
        super().__init__(width=400, compact_mode=True, **kwargs)

# ===== ЭКСПОРТ =====

__all__ = [
    "SearchFilters", "AnivesetSearchBar", "SimpleSearchBar", "CompactSearchBar"
]