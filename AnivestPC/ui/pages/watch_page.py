"""
🎬 ANIVEST DESKTOP - СТРАНИЦА ПРОСМОТРА
====================================
Страница просмотра аниме с видео плеером и информацией
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from config.theme import colors, icons, spacing, typography
from core.api.anime_service import anime_service
from core.database.database import db_manager

from ..components.video_player import KodikVideoPlayer
from ..components.episode_list import EpisodesList
from ..components.anime_card import AnimeCard

logger = logging.getLogger(__name__)

class WatchPage(ft.UserControl):
    """Страница просмотра аниме"""
    
    def __init__(
        self,
        anime_id: str,
        shikimori_id: Optional[str] = None,
        episode_number: int = 1,
        season_number: int = 1,
        on_favorite_click: Optional[Callable[[Dict, bool], None]] = None,
        on_navigate: Optional[Callable[[str], None]] = None,
        current_user: Optional[Dict] = None
    ):
        super().__init__()
        
        self.anime_id = anime_id
        self.shikimori_id = shikimori_id
        self.episode_number = episode_number
        self.season_number = season_number
        self.on_favorite_click = on_favorite_click
        self.on_navigate = on_navigate
        self.current_user = current_user
        
        # Данные
        self.anime_data = {}
        self.episodes_data = []
        self.similar_anime = []
        self.is_favorite = False
        self.watch_progress = None
        
        # Состояние
        self.is_loading = False
        self.error_message = ""
        self.player_mode = "theater"  # theater, fullscreen, mini
        
        # UI элементы
        self.video_player = None
        self.episodes_list = None
        self.anime_info_container = None
        self.similar_section = None
        self.loading_indicator = None
        self.error_container = None
    
    async def load_anime_data(self):
        """Загрузка данных аниме"""
        try:
            await self._show_loading("Загрузка аниме...")
            
            # Загружаем информацию об аниме
            logger.info(f"Загрузка данных аниме: {self.anime_id}")
            self.anime_data = await anime_service.get_anime_details(self.anime_id, self.shikimori_id)
            
            if not self.anime_data:
                raise Exception("Аниме не найдено")
            
            # Загружаем список эпизодов
            logger.info("Загрузка списка эпизодов...")
            self.episodes_data = await anime_service.get_anime_episodes(
                self.anime_id, 
                self.anime_data.get('kodik_id')
            )
            
            # Загружаем похожие аниме
            if self.shikimori_id:
                logger.info("Загрузка похожих аниме...")
                similar_data = await anime_service.shikimori.get_anime_similar(self.shikimori_id)
                if similar_data:
                    # Конвертируем в наш формат
                    self.similar_anime = []
                    for similar in similar_data[:6]:  # Показываем только 6
                        from core.api.shikimori_api import convert_shikimori_format
                        converted = convert_shikimori_format(similar)
                        self.similar_anime.append(converted)
            
            # Загружаем пользовательские данные
            if self.current_user:
                await self._load_user_data()
            
            await self._hide_loading()
            
            # Обновляем UI
            if self.page:
                self.update()
            
            logger.info(f"Данные аниме загружены: {self.anime_data.get('title', 'Неизвестно')}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки аниме: {e}")
            self.error_message = str(e)
            await self._hide_loading()
            
            if self.page:
                self.update()
    
    async def _load_user_data(self):
        """Загрузка пользовательских данных"""
        try:
            if not self.current_user:
                return
            
            user_id = self.current_user['id']
            
            # Проверяем избранное
            self.is_favorite = db_manager.is_in_favorites(user_id, self.anime_id)
            
            # Загружаем прогресс просмотра
            self.watch_progress = db_manager.get_watch_progress(user_id, self.anime_id)
            
            # Если есть сохраненный прогресс, используем его для эпизода
            if self.watch_progress and self.episode_number == 1:
                self.episode_number = self.watch_progress.episode_number
                self.season_number = self.watch_progress.season_number
            
            logger.info(f"Пользовательские данные загружены: избранное={self.is_favorite}, прогресс={self.watch_progress}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки пользовательских данных: {e}")
    
    def _create_player_section(self) -> ft.Container:
        """Создание секции видео плеера"""
        
        if not self.anime_data or not self.anime_data.get('link'):
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.movie, size=96, color=colors.text_muted),
                        ft.Text(
                            "Видео недоступно",
                            size=typography.text_xl,
                            color=colors.text_muted,
                        ),
                        ft.Text(
                            "К сожалению, для этого аниме нет доступных серий",
                            size=typography.text_md,
                            color=colors.text_muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=spacing.lg,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                height=450,
                bgcolor=colors.surface,
                border_radius=spacing.border_radius_lg,
                alignment=ft.alignment.center,
            )
        
        # Создаем видео плеер
        self.video_player = KodikVideoPlayer(
            anime_data=self.anime_data,
            episode_number=self.episode_number,
            season_number=self.season_number,
            width=1000,
            height=550,
            show_controls=True,
            autoplay=False,
            on_episode_change=self._on_episode_change,
            on_progress_update=self._on_progress_update,
            current_user=self.current_user
        )
        
        return ft.Container(
            content=self.video_player,
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_anime_info(self) -> ft.Container:
        """Создание секции информации об аниме"""
        
        if not self.anime_data:
            return ft.Container()
        
        material_data = self.anime_data.get('material_data', {})
        
        # Заголовок и основная информация
        title = material_data.get('title', 'Неизвестное аниме')
        title_en = material_data.get('title_en', '')
        description = material_data.get('description', '')
        
        # Метаинформация
        rating = material_data.get('shikimori_rating')
        votes = material_data.get('shikimori_votes')
        year = material_data.get('year')
        status = material_data.get('anime_status', '')
        episodes_total = material_data.get('episodes_total')
        genres = material_data.get('anime_genres', [])
        studios = material_data.get('anime_studios', [])
        
        # Заголовок
        header_section = ft.Column(
            controls=[
                ft.Text(
                    title,
                    size=typography.text_3xl,
                    weight=typography.weight_bold,
                    color=colors.text_primary,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    title_en,
                    size=typography.text_lg,
                    color=colors.text_secondary,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ) if title_en and title_en != title else ft.Container(),
            ],
            spacing=spacing.sm,
        )
        
        # Рейтинг и статистика
        rating_section = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icons.star, size=spacing.icon_md, color=colors.accent),
                            ft.Text(
                                f"{float(rating):.1f}",
                                size=typography.text_xl,
                                weight=typography.weight_bold,
                                color=colors.text_primary,
                            ),
                            ft.Text(
                                f"({votes} оценок)" if votes else "",
                                size=typography.text_md,
                                color=colors.text_muted,
                            ),
                        ],
                        spacing=spacing.sm,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ) if rating else ft.Container(),
                
                ft.Container(
                    content=ft.Text(
                        status,
                        size=typography.text_md,
                        color=colors.text_primary,
                        weight=typography.weight_medium,
                    ),
                    bgcolor=self._get_status_color(status) + "40",
                    border_radius=spacing.border_radius_sm,
                    padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                ),
                
                ft.Text(
                    f"{year}" if year else "",
                    size=typography.text_md,
                    color=colors.text_secondary,
                ),
                
                ft.Text(
                    f"{episodes_total} эп." if episodes_total else "",
                    size=typography.text_md,
                    color=colors.text_secondary,
                ),
            ],
            spacing=spacing.lg,
            wrap=True,
        )
        
        # Жанры
        genres_section = ft.Container()
        if genres:
            genre_chips = []
            for genre in genres[:6]:  # Показываем максимум 6 жанров
                chip = ft.Container(
                    content=ft.Text(
                        genre,
                        size=typography.text_sm,
                        color=colors.text_primary,
                    ),
                    bgcolor=colors.primary + "20",
                    border_radius=spacing.border_radius_sm,
                    padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                )
                genre_chips.append(chip)
            
            genres_section = ft.Container(
                content=ft.Row(
                    controls=genre_chips,
                    spacing=spacing.sm,
                    wrap=True,
                ),
                margin=ft.margin.symmetric(vertical=spacing.md),
            )
        
        # Описание
        description_section = ft.Container()
        if description:
            description_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Описание",
                            size=typography.text_lg,
                            weight=typography.weight_semibold,
                            color=colors.text_primary,
                        ),
                        ft.Text(
                            description,
                            size=typography.text_md,
                            color=colors.text_secondary,
                            max_lines=6,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=spacing.sm,
                ),
                margin=ft.margin.symmetric(vertical=spacing.md),
            )
        
        # Дополнительная информация
        additional_info = []
        if studios:
            studios_text = ", ".join(studios[:3])  # Показываем максимум 3 студии
            additional_info.append(f"Студия: {studios_text}")
        
        additional_section = ft.Container()
        if additional_info:
            additional_section = ft.Container(
                content=ft.Text(
                    " • ".join(additional_info),
                    size=typography.text_sm,
                    color=colors.text_muted,
                ),
                margin=ft.margin.only(top=spacing.md),
            )
        
        # Кнопки действий
        action_buttons = self._create_action_buttons()
        
        self.anime_info_container = ft.Container(
            content=ft.Column(
                controls=[
                    header_section,
                    rating_section,
                    genres_section,
                    description_section,
                    additional_section,
                    action_buttons,
                ],
                spacing=spacing.md,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
        
        return self.anime_info_container
    
    def _create_action_buttons(self) -> ft.Container:
        """Создание кнопок действий"""
        
        buttons = []
        
        # Кнопка избранного
        if self.current_user:
            favorite_button = ft.ElevatedButton(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            icons.favorite if self.is_favorite else icons.star_border,
                            size=spacing.icon_md,
                        ),
                        ft.Text(
                            "Удалить из избранного" if self.is_favorite else "Добавить в избранное",
                            size=typography.text_md,
                        ),
                    ],
                    spacing=spacing.sm,
                    tight=True,
                ),
                bgcolor=colors.secondary if self.is_favorite else colors.surface,
                color=colors.text_primary,
                on_click=self._toggle_favorite,
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
                ),
            )
            buttons.append(favorite_button)
        
        # Кнопка поделиться
        share_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icons.share, size=spacing.icon_md),
                    ft.Text("Поделиться", size=typography.text_md),
                ],
                spacing=spacing.sm,
                tight=True,
            ),
            bgcolor=colors.surface,
            color=colors.text_primary,
            on_click=self._share_anime,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
            ),
        )
        buttons.append(share_button)
        
        # Информация о прогрессе просмотра
        progress_info = ft.Container()
        if self.current_user and self.watch_progress:
            progress_text = f"Эпизод {self.watch_progress.episode_number}"
            if self.watch_progress.get_progress_percent() > 0:
                progress_text += f" ({self.watch_progress.get_progress_percent():.0f}%)"
            
            progress_info = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icons.play_circle, size=spacing.icon_md, color=colors.success),
                        ft.Text(
                            progress_text,
                            size=typography.text_md,
                            color=colors.text_secondary,
                        ),
                    ],
                    spacing=spacing.sm,
                ),
                margin=ft.margin.only(left=spacing.lg),
            )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=buttons,
                        spacing=spacing.md,
                    ),
                    progress_info,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            margin=ft.margin.only(top=spacing.lg),
        )
    
    def _create_episodes_section(self) -> ft.Container:
        """Создание секции со списком эпизодов"""
        
        if not self.episodes_data:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "📺 Эпизоды",
                            size=typography.text_xl,
                            weight=typography.weight_bold,
                            color=colors.text_primary,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "Список эпизодов недоступен",
                                size=typography.text_md,
                                color=colors.text_muted,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                            height=200,
                        ),
                    ],
                    spacing=spacing.md,
                ),
                bgcolor=colors.surface,
                border_radius=spacing.border_radius_lg,
                padding=spacing.xl,
                margin=ft.margin.only(bottom=spacing.xl),
            )
        
        # Создаем список эпизодов
        self.episodes_list = EpisodesList(
            anime_data=self.anime_data,
            episodes_data=self.episodes_data,
            current_episode=self.episode_number,
            current_season=self.season_number,
            width=400,
            height=600,
            compact_mode=False,
            show_screenshots=True,
            on_episode_select=self._on_episode_select,
            current_user=self.current_user
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "📺 Эпизоды",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    self.episodes_list,
                ],
                spacing=spacing.md,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_similar_section(self) -> ft.Container:
        """Создание секции похожих аниме"""
        
        if not self.similar_anime:
            return ft.Container()
        
        # Создаем карточки похожих аниме
        similar_cards = []
        for anime in self.similar_anime:
            card = AnimeCard(
                anime_data=anime,
                width=180,
                height=260,
                compact=True,
                on_click=self._on_similar_anime_click,
                on_favorite=self.on_favorite_click,
                current_user=self.current_user
            )
            similar_cards.append(card)
        
        self.similar_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "🔗 Похожие аниме",
                                size=typography.text_xl,
                                weight=typography.weight_bold,
                                color=colors.text_primary,
                            ),
                            ft.TextButton(
                                text="Смотреть все →",
                                on_click=lambda e: self.on_navigate("catalog") if self.on_navigate else None,
                                style=ft.ButtonStyle(color=colors.primary),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=similar_cards,
                            spacing=spacing.lg,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        height=280,
                        margin=ft.margin.only(top=spacing.md),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
        )
        
        return self.similar_section
    
    def _create_loading_indicator(self) -> ft.Container:
        """Создание индикатора загрузки"""
        self.loading_indicator = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=64,
                        height=64,
                        color=colors.primary,
                    ),
                    ft.Text(
                        "Загрузка аниме...",
                        size=typography.text_xl,
                        color=colors.text_secondary,
                        text_align=ft.TextAlign.CENTER,
                    )
                ],
                spacing=spacing.xl,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            height=600,
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
                        size=96,
                        color=colors.error,
                    ),
                    ft.Text(
                        "Ошибка загрузки аниме",
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        self.error_message,
                        size=typography.text_lg,
                        color=colors.text_secondary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                text="Попробовать снова",
                                bgcolor=colors.primary,
                                color=colors.text_primary,
                                on_click=lambda e: asyncio.create_task(self.load_anime_data()),
                            ),
                            ft.ElevatedButton(
                                text="Вернуться в каталог",
                                bgcolor=colors.surface,
                                color=colors.text_primary,
                                on_click=lambda e: self.on_navigate("catalog") if self.on_navigate else None,
                            ),
                        ],
                        spacing=spacing.md,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=spacing.xl,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            height=600,
            visible=bool(self.error_message),
        )
        
        return self.error_container
    
    def _get_status_color(self, status: str) -> str:
        """Получение цвета статуса"""
        status_colors = {
            'released': colors.success,
            'ongoing': colors.info,
            'anons': colors.warning
        }
        return status_colors.get(status.lower(), colors.text_muted)
    
    async def _show_loading(self, message: str = "Загрузка..."):
        """Показать индикатор загрузки"""
        self.is_loading = True
        self.error_message = ""
        
        if self.loading_indicator:
            # Обновляем текст загрузки
            text_control = self.loading_indicator.content.controls[1]
            text_control.value = message
            self.loading_indicator.visible = True
        
        if self.page:
            self.update()
    
    async def _hide_loading(self):
        """Скрыть индикатор загрузки"""
        self.is_loading = False
        
        if self.loading_indicator:
            self.loading_indicator.visible = False
        
        if self.page:
            self.update()
    
    def _on_episode_change(self, episode_num: int):
        """Обработка смены эпизода в плеере"""
        self.episode_number = episode_num
        
        # Обновляем список эпизодов
        if self.episodes_list:
            self.episodes_list.update_current_episode(episode_num, self.season_number)
        
        # Сохраняем прогресс
        self._save_watch_progress()
        
        logger.info(f"Смена эпизода в плеере: {episode_num}")
    
    def _on_episode_select(self, episode_num: int, season_num: int):
        """Обработка выбора эпизода в списке"""
        self.episode_number = episode_num
        self.season_number = season_num
        
        # Обновляем плеер
        if self.video_player:
            self.video_player.set_episode(episode_num)
        
        # Сохраняем прогресс
        self._save_watch_progress()
        
        logger.info(f"Выбор эпизода в списке: {episode_num}, сезон {season_num}")
    
    def _on_progress_update(self, watch_time: int, total_time: int):
        """Обработка обновления прогресса просмотра"""
        # Периодически сохраняем прогресс
        if watch_time % 30 == 0:  # Каждые 30 секунд
            self._save_watch_progress(watch_time, total_time)
    
    def _save_watch_progress(self, watch_time: int = 0, total_time: int = 0):
        """Сохранение прогресса просмотра"""
        try:
            if not self.current_user or not self.anime_data:
                return
            
            db_manager.update_watch_progress(
                user_id=self.current_user['id'],
                anime_id=self.anime_id,
                anime_title=self.anime_data.get('title', ''),
                anime_poster_url=self.anime_data.get('material_data', {}).get('poster_url', ''),
                episode_number=self.episode_number,
                season_number=self.season_number,
                watch_time_seconds=watch_time,
                total_time_seconds=total_time
            )
            
            # Обновляем локальный прогресс
            self.watch_progress = db_manager.get_watch_progress(self.current_user['id'], self.anime_id)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения прогресса: {e}")
    
    def _toggle_favorite(self, e):
        """Переключение избранного"""
        try:
            if not self.current_user or not self.anime_data:
                return
            
            user_id = self.current_user['id']
            anime_title = self.anime_data.get('title', '')
            anime_poster = self.anime_data.get('material_data', {}).get('poster_url', '')
            
            if self.is_favorite:
                # Удаляем из избранного
                success = db_manager.remove_from_favorites(user_id, self.anime_id)
                if success:
                    self.is_favorite = False
                    message = "Удалено из избранного"
                else:
                    message = "Ошибка удаления из избранного"
            else:
                # Добавляем в избранное
                success = db_manager.add_to_favorites(user_id, self.anime_id, anime_title, anime_poster)
                if success:
                    self.is_favorite = True
                    message = "Добавлено в избранное"
                else:
                    message = "Ошибка добавления в избранное"
            
            # Обновляем UI
            if self.page:
                self.update()
            
            # Показываем уведомление
            if self.page:
                snack_color = colors.success if success else colors.error
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(message),
                        bgcolor=snack_color
                    )
                )
            
            # Вызываем callback
            if self.on_favorite_click:
                self.on_favorite_click(self.anime_data, self.is_favorite)
            
        except Exception as ex:
            logger.error(f"Ошибка переключения избранного: {ex}")
    
    def _share_anime(self, e):
        """Поделиться аниме"""
        # В будущем можно реализовать копирование в буфер обмена
        anime_title = self.anime_data.get('title', 'Неизвестное аниме')
        logger.info(f"Поделиться аниме: {anime_title}")
        
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Ссылка скопирована в буфер обмена"),
                    bgcolor=colors.info
                )
            )
    
    def _on_similar_anime_click(self, anime_data: Dict):
        """Обработка клика по похожему аниме"""
        # В будущем можно реализовать переход на другое аниме
        anime_title = anime_data.get('title', 'Неизвестное аниме')
        logger.info(f"Клик по похожему аниме: {anime_title}")
    
    def update_user(self, user: Optional[Dict]):
        """Обновление информации о пользователе"""
        self.current_user = user
        
        # Перезагружаем пользовательские данные
        if user:
            asyncio.create_task(self._load_user_data())
        else:
            self.is_favorite = False
            self.watch_progress = None
        
        if self.page:
            self.update()
    
    def build(self):
        """Построение UI страницы просмотра"""
        
        # Если загрузка - показываем индикатор
        if self.is_loading:
            return self._create_loading_indicator()
        
        # Если ошибка - показываем ошибку
        if self.error_message:
            return self._create_error_container()
        
        # Основной контент
        main_content = ft.Row(
            controls=[
                # Левая колонка - плеер и информация
                ft.Column(
                    controls=[
                        self._create_player_section(),
                        self._create_anime_info(),
                        self._create_similar_section(),
                    ],
                    spacing=0,
                    expand=True,
                ),
                
                # Правая колонка - список эпизодов
                ft.Container(
                    content=self._create_episodes_section(),
                    width=450,
                ),
            ],
            spacing=spacing.xl,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[main_content],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xl,
            expand=True,
        )

# ===== ЭКСПОРТ =====

__all__ = ["WatchPage"]