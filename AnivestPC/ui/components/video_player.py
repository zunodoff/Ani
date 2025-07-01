"""
🎬 ANIVEST DESKTOP - ВИДЕО ПЛЕЕР
==============================
Компонент для просмотра аниме через Kodik iframe
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from urllib.parse import urlparse, parse_qs

from config.theme import colors, icons, spacing, typography, get_button_style
from core.database.database import db_manager

logger = logging.getLogger(__name__)

class VideoControls(ft.UserControl):
    """Кастомные элементы управления видео"""
    
    def __init__(
        self,
        on_play_pause: Optional[Callable] = None,
        on_fullscreen: Optional[Callable] = None,
        on_volume_change: Optional[Callable] = None,
        on_prev_episode: Optional[Callable] = None,
        on_next_episode: Optional[Callable] = None,
    ):
        super().__init__()
        
        self.on_play_pause = on_play_pause
        self.on_fullscreen = on_fullscreen
        self.on_volume_change = on_volume_change
        self.on_prev_episode = on_prev_episode
        self.on_next_episode = on_next_episode
        
        # Состояние
        self.is_playing = False
        self.is_fullscreen = False
        self.volume = 0.8
        self.current_time = 0
        self.duration = 0
        self.is_visible = True
        
        # UI элементы
        self.play_button = None
        self.fullscreen_button = None
        self.volume_slider = None
        self.progress_slider = None
        self.time_display = None
        
        # Таймер скрытия контролов
        self.hide_timer = None
    
    def _format_time(self, seconds: int) -> str:
        """Форматирование времени в MM:SS или HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def update_progress(self, current_time: int, duration: int):
        """Обновление прогресса воспроизведения"""
        self.current_time = current_time
        self.duration = duration
        
        if self.progress_slider and duration > 0:
            self.progress_slider.value = (current_time / duration) * 100
            self.progress_slider.update()
        
        if self.time_display:
            time_text = f"{self._format_time(current_time)} / {self._format_time(duration)}"
            self.time_display.value = time_text
            self.time_display.update()
    
    def show_controls(self):
        """Показать контролы"""
        self.is_visible = True
        self.visible = True
        if self.page:
            self.update()
        
        # Установить таймер скрытия
        if self.hide_timer:
            self.hide_timer.cancel()
        
        self.hide_timer = asyncio.create_task(self._auto_hide_controls())
    
    async def _auto_hide_controls(self):
        """Автоматическое скрытие контролов"""
        try:
            await asyncio.sleep(3.0)  # Скрыть через 3 секунды
            if self.is_playing:  # Скрывать только во время воспроизведения
                self.is_visible = False
                self.visible = False
                if self.page:
                    self.update()
        except asyncio.CancelledError:
            pass
    
    def build(self):
        """Построение UI контролов"""
        
        # Кнопка воспроизведения/паузы
        self.play_button = ft.IconButton(
            icon=icons.pause_circle if self.is_playing else icons.play_circle,
            icon_color=colors.text_primary,
            icon_size=spacing.icon_xl,
            tooltip="Пауза" if self.is_playing else "Воспроизвести",
            on_click=lambda e: self.on_play_pause() if self.on_play_pause else None,
        )
        
        # Кнопки переключения эпизодов
        prev_button = ft.IconButton(
            icon=icons.prev_track,
            icon_color=colors.text_primary,
            tooltip="Предыдущий эпизод",
            on_click=lambda e: self.on_prev_episode() if self.on_prev_episode else None,
        )
        
        next_button = ft.IconButton(
            icon=icons.next_track,
            icon_color=colors.text_primary,
            tooltip="Следующий эпизод",
            on_click=lambda e: self.on_next_episode() if self.on_next_episode else None,
        )
        
        # Слайдер прогресса
        self.progress_slider = ft.Slider(
            min=0,
            max=100,
            value=0,
            active_color=colors.primary,
            inactive_color=colors.border,
            thumb_color=colors.primary,
            on_change=self._on_seek,
            expand=True,
        )
        
        # Отображение времени
        self.time_display = ft.Text(
            "00:00 / 00:00",
            color=colors.text_primary,
            size=typography.text_sm,
        )
        
        # Слайдер громкости
        self.volume_slider = ft.Slider(
            min=0,
            max=1,
            value=self.volume,
            width=100,
            active_color=colors.primary,
            inactive_color=colors.border,
            thumb_color=colors.primary,
            on_change=self._on_volume_change,
        )
        
        # Кнопка полноэкранного режима
        self.fullscreen_button = ft.IconButton(
            icon=icons.fullscreen if not self.is_fullscreen else icons.fullscreen_exit,
            icon_color=colors.text_primary,
            tooltip="Полный экран" if not self.is_fullscreen else "Выйти из полного экрана",
            on_click=lambda e: self.on_fullscreen() if self.on_fullscreen else None,
        )
        
        # Верхняя панель с кнопками эпизодов
        top_controls = ft.Container(
            content=ft.Row(
                controls=[
                    prev_button,
                    next_button,
                    ft.Container(expand=True),  # Spacer
                    self.fullscreen_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=colors.background + "80",  # 50% прозрачность
            padding=spacing.sm,
            border_radius=spacing.border_radius_md,
        )
        
        # Нижняя панель с основными контролами
        bottom_controls = ft.Container(
            content=ft.Column(
                controls=[
                    # Прогресс-бар
                    ft.Container(
                        content=self.progress_slider,
                        padding=ft.padding.symmetric(horizontal=spacing.md),
                    ),
                    
                    # Основные контролы
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.play_button,
                                self.time_display,
                                ft.Container(expand=True),  # Spacer
                                ft.Icon(icons.volume_up, color=colors.text_primary, size=spacing.icon_sm),
                                self.volume_slider,
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=colors.background + "90",  # 90% прозрачность
            border_radius=spacing.border_radius_md,
        )
        
        return ft.Stack(
            controls=[
                # Верхние контролы
                ft.Container(
                    content=top_controls,
                    alignment=ft.alignment.top_center,
                    padding=spacing.md,
                ),
                
                # Нижние контролы
                ft.Container(
                    content=bottom_controls,
                    alignment=ft.alignment.bottom_center,
                    padding=spacing.md,
                ),
            ],
            expand=True,
        )
    
    def _on_seek(self, e):
        """Обработка перемотки"""
        if self.duration > 0:
            seek_time = int((e.control.value / 100) * self.duration)
            # TODO: Отправить команду перемотки в iframe
            logger.info(f"Seek to: {seek_time}s")
    
    def _on_volume_change(self, e):
        """Обработка изменения громкости"""
        self.volume = e.control.value
        if self.on_volume_change:
            self.on_volume_change(self.volume)
        logger.info(f"Volume: {self.volume}")
    
    def set_playing_state(self, is_playing: bool):
        """Установка состояния воспроизведения"""
        self.is_playing = is_playing
        if self.play_button:
            self.play_button.icon = icons.pause_circle if is_playing else icons.play_circle
            self.play_button.tooltip = "Пауза" if is_playing else "Воспроизвести"
            self.play_button.update()
    
    def set_fullscreen_state(self, is_fullscreen: bool):
        """Установка состояния полного экрана"""
        self.is_fullscreen = is_fullscreen
        if self.fullscreen_button:
            self.fullscreen_button.icon = icons.fullscreen_exit if is_fullscreen else icons.fullscreen
            self.fullscreen_button.tooltip = "Выйти из полного экрана" if is_fullscreen else "Полный экран"
            self.fullscreen_button.update()

class AnimeVideoPlayer(ft.UserControl):
    """Видео плеер для просмотра аниме"""
    
    def __init__(
        self,
        anime_data: Dict[str, Any],
        width: int = 800,
        height: int = 450,
        current_user: Optional[Dict] = None,
        on_episode_change: Optional[Callable] = None,
        on_progress_update: Optional[Callable] = None,
        show_controls: bool = True,
    ):
        super().__init__()
        
        self.anime_data = anime_data
        self.width = width
        self.height = height
        self.current_user = current_user
        self.on_episode_change = on_episode_change
        self.on_progress_update = on_progress_update
        self.show_controls = show_controls
        
        # Состояние просмотра
        self.current_season = 1
        self.current_episode = 1
        self.episodes_list = []
        self.is_loading = True
        self.error_message = None
        
        # Получаем данные
        self.anime_id = anime_data.get('id', '')
        self.kodik_id = anime_data.get('kodik_id')
        self.video_link = anime_data.get('link')
        self.title = anime_data.get('material_data', {}).get('title', 'Неизвестное аниме')
        
        # UI элементы
        self.video_container = None
        self.loading_indicator = None
        self.error_container = None
        self.controls = None
        
        # Инициализация
        if self.kodik_id or self.video_link:
            asyncio.create_task(self._load_episodes())
    
    async def _load_episodes(self):
        """Загрузка списка эпизодов"""
        try:
            self.is_loading = True
            await self._update_loading_state()
            
            if self.kodik_id:
                from core.api.anime_service import anime_service
                self.episodes_list = await anime_service.get_anime_episodes(
                    self.anime_id, 
                    self.kodik_id
                )
            
            if not self.episodes_list and self.video_link:
                # Если нет списка эпизодов, создаем один эпизод
                self.episodes_list = [{
                    'season': 1,
                    'episode': 1,
                    'title': 'Эпизод 1',
                    'link': self.video_link
                }]
            
            self.is_loading = False
            await self._load_current_video()
            
        except Exception as e:
            logger.error(f"Ошибка загрузки эпизодов: {e}")
            self.error_message = f"Ошибка загрузки: {e}"
            self.is_loading = False
            await self._update_loading_state()
    
    async def _load_current_video(self):
        """Загрузка текущего видео"""
        try:
            current_ep = self._get_current_episode_data()
            if current_ep and current_ep.get('link'):
                self.video_link = current_ep['link']
                await self._update_video_player()
                
                # Сохраняем прогресс просмотра
                if self.current_user:
                    self._save_watch_progress()
            else:
                self.error_message = "Видео недоступно"
                await self._update_loading_state()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки видео: {e}")
            self.error_message = f"Ошибка загрузки видео: {e}"
            await self._update_loading_state()
    
    def _get_current_episode_data(self) -> Optional[Dict]:
        """Получение данных текущего эпизода"""
        for episode in self.episodes_list:
            if (episode.get('season') == self.current_season and 
                episode.get('episode') == self.current_episode):
                return episode
        return None
    
    def _save_watch_progress(self):
        """Сохранение прогресса просмотра"""
        try:
            if self.current_user:
                material_data = self.anime_data.get('material_data', {})
                
                db_manager.update_watch_progress(
                    user_id=self.current_user['id'],
                    anime_id=self.anime_id,
                    anime_title=self.title,
                    anime_poster_url=material_data.get('poster_url', ''),
                    episode_number=self.current_episode,
                    season_number=self.current_season,
                    watch_time_seconds=0,  # TODO: Получать реальное время из плеера
                    total_time_seconds=0   # TODO: Получать реальную длительность
                )
                
                if self.on_progress_update:
                    asyncio.create_task(self.on_progress_update(
                        self.current_season, 
                        self.current_episode
                    ))
                    
        except Exception as e:
            logger.error(f"Ошибка сохранения прогресса: {e}")
    
    async def _update_loading_state(self):
        """Обновление состояния загрузки"""
        if self.loading_indicator:
            self.loading_indicator.visible = self.is_loading
            self.loading_indicator.update()
        
        if self.error_container:
            self.error_container.visible = bool(self.error_message)
            if self.error_message:
                # Обновляем текст ошибки
                error_text = self.error_container.content.controls[1]  # Второй элемент - текст
                error_text.value = self.error_message
            self.error_container.update()
    
    async def _update_video_player(self):
        """Обновление видео плеера"""
        if self.video_container and self.video_link:
            # Создаем новый WebView с видео
            web_view = ft.WebView(
                url=self.video_link,
                expand=True,
                on_page_started=self._on_video_started,
                on_page_ended=self._on_video_loaded,
            )
            
            self.video_container.content = web_view
            self.video_container.update()
            
            # Скрываем загрузку
            await self._update_loading_state()
    
    def _on_video_started(self, e):
        """Обработка начала загрузки видео"""
        logger.info("Видео начало загружаться")
    
    def _on_video_loaded(self, e):
        """Обработка завершения загрузки видео"""
        logger.info("Видео загружено")
        asyncio.create_task(self._update_loading_state())
    
    async def _change_episode(self, season: int, episode: int):
        """Смена эпизода"""
        try:
            # Проверяем доступность эпизода
            episode_data = None
            for ep in self.episodes_list:
                if ep.get('season') == season and ep.get('episode') == episode:
                    episode_data = ep
                    break
            
            if not episode_data:
                logger.warning(f"Эпизод S{season}E{episode} не найден")
                return
            
            self.current_season = season
            self.current_episode = episode
            
            # Показываем загрузку
            self.is_loading = True
            self.error_message = None
            await self._update_loading_state()
            
            # Загружаем новое видео
            await self._load_current_video()
            
            # Вызываем callback
            if self.on_episode_change:
                await self.on_episode_change(season, episode)
                
        except Exception as e:
            logger.error(f"Ошибка смены эпизода: {e}")
            self.error_message = f"Ошибка смены эпизода: {e}"
            self.is_loading = False
            await self._update_loading_state()
    
    async def next_episode(self):
        """Переход к следующему эпизоду"""
        next_ep = None
        
        # Ищем следующий эпизод
        for episode in self.episodes_list:
            if (episode.get('season') == self.current_season and 
                episode.get('episode') == self.current_episode + 1):
                next_ep = episode
                break
        
        # Если в текущем сезоне нет следующего, ищем в следующем сезоне
        if not next_ep:
            for episode in self.episodes_list:
                if (episode.get('season') == self.current_season + 1 and 
                    episode.get('episode') == 1):
                    next_ep = episode
                    break
        
        if next_ep:
            await self._change_episode(next_ep['season'], next_ep['episode'])
        else:
            logger.info("Следующий эпизод недоступен")
    
    async def prev_episode(self):
        """Переход к предыдущему эпизоду"""
        prev_ep = None
        
        # Ищем предыдущий эпизод
        if self.current_episode > 1:
            for episode in self.episodes_list:
                if (episode.get('season') == self.current_season and 
                    episode.get('episode') == self.current_episode - 1):
                    prev_ep = episode
                    break
        else:
            # Ищем последний эпизод предыдущего сезона
            max_episode = 0
            for episode in self.episodes_list:
                if episode.get('season') == self.current_season - 1:
                    max_episode = max(max_episode, episode.get('episode', 0))
            
            if max_episode > 0:
                for episode in self.episodes_list:
                    if (episode.get('season') == self.current_season - 1 and 
                        episode.get('episode') == max_episode):
                        prev_ep = episode
                        break
        
        if prev_ep:
            await self._change_episode(prev_ep['season'], prev_ep['episode'])
        else:
            logger.info("Предыдущий эпизод недоступен")
    
    def set_episode(self, season: int, episode: int):
        """Установка конкретного эпизода"""
        asyncio.create_task(self._change_episode(season, episode))
    
    def get_episodes_list(self) -> List[Dict]:
        """Получение списка всех эпизодов"""
        return self.episodes_list
    
    def get_current_episode(self) -> tuple[int, int]:
        """Получение текущего сезона и эпизода"""
        return self.current_season, self.current_episode
    
    def build(self):
        """Построение UI видео плеера"""
        
        # Контейнер для видео
        self.video_container = ft.Container(
            content=ft.Container(
                content=ft.Text(
                    "Инициализация плеера...",
                    color=colors.text_muted,
                    size=typography.text_lg,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.alignment.center,
                bgcolor=colors.background,
            ),
            width=self.width,
            height=self.height,
            border_radius=spacing.border_radius_lg,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=colors.background,
        )
        
        # Индикатор загрузки
        self.loading_indicator = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=48,
                        height=48,
                        color=colors.primary,
                    ),
                    ft.Text(
                        "Загрузка видео...",
                        color=colors.text_primary,
                        size=typography.text_lg,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=spacing.md,
            ),
            alignment=ft.alignment.center,
            bgcolor=colors.background + "CC",  # 80% прозрачность
            visible=self.is_loading,
        )
        
        # Контейнер ошибки
        self.error_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icons.error,
                        size=48,
                        color=colors.error,
                    ),
                    ft.Text(
                        self.error_message or "Произошла ошибка",
                        color=colors.error,
                        size=typography.text_lg,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.ElevatedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(icons.refresh, size=spacing.icon_sm),
                                ft.Text("Перезагрузить"),
                            ],
                            spacing=spacing.xs,
                            tight=True,
                        ),
                        bgcolor=colors.primary,
                        color=colors.text_primary,
                        on_click=lambda e: asyncio.create_task(self._load_episodes()),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=spacing.md,
            ),
            alignment=ft.alignment.center,
            bgcolor=colors.background + "CC",  # 80% прозрачность
            visible=bool(self.error_message),
        )
        
        # Контролы видео
        self.controls = VideoControls(
            on_prev_episode=lambda: asyncio.create_task(self.prev_episode()),
            on_next_episode=lambda: asyncio.create_task(self.next_episode()),
        ) if self.show_controls else None
        
        # Основной стек с видео и контролами
        video_stack = ft.Stack(
            controls=[
                # Видео контейнер
                self.video_container,
                
                # Индикатор загрузки
                self.loading_indicator,
                
                # Контейнер ошибки
                self.error_container,
                
                # Контролы (если включены)
                self.controls if self.controls else ft.Container(),
            ],
            width=self.width,
            height=self.height,
        )
        
        # Информация о текущем эпизоде
        episode_info = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        f"{self.title}",
                        size=typography.text_lg,
                        weight=typography.weight_semibold,
                        color=colors.text_primary,
                        expand=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"S{self.current_season}E{self.current_episode}",
                            size=typography.text_md,
                            color=colors.text_primary,
                            weight=typography.weight_medium,
                        ),
                        bgcolor=colors.primary,
                        border_radius=spacing.border_radius_sm,
                        padding=ft.padding.symmetric(
                            horizontal=spacing.sm,
                            vertical=spacing.xs
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_md,
            padding=spacing.md,
            margin=ft.margin.only(bottom=spacing.sm),
        )
        
        return ft.Column(
            controls=[
                episode_info,
                video_stack,
            ],
            spacing=0,
            width=self.width,
        )

# ===== МИНИ ПЛЕЕР =====

class MiniVideoPlayer(AnimeVideoPlayer):
    """Компактная версия видео плеера"""
    
    def __init__(self, **kwargs):
        super().__init__(
            width=400,
            height=225,
            show_controls=False,
            **kwargs
        )

# ===== ЭКСПОРТ =====

__all__ = [
    "VideoControls", "AnimeVideoPlayer", "MiniVideoPlayer"
]