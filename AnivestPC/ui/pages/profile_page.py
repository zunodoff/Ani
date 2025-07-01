"""
👤 ANIVEST DESKTOP - СТРАНИЦА ПРОФИЛЯ
===================================
Страница профиля пользователя с настройками и статистикой
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime, timedelta

from config.theme import colors, icons, spacing, typography
from core.database.database import db_manager

from ..components.anime_card import CompactAnimeCard

logger = logging.getLogger(__name__)

class ProfilePage(ft.UserControl):
    """Страница профиля пользователя"""
    
    def __init__(
        self,
        current_user: Optional[Dict] = None,
        on_anime_click: Optional[Callable[[Dict], None]] = None,
        on_favorite_click: Optional[Callable[[Dict, bool], None]] = None,
        on_logout: Optional[Callable] = None,
        on_navigate: Optional[Callable[[str], None]] = None
    ):
        super().__init__()
        
        self.current_user = current_user
        self.on_anime_click = on_anime_click
        self.on_favorite_click = on_favorite_click
        self.on_logout = on_logout
        self.on_navigate = on_navigate
        
        # Данные пользователя
        self.user_stats = {}
        self.recent_favorites = []
        self.watch_history = []
        self.user_achievements = []
        
        # Состояние
        self.is_loading = False
        self.is_editing = False
        
        # UI элементы
        self.profile_header = None
        self.stats_section = None
        self.activity_section = None
        self.edit_form = None
    
    async def load_user_data(self):
        """Загрузка данных пользователя"""
        try:
            if not self.current_user:
                return
            
            await self._show_loading()
            
            user_id = self.current_user['id']
            
            # Загружаем статистику
            favorites = db_manager.get_user_favorites(user_id)
            watch_history = db_manager.get_user_watch_history(user_id, limit=50)
            
            # Рассчитываем статистику
            self.user_stats = self._calculate_stats(favorites, watch_history)
            
            # Последние добавленные в избранное (для отображения)
            self.recent_favorites = favorites[:6]  # Показываем последние 6
            
            # История просмотра (последние)
            self.watch_history = watch_history[:10]  # Показываем последние 10
            
            # Достижения (простые)
            self.user_achievements = self._calculate_achievements(favorites, watch_history)
            
            await self._hide_loading()
            
            # Обновляем UI
            if self.page:
                self.update()
            
            logger.info(f"Данные профиля загружены для пользователя: {self.current_user.get('username')}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных профиля: {e}")
            await self._hide_loading()
    
    def _calculate_stats(self, favorites: List, watch_history: List) -> Dict[str, Any]:
        """Расчет статистики пользователя"""
        total_episodes = sum(h.episode_number for h in watch_history)
        completed_anime = len([h for h in watch_history if h.is_completed])
        
        # Время просмотра (примерное)
        estimated_hours = total_episodes * 0.4  # ~24 минуты на эпизод
        
        # Активность по дням
        activity_days = set()
        for history in watch_history:
            if history.last_watched:
                try:
                    watch_date = datetime.fromisoformat(history.last_watched).date()
                    activity_days.add(watch_date)
                except:
                    pass
        
        return {
            'favorites_count': len(favorites),
            'total_anime': len(watch_history),
            'completed_anime': completed_anime,
            'total_episodes': total_episodes,
            'estimated_hours': int(estimated_hours),
            'active_days': len(activity_days),
            'registration_date': self.current_user.get('created_at', ''),
        }
    
    def _calculate_achievements(self, favorites: List, watch_history: List) -> List[Dict]:
        """Расчет достижений пользователя"""
        achievements = []
        
        # Достижения по количеству аниме
        total_anime = len(watch_history)
        if total_anime >= 1:
            achievements.append({
                'title': 'Первые шаги',
                'description': 'Начали смотреть первое аниме',
                'icon': icons.star,
                'color': colors.success,
                'unlocked': True
            })
        
        if total_anime >= 10:
            achievements.append({
                'title': 'Любитель аниме',
                'description': 'Посмотрели 10 аниме',
                'icon': icons.favorite,
                'color': colors.primary,
                'unlocked': True
            })
        
        if total_anime >= 50:
            achievements.append({
                'title': 'Настоящий отаку',
                'description': 'Посмотрели 50 аниме',
                'icon': icons.trending_up,
                'color': colors.secondary,
                'unlocked': True
            })
        
        # Достижения по избранному
        favorites_count = len(favorites)
        if favorites_count >= 5:
            achievements.append({
                'title': 'Коллекционер',
                'description': 'Добавили 5 аниме в избранное',
                'icon': icons.star_border,
                'color': colors.accent,
                'unlocked': True
            })
        
        # Достижения по эпизодам
        total_episodes = sum(h.episode_number for h in watch_history)
        if total_episodes >= 100:
            achievements.append({
                'title': 'Марафонец',
                'description': 'Посмотрели 100 эпизодов',
                'icon': icons.play_circle,
                'color': colors.info,
                'unlocked': True
            })
        
        return achievements
    
    def _create_profile_header(self) -> ft.Container:
        """Создание заголовка профиля"""
        if not self.current_user:
            return ft.Container()
        
        username = self.current_user.get('username', 'Пользователь')
        email = self.current_user.get('email', '')
        role = self.current_user.get('role', 'user')
        created_at = self.current_user.get('created_at', '')
        
        # Аватар пользователя
        avatar = ft.Container(
            content=ft.Text(
                username[0].upper(),
                size=typography.text_4xl,
                weight=typography.weight_bold,
                color=colors.text_primary,
                text_align=ft.TextAlign.CENTER,
            ),
            width=120,
            height=120,
            bgcolor=colors.primary,
            border_radius=60,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(0, 8)
            ),
        )
        
        # Информация о пользователе
        user_info = ft.Column(
            controls=[
                ft.Text(
                    username,
                    size=typography.text_3xl,
                    weight=typography.weight_bold,
                    color=colors.text_primary,
                ),
                ft.Text(
                    email,
                    size=typography.text_lg,
                    color=colors.text_secondary,
                ),
                ft.Container(
                    content=ft.Text(
                        role.upper(),
                        size=typography.text_sm,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    bgcolor=colors.secondary + "40",
                    border_radius=spacing.border_radius_sm,
                    padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                ),
                ft.Text(
                    f"Регистрация: {self._format_date(created_at)}" if created_at else "",
                    size=typography.text_sm,
                    color=colors.text_muted,
                ),
            ],
            spacing=spacing.sm,
            expand=True,
        )
        
        # Кнопки действий
        action_buttons = ft.Column(
            controls=[
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icons.settings, size=spacing.icon_sm),
                            ft.Text("Редактировать", size=typography.text_sm),
                        ],
                        spacing=spacing.xs,
                        tight=True,
                    ),
                    bgcolor=colors.primary,
                    color=colors.text_primary,
                    on_click=self._toggle_edit_mode,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                    ),
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icons.logout, size=spacing.icon_sm),
                            ft.Text("Выйти", size=typography.text_sm),
                        ],
                        spacing=spacing.xs,
                        tight=True,
                    ),
                    bgcolor=colors.error,
                    color=colors.text_primary,
                    on_click=self._logout,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                    ),
                ),
            ],
            spacing=spacing.sm,
            horizontal_alignment=ft.CrossAxisAlignment.END,
        )
        
        self.profile_header = ft.Container(
            content=ft.Row(
                controls=[
                    avatar,
                    ft.Container(width=spacing.xl),  # Отступ
                    user_info,
                    action_buttons,
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(0, 8)
            ),
        )
        
        return self.profile_header
    
    def _create_stats_section(self) -> ft.Container:
        """Создание секции статистики"""
        
        if not self.user_stats:
            return ft.Container()
        
        # Основные статистики
        main_stats = [
            {
                'title': 'Избранное',
                'value': self.user_stats.get('favorites_count', 0),
                'icon': icons.favorite,
                'color': colors.secondary,
                'description': 'аниме в избранном'
            },
            {
                'title': 'Просмотрено',
                'value': self.user_stats.get('total_anime', 0),
                'icon': icons.movie,
                'color': colors.primary,
                'description': 'аниме в истории'
            },
            {
                'title': 'Завершено',
                'value': self.user_stats.get('completed_anime', 0),
                'icon': icons.check_circle,
                'color': colors.success,
                'description': 'полностью просмотрено'
            },
            {
                'title': 'Эпизодов',
                'value': self.user_stats.get('total_episodes', 0),
                'icon': icons.play_circle,
                'color': colors.info,
                'description': 'эпизодов просмотрено'
            },
        ]
        
        # Дополнительные статистики
        additional_stats = [
            {
                'title': 'Время просмотра',
                'value': f"~{self.user_stats.get('estimated_hours', 0)} ч",
                'description': 'приблизительное время'
            },
            {
                'title': 'Активных дней',
                'value': self.user_stats.get('active_days', 0),
                'description': 'дней с активностью'
            },
        ]
        
        # Создаем карточки основной статистики
        main_stat_cards = []
        for stat in main_stats:
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            stat['icon'],
                            size=32,
                            color=stat['color'],
                        ),
                        ft.Text(
                            str(stat['value']),
                            size=typography.text_3xl,
                            weight=typography.weight_bold,
                            color=colors.text_primary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            stat['title'],
                            size=typography.text_md,
                            weight=typography.weight_semibold,
                            color=colors.text_secondary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            stat['description'],
                            size=typography.text_sm,
                            color=colors.text_muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=spacing.sm,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                width=160,
                height=140,
                bgcolor=colors.card,
                border_radius=spacing.border_radius_lg,
                padding=spacing.md,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=colors.shadow,
                    offset=ft.Offset(0, 4)
                ),
            )
            main_stat_cards.append(card)
        
        # Дополнительная статистика
        additional_stats_widgets = []
        for stat in additional_stats:
            widget = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            stat['title'],
                            size=typography.text_md,
                            color=colors.text_secondary,
                            expand=True,
                        ),
                        ft.Text(
                            str(stat['value']),
                            size=typography.text_lg,
                            weight=typography.weight_semibold,
                            color=colors.text_primary,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=colors.surface_light,
                border_radius=spacing.border_radius_md,
                padding=spacing.md,
            )
            additional_stats_widgets.append(widget)
        
        self.stats_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "📊 Статистика",
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=main_stat_cards,
                            spacing=spacing.lg,
                            alignment=ft.MainAxisAlignment.CENTER,
                            wrap=True,
                        ),
                        margin=ft.margin.symmetric(vertical=spacing.lg),
                    ),
                    ft.Column(
                        controls=additional_stats_widgets,
                        spacing=spacing.sm,
                    ),
                ],
                spacing=spacing.md,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
        
        return self.stats_section
    
    def _create_achievements_section(self) -> ft.Container:
        """Создание секции достижений"""
        
        if not self.user_achievements:
            return ft.Container()
        
        achievement_cards = []
        for achievement in self.user_achievements:
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(
                                achievement['icon'],
                                size=24,
                                color=achievement['color'],
                            ),
                            width=40,
                            height=40,
                            bgcolor=achievement['color'] + "20",
                            border_radius=20,
                            alignment=ft.alignment.center,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    achievement['title'],
                                    size=typography.text_md,
                                    weight=typography.weight_semibold,
                                    color=colors.text_primary,
                                ),
                                ft.Text(
                                    achievement['description'],
                                    size=typography.text_sm,
                                    color=colors.text_secondary,
                                ),
                            ],
                            spacing=spacing.xs,
                            expand=True,
                        ),
                        ft.Icon(
                            icons.check_circle,
                            size=spacing.icon_md,
                            color=colors.success,
                        ),
                    ],
                    spacing=spacing.md,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=colors.card,
                border_radius=spacing.border_radius_md,
                padding=spacing.md,
                margin=ft.margin.only(bottom=spacing.sm),
            )
            achievement_cards.append(card)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "🏆 Достижения",
                        size=typography.text_2xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    ft.Column(
                        controls=achievement_cards,
                        spacing=0,
                    ),
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_activity_section(self) -> ft.Container:
        """Создание секции активности"""
        
        # Последние добавленные в избранное
        favorites_section = ft.Container()
        if self.recent_favorites:
            favorite_cards = []
            for favorite in self.recent_favorites:
                anime_data = {
                    'id': favorite.anime_id,
                    'title': favorite.anime_title,
                    'material_data': {
                        'title': favorite.anime_title,
                        'poster_url': favorite.anime_poster_url or 'https://via.placeholder.com/300x400/8B5CF6/FFFFFF?text=Нет+постера',
                    }
                }
                
                card = CompactAnimeCard(
                    anime_data=anime_data,
                    on_click=self.on_anime_click,
                    on_favorite=self.on_favorite_click,
                    current_user=self.current_user
                )
                favorite_cards.append(card)
            
            favorites_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "⭐ Недавно добавленное в избранное",
                                    size=typography.text_lg,
                                    weight=typography.weight_semibold,
                                    color=colors.text_primary,
                                ),
                                ft.TextButton(
                                    text="Смотреть все →",
                                    on_click=lambda e: self.on_navigate("favorites") if self.on_navigate else None,
                                    style=ft.ButtonStyle(color=colors.primary),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            content=ft.Row(
                                controls=favorite_cards,
                                spacing=spacing.md,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                            height=240,
                            margin=ft.margin.only(top=spacing.md),
                        ),
                    ],
                    spacing=0,
                ),
                margin=ft.margin.only(bottom=spacing.xl),
            )
        
        # История просмотра
        history_section = ft.Container()
        if self.watch_history:
            history_items = []
            for history in self.watch_history[:5]:  # Показываем только последние 5
                item = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                history.anime_title,
                                size=typography.text_md,
                                color=colors.text_primary,
                                expand=True,
                            ),
                            ft.Text(
                                f"Эпизод {history.episode_number}",
                                size=typography.text_sm,
                                color=colors.text_secondary,
                            ),
                            ft.Text(
                                self._format_date(history.last_watched),
                                size=typography.text_sm,
                                color=colors.text_muted,
                            ),
                        ],
                        spacing=spacing.md,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=colors.surface_light,
                    border_radius=spacing.border_radius_sm,
                    padding=spacing.md,
                    margin=ft.margin.only(bottom=spacing.xs),
                )
                history_items.append(item)
            
            history_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "📖 Недавняя активность",
                                    size=typography.text_lg,
                                    weight=typography.weight_semibold,
                                    color=colors.text_primary,
                                ),
                                ft.TextButton(
                                    text="Смотреть все →",
                                    on_click=lambda e: self.on_navigate("my_list") if self.on_navigate else None,
                                    style=ft.ButtonStyle(color=colors.primary),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Column(
                            controls=history_items,
                            spacing=0,
                        ),
                    ],
                    spacing=spacing.md,
                ),
            )
        
        self.activity_section = ft.Container(
            content=ft.Column(
                controls=[favorites_section, history_section],
                spacing=0,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
        )
        
        return self.activity_section
    
    def _create_edit_form(self) -> ft.Container:
        """Создание формы редактирования профиля"""
        
        if not self.current_user:
            return ft.Container()
        
        # Поля для редактирования
        username_field = ft.TextField(
            label="Имя пользователя",
            value=self.current_user.get('username', ''),
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
        )
        
        email_field = ft.TextField(
            label="Email",
            value=self.current_user.get('email', ''),
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
        )
        
        # Кнопки действий
        action_buttons = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="Сохранить",
                    bgcolor=colors.success,
                    color=colors.text_primary,
                    on_click=lambda e: self._save_profile_changes(username_field.value, email_field.value),
                ),
                ft.ElevatedButton(
                    text="Отмена",
                    bgcolor=colors.surface,
                    color=colors.text_primary,
                    on_click=self._cancel_edit,
                ),
            ],
            spacing=spacing.md,
            alignment=ft.MainAxisAlignment.END,
        )
        
        self.edit_form = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "✏️ Редактирование профиля",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    username_field,
                    email_field,
                    action_buttons,
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_xl,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
            visible=self.is_editing,
        )
        
        return self.edit_form
    
    def _create_loading_indicator(self) -> ft.Container:
        """Создание индикатора загрузки"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=48,
                        height=48,
                        color=colors.primary,
                    ),
                    ft.Text(
                        "Загрузка профиля...",
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
    
    def _format_date(self, date_string: Optional[str]) -> str:
        """Форматирование даты"""
        if not date_string:
            return ""
        
        try:
            dt = datetime.fromisoformat(date_string)
            return dt.strftime("%d.%m.%Y")
        except:
            return date_string
    
    async def _show_loading(self):
        """Показать индикатор загрузки"""
        self.is_loading = True
        if self.page:
            self.update()
    
    async def _hide_loading(self):
        """Скрыть индикатор загрузки"""
        self.is_loading = False
        if self.page:
            self.update()
    
    def _toggle_edit_mode(self, e):
        """Переключение режима редактирования"""
        self.is_editing = not self.is_editing
        if self.page:
            self.update()
    
    def _cancel_edit(self, e):
        """Отмена редактирования"""
        self.is_editing = False
        if self.page:
            self.update()
    
    def _save_profile_changes(self, username: str, email: str):
        """Сохранение изменений профиля"""
        try:
            if not self.current_user:
                return
            
            # Валидация
            if not username or len(username) < 3:
                self._show_error("Имя пользователя должно содержать минимум 3 символа")
                return
            
            if not email or '@' not in email:
                self._show_error("Введите корректный email")
                return
            
            # Обновляем в БД
            success = db_manager.update_user(
                self.current_user['id'],
                username=username,
                email=email
            )
            
            if success:
                # Обновляем локальные данные
                self.current_user['username'] = username
                self.current_user['email'] = email
                
                self.is_editing = False
                
                if self.page:
                    self.update()
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Профиль успешно обновлен"),
                            bgcolor=colors.success
                        )
                    )
                
                logger.info(f"Профиль обновлен: {username}")
            else:
                self._show_error("Ошибка обновления профиля")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения профиля: {e}")
            self._show_error("Произошла ошибка при сохранении")
    
    def _show_error(self, message: str):
        """Показать сообщение об ошибке"""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=colors.error
                )
            )
    
    def _logout(self, e):
        """Выход из системы"""
        if self.on_logout:
            self.on_logout()
    
    def update_user(self, user: Optional[Dict]):
        """Обновление информации о пользователе"""
        self.current_user = user
        
        # Перезагружаем данные
        if user:
            asyncio.create_task(self.load_user_data())
        
        if self.page:
            self.update()
    
    def build(self):
        """Построение UI страницы профиля"""
        
        # Если нет пользователя
        if not self.current_user:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.person, size=96, color=colors.text_muted),
                        ft.Text(
                            "Требуется авторизация",
                            size=typography.text_2xl,
                            weight=typography.weight_bold,
                            color=colors.text_muted,
                        ),
                        ft.Text(
                            "Войдите в систему для просмотра профиля",
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
        
        # Если загрузка
        if self.is_loading:
            return self._create_loading_indicator()
        
        # Основной контент
        content_sections = [
            self._create_profile_header(),
        ]
        
        # Форма редактирования (если активна)
        if self.is_editing:
            content_sections.append(self._create_edit_form())
        
        # Остальные секции
        content_sections.extend([
            self._create_stats_section(),
            self._create_achievements_section(),
            self._create_activity_section(),
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

__all__ = ["ProfilePage"]