"""
📱 ANIVEST DESKTOP - БОКОВАЯ ПАНЕЛЬ НАВИГАЦИИ
==========================================
Компонент сайдбара с иконками и текстом для навигации
"""

import flet as ft
import logging
from typing import Dict, Any, Callable, Optional, List

from config.theme import colors, icons, spacing, typography, get_sidebar_button_style
from config.settings import USER_SETTINGS

logger = logging.getLogger(__name__)

class NavigationItem:
    """Элемент навигации"""
    def __init__(
        self,
        key: str,
        icon: str,
        text: str,
        tooltip: Optional[str] = None,
        badge_count: int = 0,
        divider_after: bool = False
    ):
        self.key = key
        self.icon = icon
        self.text = text
        self.tooltip = tooltip or text
        self.badge_count = badge_count
        self.divider_after = divider_after

class AnivesetSidebar(ft.UserControl):
    """Боковая панель навигации с иконками и текстом"""
    
    def __init__(
        self,
        current_page: str = "home",
        width: int = 180,
        on_navigate: Optional[Callable[[str], None]] = None,
        current_user: Optional[Dict] = None,
        compact_mode: bool = False
    ):
        super().__init__()
        
        self.current_page = current_page
        self.width = width if not compact_mode else 60
        self.on_navigate = on_navigate
        self.current_user = current_user
        self.compact_mode = compact_mode
        
        # Навигационные элементы
        self.navigation_items = self._create_navigation_items()
        self.profile_items = self._create_profile_items()
        
        # UI элементы
        self.nav_buttons = {}
        self.profile_buttons = {}
        
    def _create_navigation_items(self) -> List[NavigationItem]:
        """Создание основных элементов навигации"""
        return [
            NavigationItem("home", icons.home, "Главная"),
            NavigationItem("catalog", icons.movie, "Каталог"),
            NavigationItem("favorites", icons.favorite, "Избранное", badge_count=self._get_favorites_count()),
            NavigationItem("my_list", icons.list, "Мой список"),
            NavigationItem("downloads", icons.download, "Загрузки", divider_after=True),
        ]
    
    def _create_profile_items(self) -> List[NavigationItem]:
        """Создание элементов профиля"""
        return [
            NavigationItem("stats", icons.trending_up, "Статистика"),
            NavigationItem("settings", icons.settings, "Настройки"),
            NavigationItem("about", icons.info, "О программе"),
        ]
    
    def _get_favorites_count(self) -> int:
        """Получение количества избранного для бейджа"""
        try:
            if self.current_user:
                from core.database.database import db_manager
                favorites = db_manager.get_user_favorites(self.current_user['id'])
                return len(favorites)
        except Exception as e:
            logger.error(f"Ошибка получения количества избранного: {e}")
        return 0
    
    def _create_navigation_button(self, item: NavigationItem) -> ft.Container:
        """Создание кнопки навигации"""
        is_active = item.key == self.current_page
        
        # Иконка с бейджем
        icon_with_badge = ft.Stack(
            controls=[
                ft.Icon(
                    item.icon,
                    color=colors.text_primary if is_active else colors.text_muted,
                    size=spacing.icon_md,
                ),
                # Бейдж с количеством
                ft.Container(
                    content=ft.Text(
                        str(item.badge_count),
                        size=typography.text_xs,
                        color=colors.text_primary,
                        weight=typography.weight_bold,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=16,
                    height=16,
                    bgcolor=colors.secondary,
                    border_radius=8,
                    alignment=ft.alignment.center,
                    offset=ft.transform.Offset(0.7, -0.7),
                    visible=item.badge_count > 0
                ) if not self.compact_mode else ft.Container()
            ],
            width=spacing.icon_md,
            height=spacing.icon_md,
        )
        
        # Контент кнопки
        if self.compact_mode:
            button_content = ft.Container(
                content=icon_with_badge,
                alignment=ft.alignment.center,
                tooltip=item.tooltip
            )
        else:
            button_content = ft.Row(
                controls=[
                    icon_with_badge,
                    ft.Text(
                        item.text,
                        color=colors.text_primary if is_active else colors.text_muted,
                        size=typography.text_md,
                        weight=typography.weight_semibold if is_active else typography.weight_normal,
                    )
                ],
                spacing=spacing.md,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        
        # Контейнер кнопки
        button_container = ft.Container(
            content=button_content,
            bgcolor=colors.primary if is_active else "transparent",
            border_radius=spacing.border_radius_md,
            padding=ft.padding.symmetric(
                horizontal=spacing.md if not self.compact_mode else spacing.sm,
                vertical=spacing.sm
            ),
            margin=ft.margin.symmetric(
                horizontal=spacing.sm,
                vertical=2
            ),
            height=48,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e, page=item.key: self._on_navigate(page),
            ink=True,
        )
        
        # Добавляем разделитель если нужно
        controls = [button_container]
        if item.divider_after and not self.compact_mode:
            controls.append(self._create_divider("ПРОФИЛЬ"))
        
        return ft.Column(controls=controls, spacing=0) if len(controls) > 1 else button_container
    
    def _create_divider(self, text: str) -> ft.Container:
        """Создание разделителя с текстом"""
        if self.compact_mode:
            return ft.Container(
                height=1,
                bgcolor=colors.border,
                margin=ft.margin.symmetric(horizontal=spacing.md, vertical=spacing.lg),
            )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        height=1,
                        bgcolor=colors.border,
                        margin=ft.margin.symmetric(horizontal=spacing.md, vertical=spacing.sm),
                    ),
                    ft.Container(
                        content=ft.Text(
                            text,
                            size=typography.text_xs,
                            color=colors.text_muted,
                            weight=typography.weight_bold,
                        ),
                        padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.xs),
                    )
                ],
                spacing=0,
            ),
            margin=ft.margin.symmetric(vertical=spacing.sm),
        )
    
    def _create_user_section(self) -> ft.Container:
        """Создание секции пользователя"""
        if not self.current_user:
            # Кнопка входа для неавторизованных пользователей
            return ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icons.login, size=spacing.icon_sm),
                            ft.Text("Войти", size=typography.text_sm) if not self.compact_mode else ft.Container()
                        ],
                        spacing=spacing.sm,
                        alignment=ft.MainAxisAlignment.CENTER if self.compact_mode else ft.MainAxisAlignment.START,
                    ),
                    bgcolor=colors.primary,
                    color=colors.text_primary,
                    on_click=lambda e: self._on_navigate("login"),
                    width=self.width - spacing.md * 2 if not self.compact_mode else None,
                ),
                margin=ft.margin.all(spacing.sm),
                alignment=ft.alignment.center,
            )
        
        # Информация о пользователе
        user_avatar = ft.Container(
            content=ft.Text(
                self.current_user.get('username', 'U')[0].upper(),
                size=typography.text_md,
                color=colors.text_primary,
                weight=typography.weight_bold,
                text_align=ft.TextAlign.CENTER
            ),
            width=36,
            height=36,
            bgcolor=colors.primary,
            border_radius=18,
            alignment=ft.alignment.center,
        )
        
        if self.compact_mode:
            return ft.Container(
                content=user_avatar,
                margin=ft.margin.all(spacing.sm),
                alignment=ft.alignment.center,
                tooltip=f"Пользователь: {self.current_user.get('username', 'Неизвестен')}"
            )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    user_avatar,
                    ft.Column(
                        controls=[
                            ft.Text(
                                self.current_user.get('username', 'Неизвестен'),
                                size=typography.text_md,
                                color=colors.text_primary,
                                weight=typography.weight_semibold,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                max_lines=1,
                            ),
                            ft.Text(
                                f"Роль: {self.current_user.get('role', 'user')}",
                                size=typography.text_xs,
                                color=colors.text_muted,
                            )
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=icons.logout,
                        icon_color=colors.text_muted,
                        icon_size=spacing.icon_sm,
                        tooltip="Выйти",
                        on_click=lambda e: self._on_navigate("logout"),
                    )
                ],
                spacing=spacing.sm,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_md,
            padding=spacing.sm,
            margin=ft.margin.all(spacing.sm),
        )
    
    def _create_toggle_button(self) -> ft.Container:
        """Создание кнопки переключения компактного режима"""
        return ft.Container(
            content=ft.IconButton(
                icon=icons.menu if self.compact_mode else icons.close,
                icon_color=colors.text_muted,
                icon_size=spacing.icon_sm,
                tooltip="Переключить компактный режим" if not self.compact_mode else "Развернуть сайдбар",
                on_click=self._toggle_compact_mode,
            ),
            alignment=ft.alignment.center,
            margin=ft.margin.symmetric(vertical=spacing.sm),
        )
    
    def _on_navigate(self, page_key: str):
        """Обработка навигации"""
        if page_key != self.current_page:
            self.current_page = page_key
            
            # Обновляем состояние кнопок
            self._update_button_states()
            
            # Вызываем callback
            if self.on_navigate:
                self.on_navigate(page_key)
            
            logger.info(f"Навигация на страницу: {page_key}")
    
    def _toggle_compact_mode(self, e):
        """Переключение компактного режима"""
        self.compact_mode = not self.compact_mode
        self.width = 60 if self.compact_mode else 180
        
        # Сохраняем настройку
        USER_SETTINGS["sidebar_compact"] = self.compact_mode
        
        # Перестраиваем сайдбар
        if self.page:
            self.update()
        
        logger.info(f"Компактный режим сайдбара: {self.compact_mode}")
    
    def _update_button_states(self):
        """Обновление состояния кнопок"""
        # Обновляем навигационные кнопки
        for item in self.navigation_items + self.profile_items:
            if item.key in self.nav_buttons:
                button = self.nav_buttons[item.key]
                is_active = item.key == self.current_page
                
                # Обновляем стили кнопки
                button.bgcolor = colors.primary if is_active else "transparent"
                
                if self.page:
                    button.update()
    
    def update_user(self, user: Optional[Dict]):
        """Обновление информации о пользователе"""
        self.current_user = user
        if self.page:
            self.update()
    
    def update_page(self, page_key: str):
        """Обновление текущей страницы"""
        if page_key != self.current_page:
            self.current_page = page_key
            self._update_button_states()
    
    def update_favorites_count(self):
        """Обновление количества избранного"""
        # Обновляем количество для элемента favorites
        for item in self.navigation_items:
            if item.key == "favorites":
                item.badge_count = self._get_favorites_count()
                break
        
        # Перестраиваем сайдбар
        if self.page:
            self.update()
    
    def build(self):
        """Построение UI сайдбара"""
        # Навигационные кнопки
        nav_buttons = []
        for item in self.navigation_items:
            button = self._create_navigation_button(item)
            nav_buttons.append(button)
            # Сохраняем ссылку на кнопку для обновления
            if isinstance(button, ft.Container):
                self.nav_buttons[item.key] = button
        
        # Профильные кнопки
        profile_buttons = []
        for item in self.profile_items:
            button = self._create_navigation_button(item)
            profile_buttons.append(button)
            # Сохраняем ссылку на кнопку для обновления
            if isinstance(button, ft.Container):
                self.profile_buttons[item.key] = button
        
        # Основной контент сайдбара
        sidebar_content = ft.Column(
            controls=[
                # Кнопка переключения режима
                self._create_toggle_button(),
                
                # Основная навигация
                ft.Container(
                    content=ft.Column(
                        controls=nav_buttons,
                        spacing=spacing.xs,
                    ),
                    expand=True,
                ),
                
                # Разделитель для профиля
                self._create_divider("ПРОФИЛЬ") if not self.compact_mode else ft.Container(height=1, bgcolor=colors.border, margin=ft.margin.symmetric(horizontal=spacing.md)),
                
                # Профильная навигация
                ft.Column(
                    controls=profile_buttons,
                    spacing=spacing.xs,
                ),
                
                # Информация о пользователе
                self._create_user_section(),
            ],
            spacing=0,
            expand=True,
        )
        
        # Главный контейнер сайдбара
        return ft.Container(
            content=sidebar_content,
            width=self.width,
            bgcolor=colors.surface,
            border=ft.border.only(right=ft.border.BorderSide(1, colors.border)),
            padding=ft.padding.symmetric(vertical=spacing.sm),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

# ===== УПРОЩЕННАЯ ВЕРСИЯ САЙДБАРА =====

class CompactSidebar(AnivesetSidebar):
    """Упрощенная версия сайдбара только с иконками"""
    
    def __init__(self, **kwargs):
        super().__init__(compact_mode=True, width=60, **kwargs)

# ===== МОБИЛЬНАЯ ВЕРСИЯ =====

class MobileSidebar(ft.UserControl):
    """Мобильная версия сайдбара (drawer)"""
    
    def __init__(
        self,
        current_page: str = "home",
        on_navigate: Optional[Callable[[str], None]] = None,
        current_user: Optional[Dict] = None,
        on_close: Optional[Callable] = None
    ):
        super().__init__()
        
        self.current_page = current_page
        self.on_navigate = on_navigate
        self.current_user = current_user
        self.on_close = on_close
        
        # Используем обычный сайдбар внутри
        self.sidebar = AnivesetSidebar(
            current_page=current_page,
            on_navigate=self._handle_navigate,
            current_user=current_user,
            width=280  # Шире для мобильной версии
        )
    
    def _handle_navigate(self, page_key: str):
        """Обработка навигации с закрытием drawer"""
        if self.on_navigate:
            self.on_navigate(page_key)
        
        if self.on_close:
            self.on_close()
    
    def build(self):
        """Построение мобильного сайдбара"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Заголовок с кнопкой закрытия
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(
                                    "Anivest",
                                    size=typography.text_2xl,
                                    weight=typography.weight_bold,
                                    color=colors.text_primary
                                ),
                                ft.IconButton(
                                    icon=icons.close,
                                    icon_color=colors.text_muted,
                                    on_click=lambda e: self.on_close() if self.on_close else None,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=spacing.md,
                        bgcolor=colors.background,
                        border=ft.border.only(bottom=ft.border.BorderSide(1, colors.border)),
                    ),
                    
                    # Основной сайдбар
                    ft.Container(
                        content=self.sidebar,
                        expand=True,
                    )
                ],
                spacing=0,
                expand=True,
            ),
            width=280,
            bgcolor=colors.surface,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=colors.shadow,
                offset=ft.Offset(2, 0)
            ),
        )

# ===== ЭКСПОРТ =====

__all__ = [
    "NavigationItem", "AnivesetSidebar", "CompactSidebar", "MobileSidebar"
]