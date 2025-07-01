"""
📺 ANIVEST DESKTOP - СПИСОК ЭПИЗОДОВ
==================================
Компонент для выбора и навигации по эпизодам аниме
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from collections import defaultdict

from config.theme import colors, icons, spacing, typography, get_button_style
from core.database.database import db_manager

logger = logging.getLogger(__name__)

class EpisodeItem(ft.UserControl):
    """Элемент списка - один эпизод"""
    
    def __init__(
        self,
        episode_data: Dict[str, Any],
        is_current: bool = False,
        is_watched: bool = False,
        on_click: Optional[Callable] = None,
        compact_mode: bool = False
    ):
        super().__init__()
        
        self.episode_data = episode_data
        self.is_current = is_current
        self.is_watched = is_watched
        self.on_click = on_click
        self.compact_mode = compact_mode
        
        # Извлекаем данные эпизода
        self.season = episode_data.get('season', 1)
        self.episode = episode_data.get('episode', 1)
        self.title = episode_data.get('title', f'Эпизод {self.episode}')
        self.link = episode_data.get('link', '')
        self.screenshot = episode_data.get('screenshot', '')
        self.duration = episode_data.get('duration', '')
    
    def _get_episode_number_display(self) -> str:
        """Получение отображаемого номера эпизода"""
        if self.season > 1:
            return f"S{self.season}E{self.episode}"
        else:
            return f"{self.episode}"
    
    def build(self):
        """Построение UI элемента эпизода"""
        
        # Иконка статуса
        status_icon = None
        if self.is_current:
            status_icon = ft.Icon(
                icons.play_circle,
                color=colors.primary,
                size=spacing.icon_md
            )
        elif self.is_watched:
            status_icon = ft.Icon(
                icons.check_circle,
                color=colors.success,
                size=spacing.icon_sm
            )
        else:
            status_icon = ft.Container(width=spacing.icon_sm, height=spacing.icon_sm)
        
        if self.compact_mode:
            # Компактный режим - только номер и иконка
            content = ft.Container(
                content=ft.Row(
                    controls=[
                        status_icon,
                        ft.Text(
                            self._get_episode_number_display(),
                            size=typography.text_sm,
                            color=colors.text_primary if self.is_current else colors.text_secondary,
                            weight=typography.weight_semibold if self.is_current else typography.weight_normal,
                        ),
                    ],
                    spacing=spacing.sm,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                width=60,
                height=40,
                bgcolor=colors.primary + "20" if self.is_current else "transparent",
                border=ft.border.all(
                    1, 
                    colors.primary if self.is_current else colors.border
                ),
                border_radius=spacing.border_radius_sm,
                padding=spacing.sm,
                on_click=lambda e: self.on_click(self.season, self.episode) if self.on_click else None,
                ink=True,
            )
        else:
            # Полный режим с описанием
            
            # Превью эпизода (если есть скриншот)
            preview = ft.Container(
                content=ft.Image(
                    src=self.screenshot,
                    width=120,
                    height=68,  # 16:9 соотношение
                    fit=ft.ImageFit.COVER,
                    error_content=ft.Container(
                        content=ft.Icon(
                            icons.movie,
                            size=spacing.icon_lg,
                            color=colors.text_muted
                        ),
                        alignment=ft.alignment.center,
                        bgcolor=colors.surface,
                    )
                ) if self.screenshot else ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                icons.movie,
                                size=spacing.icon_lg,
                                color=colors.text_muted
                            ),
                            ft.Text(
                                self._get_episode_number_display(),
                                size=typography.text_lg,
                                color=colors.text_primary,
                                weight=typography.weight_bold,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=spacing.xs,
                    ),
                    alignment=ft.alignment.center,
                    bgcolor=colors.surface,
                ),
                width=120,
                height=68,
                border_radius=spacing.border_radius_sm,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
            
            # Информация об эпизоде
            episode_info = ft.Container(
                content=ft.Column(
                    controls=[
                        # Номер и название
                        ft.Text(
                            f"{self._get_episode_number_display()}. {self.title}",
                            size=typography.text_md,
                            color=colors.text_primary if self.is_current else colors.text_secondary,
                            weight=typography.weight_semibold if self.is_current else typography.weight_normal,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        
                        # Дополнительная информация
                        ft.Row(
                            controls=[
                                status_icon,
                                ft.Text(
                                    "Текущий" if self.is_current else ("Просмотрен" if self.is_watched else "Не просмотрен"),
                                    size=typography.text_xs,
                                    color=colors.primary if self.is_current else (colors.success if self.is_watched else colors.text_muted),
                                ),
                                ft.Text(
                                    f"• {self.duration}" if self.duration else "",
                                    size=typography.text_xs,
                                    color=colors.text_muted,
                                ) if self.duration else ft.Container(),
                            ],
                            spacing=spacing.xs,
                        ),
                    ],
                    spacing=spacing.xs,
                    expand=True,
                ),
                expand=True,
                padding=ft.padding.only(left=spacing.md),
            )
            
            # Кнопка воспроизведения
            play_button = ft.IconButton(
                icon=icons.play_circle if not self.is_current else icons.pause_circle,
                icon_color=colors.primary,
                icon_size=spacing.icon_lg,
                tooltip="Воспроизвести" if not self.is_current else "Текущий эпизод",
                on_click=lambda e: self.on_click(self.season, self.episode) if self.on_click else None,
            )
            
            content = ft.Container(
                content=ft.Row(
                    controls=[
                        preview,
                        episode_info,
                        play_button,
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=colors.primary + "10" if self.is_current else colors.surface,
                border=ft.border.all(
                    2 if self.is_current else 1,
                    colors.primary if self.is_current else colors.border
                ),
                border_radius=spacing.border_radius_md,
                padding=spacing.md,
                margin=ft.margin.symmetric(vertical=spacing.xs),
                on_click=lambda e: self.on_click(self.season, self.episode) if self.on_click else None,
                ink=True,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            )
        
        return content
    
    def update_status(self, is_current: bool, is_watched: bool):
        """Обновление статуса эпизода"""
        self.is_current = is_current
        self.is_watched = is_watched
        if self.page:
            self.update()

class SeasonSelector(ft.UserControl):
    """Селектор сезонов"""
    
    def __init__(
        self,
        seasons_list: List[int],
        current_season: int = 1,
        on_season_change: Optional[Callable] = None
    ):
        super().__init__()
        
        self.seasons_list = seasons_list
        self.current_season = current_season
        self.on_season_change = on_season_change
        
        # UI элементы
        self.season_buttons = {}
    
    def build(self):
        """Построение селектора сезонов"""
        if len(self.seasons_list) <= 1:
            # Если сезон один, не показываем селектор
            return ft.Container()
        
        # Создаем кнопки для каждого сезона
        season_controls = []
        
        for season_num in self.seasons_list:
            is_current = season_num == self.current_season
            
            button = ft.Container(
                content=ft.Text(
                    f"Сезон {season_num}",
                    size=typography.text_sm,
                    color=colors.text_primary if is_current else colors.text_secondary,
                    weight=typography.weight_semibold if is_current else typography.weight_normal,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=colors.primary if is_current else colors.surface,
                border=ft.border.all(1, colors.primary if is_current else colors.border),
                border_radius=spacing.border_radius_sm,
                padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                on_click=lambda e, s=season_num: self._on_season_click(s),
                ink=True,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            )
            
            self.season_buttons[season_num] = button
            season_controls.append(button)
        
        return ft.Container(
            content=ft.Row(
                controls=season_controls,
                spacing=spacing.sm,
                wrap=True,
            ),
            margin=ft.margin.only(bottom=spacing.md),
        )
    
    def _on_season_click(self, season_num: int):
        """Обработка клика по сезону"""
        if season_num != self.current_season:
            self.current_season = season_num
            
            # Обновляем кнопки
            for s_num, button in self.season_buttons.items():
                is_current = s_num == season_num
                
                button.bgcolor = colors.primary if is_current else colors.surface
                button.border = ft.border.all(1, colors.primary if is_current else colors.border)
                
                # Обновляем текст
                text_control = button.content
                text_control.color = colors.text_primary if is_current else colors.text_secondary
                text_control.weight = typography.weight_semibold if is_current else typography.weight_normal
                
                button.update()
            
            # Вызываем callback
            if self.on_season_change:
                self.on_season_change(season_num)

class AnimeEpisodeList(ft.UserControl):
    """Список эпизодов аниме с группировкой по сезонам"""
    
    def __init__(
        self,
        anime_data: Dict[str, Any],
        episodes_list: List[Dict[str, Any]],
        current_season: int = 1,
        current_episode: int = 1,
        current_user: Optional[Dict] = None,
        on_episode_select: Optional[Callable] = None,
        compact_mode: bool = False,
        max_height: Optional[int] = None
    ):
        super().__init__()
        
        self.anime_data = anime_data
        self.episodes_list = episodes_list
        self.current_season = current_season
        self.current_episode = current_episode
        self.current_user = current_user
        self.on_episode_select = on_episode_select
        self.compact_mode = compact_mode
        self.max_height = max_height
        
        # Группируем эпизоды по сезонам
        self.episodes_by_season = self._group_episodes_by_season()
        self.seasons_list = sorted(self.episodes_by_season.keys())
        
        # Получаем информацию о просмотренных эпизодах
        self.watched_episodes = self._get_watched_episodes()
        
        # UI элементы
        self.season_selector = None
        self.episodes_container = None
        self.episode_items = {}
    
    def _group_episodes_by_season(self) -> Dict[int, List[Dict]]:
        """Группировка эпизодов по сезонам"""
        grouped = defaultdict(list)
        
        for episode in self.episodes_list:
            season = episode.get('season', 1)
            grouped[season].append(episode)
        
        # Сортируем эпизоды в каждом сезоне
        for season in grouped:
            grouped[season].sort(key=lambda ep: ep.get('episode', 1))
        
        return dict(grouped)
    
    def _get_watched_episodes(self) -> set:
        """Получение множества просмотренных эпизодов"""
        watched = set()
        
        try:
            if self.current_user:
                anime_id = self.anime_data.get('id', '')
                progress = db_manager.get_watch_progress(
                    self.current_user['id'], 
                    anime_id
                )
                
                if progress:
                    # Помечаем как просмотренные все эпизоды до текущего включительно
                    for season in range(1, progress.season_number + 1):
                        if season < progress.season_number:
                            # Все эпизоды предыдущих сезонов
                            if season in self.episodes_by_season:
                                for episode in self.episodes_by_season[season]:
                                    watched.add((season, episode.get('episode', 1)))
                        else:
                            # Эпизоды текущего сезона до текущего включительно
                            if season in self.episodes_by_season:
                                for episode in self.episodes_by_season[season]:
                                    ep_num = episode.get('episode', 1)
                                    if ep_num <= progress.episode_number:
                                        watched.add((season, ep_num))
        except Exception as e:
            logger.error(f"Ошибка получения просмотренных эпизодов: {e}")
        
        return watched
    
    def _create_episodes_list(self, season: int) -> ft.Column:
        """Создание списка эпизодов для сезона"""
        if season not in self.episodes_by_season:
            return ft.Column([])
        
        episode_controls = []
        
        for episode_data in self.episodes_by_season[season]:
            ep_season = episode_data.get('season', 1)
            ep_number = episode_data.get('episode', 1)
            
            is_current = (ep_season == self.current_season and 
                         ep_number == self.current_episode)
            is_watched = (ep_season, ep_number) in self.watched_episodes
            
            episode_item = EpisodeItem(
                episode_data=episode_data,
                is_current=is_current,
                is_watched=is_watched,
                on_click=self._on_episode_click,
                compact_mode=self.compact_mode
            )
            
            # Сохраняем ссылку для обновления
            self.episode_items[(ep_season, ep_number)] = episode_item
            
            episode_controls.append(episode_item)
        
        if self.compact_mode:
            # В компактном режиме показываем эпизоды в сетке
            return ft.Column(
                controls=[
                    ft.GridView(
                        controls=episode_controls,
                        runs_count=6,  # 6 колонок
                        max_extent=70,
                        child_aspect_ratio=1.5,
                        spacing=spacing.sm,
                        run_spacing=spacing.sm,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
            )
        else:
            # В полном режиме показываем список
            return ft.Column(
                controls=episode_controls,
                spacing=spacing.xs,
                scroll=ft.ScrollMode.AUTO,
            )
    
    def _on_episode_click(self, season: int, episode: int):
        """Обработка клика по эпизоду"""
        if (season != self.current_season or episode != self.current_episode):
            # Обновляем текущий эпизод
            old_key = (self.current_season, self.current_episode)
            new_key = (season, episode)
            
            self.current_season = season
            self.current_episode = episode
            
            # Обновляем статус старого эпизода
            if old_key in self.episode_items:
                old_item = self.episode_items[old_key]
                old_item.update_status(
                    is_current=False,
                    is_watched=old_key in self.watched_episodes
                )
            
            # Обновляем статус нового эпизода
            if new_key in self.episode_items:
                new_item = self.episode_items[new_key]
                new_item.update_status(
                    is_current=True,
                    is_watched=new_key in self.watched_episodes
                )
            
            # Перестраиваем список если сменился сезон
            if old_key[0] != season:
                if self.episodes_container:
                    self.episodes_container.content = self._create_episodes_list(season)
                    self.episodes_container.update()
            
            # Вызываем callback
            if self.on_episode_select:
                asyncio.create_task(self.on_episode_select(season, episode))
            
            logger.info(f"Выбран эпизод S{season}E{episode}")
    
    def _on_season_change(self, season: int):
        """Обработка смены сезона"""
        if self.episodes_container:
            self.episodes_container.content = self._create_episodes_list(season)
            self.episodes_container.update()
    
    def update_current_episode(self, season: int, episode: int):
        """Обновление текущего эпизода"""
        if (season != self.current_season or episode != self.current_episode):
            old_key = (self.current_season, self.current_episode)
            new_key = (season, episode)
            
            self.current_season = season
            self.current_episode = episode
            
            # Обновляем элементы
            if old_key in self.episode_items:
                self.episode_items[old_key].update_status(
                    is_current=False,
                    is_watched=old_key in self.watched_episodes
                )
            
            if new_key in self.episode_items:
                self.episode_items[new_key].update_status(
                    is_current=True,
                    is_watched=new_key in self.watched_episodes
                )
            
            # Обновляем селектор сезонов если нужно
            if self.season_selector and old_key[0] != season:
                self.season_selector.current_season = season
                if self.season_selector.page:
                    self.season_selector.update()
                
                # Обновляем список эпизодов
                if self.episodes_container:
                    self.episodes_container.content = self._create_episodes_list(season)
                    self.episodes_container.update()
    
    def mark_episode_watched(self, season: int, episode: int):
        """Отметить эпизод как просмотренный"""
        self.watched_episodes.add((season, episode))
        
        if (season, episode) in self.episode_items:
            episode_item = self.episode_items[(season, episode)]
            episode_item.update_status(
                is_current=episode_item.is_current,
                is_watched=True
            )
    
    def get_total_episodes_count(self) -> int:
        """Получение общего количества эпизодов"""
        return len(self.episodes_list)
    
    def get_watched_episodes_count(self) -> int:
        """Получение количества просмотренных эпизодов"""
        return len(self.watched_episodes)
    
    def build(self):
        """Построение UI списка эпизодов"""
        
        # Заголовок с информацией
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Эпизоды",
                        size=typography.text_lg,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"{self.get_watched_episodes_count()}/{self.get_total_episodes_count()}",
                            size=typography.text_sm,
                            color=colors.text_secondary,
                        ),
                        bgcolor=colors.surface,
                        border_radius=spacing.border_radius_sm,
                        padding=ft.padding.symmetric(
                            horizontal=spacing.sm,
                            vertical=spacing.xs
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            margin=ft.margin.only(bottom=spacing.md),
        )
        
        # Селектор сезонов
        self.season_selector = SeasonSelector(
            seasons_list=self.seasons_list,
            current_season=self.current_season,
            on_season_change=self._on_season_change
        )
        
        # Контейнер для списка эпизодов
        self.episodes_container = ft.Container(
            content=self._create_episodes_list(self.current_season),
            expand=True,
        )
        
        # Основная колонка
        main_column = ft.Column(
            controls=[
                header,
                self.season_selector,
                self.episodes_container,
            ],
            spacing=0,
            expand=True,
        )
        
        # Применяем ограничение высоты если задано
        if self.max_height:
            return ft.Container(
                content=main_column,
                height=self.max_height,
            )
        
        return main_column

# ===== КОМПАКТНАЯ ВЕРСИЯ =====

class CompactEpisodeList(AnimeEpisodeList):
    """Компактная версия списка эпизодов"""
    
    def __init__(self, **kwargs):
        super().__init__(compact_mode=True, **kwargs)

# ===== ЭКСПОРТ =====

__all__ = [
    "EpisodeItem", "SeasonSelector", "AnimeEpisodeList", "CompactEpisodeList"
]