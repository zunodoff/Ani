"""
🎯 ANIVEST DESKTOP - КАРТОЧКА АНИМЕ
=================================
Компонент для отображения карточки аниме с постером и информацией
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional

from config.theme import colors, icons, spacing, typography, get_card_style, get_rating_color
from core.database.database import db_manager

logger = logging.getLogger(__name__)

class AnimeCard(ft.UserControl):
    """Карточка аниме с постером, названием, рейтингом и действиями"""
    
    def __init__(
        self, 
        anime_data: Dict[str, Any],
        width: int = 200,
        height: int = 300,
        show_actions: bool = True,
        compact: bool = False,
        on_click: Optional[Callable] = None,
        on_favorite: Optional[Callable] = None,
        current_user: Optional[Dict] = None
    ):
        super().__init__()
        
        self.anime_data = anime_data
        self.width = width
        self.height = height
        self.show_actions = show_actions
        self.compact = compact
        self.on_click = on_click
        self.on_favorite = on_favorite
        self.current_user = current_user
        
        # Извлекаем данные из anime_data
        self.material_data = anime_data.get('material_data', {})
        self.anime_id = anime_data.get('id', '')
        self.shikimori_id = anime_data.get('shikimori_id', '')
        
        # Состояния
        self.is_favorite = False
        self.is_loading = False
        
        # UI элементы
        self.poster_image = None
        self.favorite_button = None
        self.rating_container = None
        self.loading_indicator = None
        
        # Проверяем избранное при инициализации
        if self.current_user:
            asyncio.create_task(self._check_favorite_status())
    
    async def _check_favorite_status(self):
        """Проверка статуса избранного"""
        try:
            if self.current_user and self.anime_id:
                self.is_favorite = db_manager.is_in_favorites(
                    self.current_user['id'], 
                    self.anime_id
                )
                await self._update_favorite_button()
        except Exception as e:
            logger.error(f"Ошибка проверки избранного: {e}")
    
    async def _update_favorite_button(self):
        """Обновление кнопки избранного"""
        if self.favorite_button:
            self.favorite_button.icon = icons.favorite if self.is_favorite else icons.star_border
            self.favorite_button.icon_color = colors.secondary if self.is_favorite else colors.text_muted
            self.favorite_button.tooltip = "Удалить из избранного" if self.is_favorite else "Добавить в избранное"
            
            if self.page:
                self.favorite_button.update()
    
    def _get_title(self) -> str:
        """Получение названия аниме"""
        return (
            self.material_data.get('title') or 
            self.material_data.get('anime_title') or 
            self.anime_data.get('title') or 
            'Неизвестное аниме'
        )
    
    def _get_poster_url(self) -> str:
        """Получение URL постера"""
        return (
            self.material_data.get('poster_url') or
            self.material_data.get('anime_poster_url') or
            'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера'
        )
    
    def _get_rating(self) -> Optional[float]:
        """Получение рейтинга"""
        rating = self.material_data.get('shikimori_rating')
        if rating:
            try:
                return float(rating)
            except:
                pass
        return None
    
    def _get_episodes_info(self) -> str:
        """Получение информации о эпизодах"""
        episodes_total = self.material_data.get('episodes_total')
        episodes_aired = self.material_data.get('episodes_aired')
        anime_status = self.material_data.get('anime_status', '')
        
        if episodes_total:
            if anime_status.lower() == 'ongoing' and episodes_aired:
                return f"{episodes_aired}/{episodes_total} эп."
            else:
                return f"{episodes_total} эп."
        elif episodes_aired:
            return f"{episodes_aired} эп."
        else:
            return "? эп."
    
    def _get_year(self) -> str:
        """Получение года выхода"""
        year = (
            self.material_data.get('year') or 
            self.anime_data.get('year')
        )
        return str(year) if year else "?"
    
    def _get_status_color(self) -> str:
        """Получение цвета статуса"""
        status = self.material_data.get('anime_status', '').lower()
        status_colors = {
            'released': colors.success,
            'ongoing': colors.info,
            'anons': colors.warning
        }
        return status_colors.get(status, colors.text_muted)
    
    def _get_genres_text(self) -> str:
        """Получение списка жанров"""
        genres = (
            self.material_data.get('anime_genres') or 
            self.material_data.get('all_genres') or 
            []
        )
        
        if isinstance(genres, list) and genres:
            # Показываем только первые 3 жанра
            return ', '.join(genres[:3])
        return "Неизвестно"
    
    async def _on_card_click(self, e):
        """Обработка клика по карточке"""
        if self.on_click and not self.is_loading:
            try:
                self.is_loading = True
                await self._show_loading()
                await self.on_click(self.anime_data)
            except Exception as ex:
                logger.error(f"Ошибка при клике на карточку: {ex}")
            finally:
                self.is_loading = False
                await self._hide_loading()
    
    async def _on_favorite_click(self, e):
        """Обработка клика по избранному"""
        if not self.current_user:
            # Показываем сообщение о необходимости авторизации
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Войдите в систему для добавления в избранное"),
                        bgcolor=colors.warning
                    )
                )
            return
        
        try:
            self.is_loading = True
            await self._show_loading()
            
            if self.is_favorite:
                # Удаляем из избранного
                success = db_manager.remove_from_favorites(
                    self.current_user['id'], 
                    self.anime_id
                )
                if success:
                    self.is_favorite = False
                    message = "Удалено из избранного"
                else:
                    message = "Ошибка удаления из избранного"
            else:
                # Добавляем в избранное
                success = db_manager.add_to_favorites(
                    self.current_user['id'],
                    self.anime_id,
                    self._get_title(),
                    self._get_poster_url()
                )
                if success:
                    self.is_favorite = True
                    message = "Добавлено в избранное"
                else:
                    message = "Ошибка добавления в избранное"
            
            # Обновляем UI
            await self._update_favorite_button()
            
            # Показываем уведомление
            if self.page:
                snack_color = colors.success if success else colors.error
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(message),
                        bgcolor=snack_color
                    )
                )
            
            # Вызываем callback если есть
            if self.on_favorite:
                await self.on_favorite(self.anime_data, self.is_favorite)
                
        except Exception as ex:
            logger.error(f"Ошибка при работе с избранным: {ex}")
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Произошла ошибка"),
                        bgcolor=colors.error
                    )
                )
        finally:
            self.is_loading = False
            await self._hide_loading()
    
    async def _show_loading(self):
        """Показать индикатор загрузки"""
        if self.loading_indicator:
            self.loading_indicator.visible = True
            if self.page:
                self.loading_indicator.update()
    
    async def _hide_loading(self):
        """Скрыть индикатор загрузки"""
        if self.loading_indicator:
            self.loading_indicator.visible = False
            if self.page:
                self.loading_indicator.update()
    
    def build(self):
        """Построение UI карточки"""
        rating = self._get_rating()
        
        # Постер с градиентом
        poster_stack = ft.Stack(
            controls=[
                # Основной постер
                ft.Container(
                    content=ft.Image(
                        src=self._get_poster_url(),
                        width=self.width,
                        height=self.height - 80 if not self.compact else self.height - 60,
                        fit=ft.ImageFit.COVER,
                        error_content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(
                                        icons.movie,
                                        size=48,
                                        color=colors.text_muted
                                    ),
                                    ft.Text(
                                        "Нет изображения",
                                        size=typography.text_sm,
                                        color=colors.text_muted,
                                        text_align=ft.TextAlign.CENTER
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=spacing.sm
                            ),
                            alignment=ft.alignment.center,
                            bgcolor=colors.card,
                        )
                    ),
                    border_radius=ft.border_radius.vertical(
                        top=spacing.border_radius_lg
                    ),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                
                # Градиент снизу для лучшей читаемости
                ft.Container(
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.bottom_center,
                        end=ft.alignment.center,
                        colors=["#00000080", "#00000000"]
                    ),
                    border_radius=ft.border_radius.vertical(
                        top=spacing.border_radius_lg
                    ),
                ),
                
                # Кнопка избранного (если показываем действия и пользователь авторизован)
                ft.Container(
                    content=ft.IconButton(
                        icon=icons.star_border,
                        icon_color=colors.text_muted,
                        icon_size=spacing.icon_md,
                        tooltip="Добавить в избранное",
                        on_click=self._on_favorite_click,
                        ref=self.favorite_button  # Сохраняем ссылку
                    ) if self.show_actions and self.current_user else None,
                    alignment=ft.alignment.top_right,
                    padding=spacing.sm,
                ) if self.show_actions and self.current_user else ft.Container(),
                
                # Рейтинг (если есть)
                ft.Container(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    icons.star,
                                    size=spacing.icon_sm,
                                    color=colors.accent
                                ),
                                ft.Text(
                                    f"{rating:.1f}",
                                    size=typography.text_sm,
                                    weight=typography.weight_semibold,
                                    color=colors.text_primary
                                )
                            ],
                            spacing=4,
                            tight=True
                        ),
                        bgcolor=colors.background + "E6",  # 90% непрозрачность
                        border_radius=spacing.border_radius_sm,
                        padding=ft.padding.symmetric(
                            horizontal=spacing.sm,
                            vertical=4
                        )
                    ),
                    alignment=ft.alignment.top_left,
                    padding=spacing.sm,
                ) if rating and rating > 0 else ft.Container(),
                
                # Индикатор загрузки
                ft.Container(
                    content=ft.ProgressRing(
                        width=32,
                        height=32,
                        color=colors.primary
                    ),
                    alignment=ft.alignment.center,
                    bgcolor=colors.background + "CC",  # 80% непрозрачность
                    visible=False,
                    ref=self.loading_indicator  # Сохраняем ссылку
                )
            ],
            width=self.width,
            height=self.height - 80 if not self.compact else self.height - 60,
        )
        
        # Информация о аниме
        info_section = ft.Container(
            content=ft.Column(
                controls=[
                    # Название
                    ft.Text(
                        self._get_title(),
                        size=typography.text_md if not self.compact else typography.text_sm,
                        weight=typography.weight_semibold,
                        color=colors.text_primary,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    
                    # Дополнительная информация (если не компактный режим)
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                # Год
                                ft.Text(
                                    self._get_year(),
                                    size=typography.text_xs,
                                    color=colors.text_muted
                                ),
                                
                                ft.Text("•", size=typography.text_xs, color=colors.text_muted),
                                
                                # Количество эпизодов
                                ft.Text(
                                    self._get_episodes_info(),
                                    size=typography.text_xs,
                                    color=colors.text_muted
                                ),
                                
                                ft.Text("•", size=typography.text_xs, color=colors.text_muted),
                                
                                # Статус
                                ft.Container(
                                    content=ft.Text(
                                        self.material_data.get('anime_status', 'Неизвестно'),
                                        size=typography.text_xs,
                                        color=colors.text_primary,
                                        weight=typography.weight_medium
                                    ),
                                    bgcolor=self._get_status_color() + "40",  # 25% непрозрачность
                                    border_radius=spacing.border_radius_sm,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        margin=ft.margin.only(top=spacing.xs)
                    ) if not self.compact else ft.Container(),
                    
                    # Жанры (только для полной карточки)
                    ft.Text(
                        self._get_genres_text(),
                        size=typography.text_xs,
                        color=colors.text_muted,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ) if not self.compact else ft.Container(),
                ],
                spacing=spacing.xs,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True
            ),
            padding=spacing.md,
            height=80 if not self.compact else 60,
        )
        
        # Главный контейнер карточки
        card_container = ft.Container(
            content=ft.Column(
                controls=[poster_stack, info_section],
                spacing=0,
                tight=True
            ),
            width=self.width,
            height=self.height,
            bgcolor=colors.card,
            border_radius=spacing.border_radius_lg,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=colors.shadow,
                offset=ft.Offset(0, 5)
            ),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=self._on_card_click,
            ink=True,
        )
        
        # Сохраняем ссылки на элементы для дальнейшего обновления
        self.poster_image = poster_stack
        
        return card_container
    
    def update_anime_data(self, new_anime_data: Dict[str, Any]):
        """Обновление данных аниме"""
        self.anime_data = new_anime_data
        self.material_data = new_anime_data.get('material_data', {})
        self.anime_id = new_anime_data.get('id', '')
        self.shikimori_id = new_anime_data.get('shikimori_id', '')
        
        # Перестраиваем карточку
        if self.page:
            self.update()

# ===== СПЕЦИАЛИЗИРОВАННЫЕ ВАРИАНТЫ КАРТОЧЕК =====

class CompactAnimeCard(AnimeCard):
    """Компактная карточка аниме для списков"""
    
    def __init__(self, anime_data: Dict[str, Any], **kwargs):
        super().__init__(
            anime_data=anime_data,
            width=150,
            height=220,
            compact=True,
            **kwargs
        )

class LargeAnimeCard(AnimeCard):
    """Большая карточка аниме для главной страницы"""
    
    def __init__(self, anime_data: Dict[str, Any], **kwargs):
        super().__init__(
            anime_data=anime_data,
            width=240,
            height=360,
            compact=False,
            **kwargs
        )

class ListAnimeCard(ft.UserControl):
    """Горизонтальная карточка аниме для списков"""
    
    def __init__(
        self,
        anime_data: Dict[str, Any],
        width: int = 400,
        height: int = 120,
        on_click: Optional[Callable] = None,
        on_favorite: Optional[Callable] = None,
        current_user: Optional[Dict] = None
    ):
        super().__init__()
        
        self.anime_data = anime_data
        self.width = width
        self.height = height
        self.on_click = on_click
        self.on_favorite = on_favorite
        self.current_user = current_user
        
        # Извлекаем данные
        self.material_data = anime_data.get('material_data', {})
        self.anime_id = anime_data.get('id', '')
    
    def build(self):
        """Построение горизонтальной карточки"""
        poster_size = self.height - 20  # Отступы
        
        # Постер
        poster = ft.Container(
            content=ft.Image(
                src=self.material_data.get('poster_url', ''),
                width=poster_size * 0.7,  # Соотношение сторон постера
                height=poster_size,
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(
                    content=ft.Icon(icons.movie, size=32, color=colors.text_muted),
                    alignment=ft.alignment.center,
                    bgcolor=colors.surface,
                    width=poster_size * 0.7,
                    height=poster_size,
                )
            ),
            border_radius=spacing.border_radius_md,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        
        # Информация
        title = self.material_data.get('title', self.anime_data.get('title', 'Неизвестное аниме'))
        rating = self.material_data.get('shikimori_rating')
        episodes = self.material_data.get('episodes_total', '?')
        year = self.material_data.get('year', '?')
        
        info = ft.Container(
            content=ft.Column(
                controls=[
                    # Название
                    ft.Text(
                        title,
                        size=typography.text_lg,
                        weight=typography.weight_semibold,
                        color=colors.text_primary,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    
                    # Рейтинг и год
                    ft.Row(
                        controls=[
                            ft.Icon(icons.star, size=16, color=colors.accent) if rating else ft.Container(),
                            ft.Text(
                                f"{float(rating):.1f}" if rating else "",
                                size=typography.text_sm,
                                color=colors.text_secondary
                            ) if rating else ft.Container(),
                            
                            ft.Text("•", size=typography.text_sm, color=colors.text_muted) if rating else ft.Container(),
                            
                            ft.Text(
                                f"{year}",
                                size=typography.text_sm,
                                color=colors.text_secondary
                            ),
                            
                            ft.Text("•", size=typography.text_sm, color=colors.text_muted),
                            
                            ft.Text(
                                f"{episodes} эп.",
                                size=typography.text_sm,
                                color=colors.text_secondary
                            ),
                        ],
                        spacing=4,
                    ),
                    
                    # Описание (краткое)
                    ft.Text(
                        self.material_data.get('description', ''),
                        size=typography.text_sm,
                        color=colors.text_muted,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ) if self.material_data.get('description') else ft.Container(),
                ],
                spacing=spacing.sm,
                expand=True,
                alignment=ft.MainAxisAlignment.START
            ),
            expand=True,
            padding=ft.padding.only(left=spacing.md),
        )
        
        # Кнопки действий
        actions = ft.Column(
            controls=[
                ft.IconButton(
                    icon=icons.star_border,
                    icon_color=colors.text_muted,
                    tooltip="Добавить в избранное",
                    on_click=lambda e: self.on_favorite(self.anime_data) if self.on_favorite else None
                ) if self.current_user else ft.Container(),
                
                ft.IconButton(
                    icon=icons.play_circle,
                    icon_color=colors.primary,
                    tooltip="Смотреть",
                    on_click=lambda e: self.on_click(self.anime_data) if self.on_click else None
                ),
            ],
            spacing=spacing.sm,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[poster, info, actions],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=self.width,
            height=self.height,
            bgcolor=colors.card,
            border_radius=spacing.border_radius_lg,
            padding=spacing.sm,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=colors.shadow,
                offset=ft.Offset(0, 2)
            ),
            on_click=lambda e: self.on_click(self.anime_data) if self.on_click else None,
            ink=True,
        )

# ===== ЭКСПОРТ =====

__all__ = [
    "AnimeCard", "CompactAnimeCard", "LargeAnimeCard", "ListAnimeCard"
]