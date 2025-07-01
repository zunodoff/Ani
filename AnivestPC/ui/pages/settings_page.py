"""
⚙️ ANIVEST DESKTOP - СТРАНИЦА НАСТРОЕК
====================================
Страница настроек приложения и пользователя
"""

import flet as ft
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
import json
import os

from config.theme import colors, icons, spacing, typography
from config.settings import USER_SETTINGS, HOTKEYS, APP_NAME, APP_VERSION, DATABASE_CONFIG, CACHE_CONFIG
from core.database.database import db_manager
from core.api.anime_service import anime_service

logger = logging.getLogger(__name__)

class SettingsPage(ft.UserControl):
    """Страница настроек приложения"""
    
    def __init__(
        self,
        current_user: Optional[Dict] = None,
        on_theme_change: Optional[Callable[[str], None]] = None,
        on_restart_required: Optional[Callable] = None
    ):
        super().__init__()
        
        self.current_user = current_user
        self.on_theme_change = on_theme_change
        self.on_restart_required = on_restart_required
        
        # Локальные копии настроек
        self.app_settings = USER_SETTINGS.copy()
        self.hotkey_settings = HOTKEYS.copy()
        
        # Состояние
        self.has_changes = False
        self.is_saving = False
        
        # UI элементы
        self.settings_sections = {}
        self.save_button = None
        self.reset_button = None
    
    def _create_appearance_section(self) -> ft.Container:
        """Создание секции внешнего вида"""
        
        # Тема
        theme_selector = ft.RadioGroup(
            content=ft.Column(
                controls=[
                    ft.Radio(value="dark", label="Темная тема"),
                    ft.Radio(value="light", label="Светлая тема (в разработке)"),
                    ft.Radio(value="auto", label="Автоматически (в разработке)"),
                ],
                spacing=spacing.sm,
            ),
            value=self.app_settings.get("theme", "dark"),
            on_change=self._on_theme_change,
        )
        
        # Язык интерфейса
        language_dropdown = ft.Dropdown(
            value=self.app_settings.get("language", "ru"),
            options=[
                ft.dropdown.Option(key="ru", text="Русский"),
                ft.dropdown.Option(key="en", text="English (в разработке)"),
            ],
            width=200,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_language_change,
        )
        
        # Ширина сайдбара
        sidebar_width_slider = ft.Slider(
            min=150,
            max=300,
            divisions=15,
            value=self.app_settings.get("sidebar_width", 180),
            label="Ширина сайдбара: {value}px",
            active_color=colors.primary,
            inactive_color=colors.border,
            thumb_color=colors.primary,
            on_change=self._on_sidebar_width_change,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "🎨 Внешний вид",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    
                    self._create_setting_item(
                        "Тема приложения",
                        "Выберите цветовую схему интерфейса",
                        theme_selector
                    ),
                    
                    self._create_setting_item(
                        "Язык интерфейса",
                        "Выберите язык пользовательского интерфейса",
                        language_dropdown
                    ),
                    
                    self._create_setting_item(
                        "Ширина боковой панели",
                        "Настройте ширину навигационной панели",
                        sidebar_width_slider
                    ),
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_player_section(self) -> ft.Container:
        """Создание секции настроек плеера"""
        
        # Автовоспроизведение
        autoplay_switch = ft.Switch(
            value=self.app_settings.get("auto_play", False),
            active_color=colors.primary,
            on_change=self._on_autoplay_change,
        )
        
        # Громкость по умолчанию
        volume_slider = ft.Slider(
            min=0,
            max=1,
            divisions=20,
            value=self.app_settings.get("player_volume", 0.8),
            label="Громкость: {value:.0%}",
            active_color=colors.primary,
            inactive_color=colors.border,
            thumb_color=colors.primary,
            on_change=self._on_volume_change,
        )
        
        # Качество по умолчанию
        quality_dropdown = ft.Dropdown(
            value=self.app_settings.get("quality_preference", "720p"),
            options=[
                ft.dropdown.Option(key="480p", text="480p (SD)"),
                ft.dropdown.Option(key="720p", text="720p (HD)"),
                ft.dropdown.Option(key="1080p", text="1080p (Full HD)"),
            ],
            width=200,
            bgcolor=colors.surface,
            border_color=colors.border,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            on_change=self._on_quality_change,
        )
        
        # Запоминать позицию воспроизведения
        remember_position_switch = ft.Switch(
            value=self.app_settings.get("remember_position", True),
            active_color=colors.primary,
            on_change=self._on_remember_position_change,
        )
        
        # Автоматически отмечать как просмотренное
        auto_mark_switch = ft.Switch(
            value=self.app_settings.get("auto_mark_watched", True),
            active_color=colors.primary,
            on_change=self._on_auto_mark_change,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "🎬 Видео плеер",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    
                    self._create_setting_item(
                        "Автовоспроизведение",
                        "Автоматически начинать воспроизведение при открытии",
                        autoplay_switch
                    ),
                    
                    self._create_setting_item(
                        "Громкость по умолчанию",
                        "Уровень громкости при запуске плеера",
                        volume_slider
                    ),
                    
                    self._create_setting_item(
                        "Качество видео",
                        "Предпочитаемое качество воспроизведения",
                        quality_dropdown
                    ),
                    
                    self._create_setting_item(
                        "Запоминать позицию",
                        "Сохранять время просмотра для продолжения",
                        remember_position_switch
                    ),
                    
                    self._create_setting_item(
                        "Автоотметка просмотра",
                        "Автоматически отмечать аниме как просмотренное",
                        auto_mark_switch
                    ),
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_notifications_section(self) -> ft.Container:
        """Создание секции уведомлений"""
        
        # Включить уведомления
        notifications_switch = ft.Switch(
            value=self.app_settings.get("notifications", True),
            active_color=colors.primary,
            on_change=self._on_notifications_change,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "🔔 Уведомления",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    
                    self._create_setting_item(
                        "Системные уведомления",
                        "Показывать уведомления в системе (в разработке)",
                        notifications_switch
                    ),
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_data_section(self) -> ft.Container:
        """Создание секции управления данными"""
        
        # Кнопки управления данными
        clear_cache_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icons.delete, size=spacing.icon_sm),
                    ft.Text("Очистить кеш", size=typography.text_sm),
                ],
                spacing=spacing.xs,
                tight=True,
            ),
            bgcolor=colors.warning,
            color=colors.text_primary,
            on_click=self._clear_cache,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
            ),
        )
        
        export_data_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icons.download, size=spacing.icon_sm),
                    ft.Text("Экспорт данных", size=typography.text_sm),
                ],
                spacing=spacing.xs,
                tight=True,
            ),
            bgcolor=colors.info,
            color=colors.text_primary,
            on_click=self._export_data,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
            ),
        )
        
        reset_settings_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icons.settings, size=spacing.icon_sm),
                    ft.Text("Сброс настроек", size=typography.text_sm),
                ],
                spacing=spacing.xs,
                tight=True,
            ),
            bgcolor=colors.error,
            color=colors.text_primary,
            on_click=self._reset_settings,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=spacing.md, vertical=spacing.sm),
            ),
        )
        
        # Статистика данных
        cache_stats = self._get_cache_stats()
        db_stats = self._get_database_stats()
        
        stats_info = ft.Column(
            controls=[
                ft.Text(
                    "📊 Статистика данных:",
                    size=typography.text_md,
                    weight=typography.weight_semibold,
                    color=colors.text_primary,
                ),
                ft.Text(
                    f"• Размер кеша: {cache_stats.get('cache_size', 'Неизвестно')}",
                    size=typography.text_sm,
                    color=colors.text_secondary,
                ),
                ft.Text(
                    f"• Записей в БД: {db_stats.get('total_records', 'Неизвестно')}",
                    size=typography.text_sm,
                    color=colors.text_secondary,
                ),
            ],
            spacing=spacing.xs,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "💾 Управление данными",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    
                    stats_info,
                    
                    ft.Row(
                        controls=[
                            clear_cache_button,
                            export_data_button,
                            reset_settings_button,
                        ],
                        spacing=spacing.md,
                        wrap=True,
                    ),
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
            margin=ft.margin.only(bottom=spacing.xl),
        )
    
    def _create_about_section(self) -> ft.Container:
        """Создание секции о приложении"""
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "ℹ️ О приложении",
                        size=typography.text_xl,
                        weight=typography.weight_bold,
                        color=colors.text_primary,
                    ),
                    
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        APP_NAME,
                                        size=typography.text_2xl,
                                        weight=typography.weight_bold,
                                        color=colors.primary,
                                    ),
                                    ft.Text(
                                        f"Версия {APP_VERSION}",
                                        size=typography.text_lg,
                                        color=colors.text_secondary,
                                    ),
                                    ft.Text(
                                        "Десктопное приложение для просмотра аниме",
                                        size=typography.text_md,
                                        color=colors.text_muted,
                                    ),
                                ],
                                spacing=spacing.sm,
                            ),
                            
                            ft.Container(
                                content=ft.Icon(
                                    icons.movie,
                                    size=64,
                                    color=colors.primary,
                                ),
                                width=80,
                                height=80,
                                bgcolor=colors.primary + "20",
                                border_radius=40,
                                alignment=ft.alignment.center,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Возможности:",
                                size=typography.text_md,
                                weight=typography.weight_semibold,
                                color=colors.text_primary,
                            ),
                            ft.Text(
                                "• Интеграция с Shikimori API для информации об аниме",
                                size=typography.text_sm,
                                color=colors.text_secondary,
                            ),
                            ft.Text(
                                "• Видео через Kodik с поддержкой различных озвучек",
                                size=typography.text_sm,
                                color=colors.text_secondary,
                            ),
                            ft.Text(
                                "• Система избранного и истории просмотра",
                                size=typography.text_sm,
                                color=colors.text_secondary,
                            ),
                            ft.Text(
                                "• Современный интерфейс с темной темой",
                                size=typography.text_sm,
                                color=colors.text_secondary,
                            ),
                        ],
                        spacing=spacing.xs,
                    ),
                ],
                spacing=spacing.lg,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.xl,
        )
    
    def _create_setting_item(self, title: str, description: str, control: ft.Control) -> ft.Container:
        """Создание элемента настройки"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                title,
                                size=typography.text_md,
                                weight=typography.weight_semibold,
                                color=colors.text_primary,
                            ),
                            ft.Text(
                                description,
                                size=typography.text_sm,
                                color=colors.text_muted,
                            ),
                        ],
                        spacing=spacing.xs,
                        expand=True,
                    ),
                    control,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=colors.card,
            border_radius=spacing.border_radius_md,
            padding=spacing.md,
            margin=ft.margin.only(bottom=spacing.sm),
        )
    
    def _create_action_buttons(self) -> ft.Container:
        """Создание кнопок действий"""
        
        self.save_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icons.check_circle, size=spacing.icon_md),
                    ft.Text("Сохранить настройки", size=typography.text_md),
                ],
                spacing=spacing.sm,
                tight=True,
            ),
            bgcolor=colors.success,
            color=colors.text_primary,
            on_click=self._save_settings,
            disabled=not self.has_changes,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
            ),
        )
        
        self.reset_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icons.close, size=spacing.icon_md),
                    ft.Text("Отменить изменения", size=typography.text_md),
                ],
                spacing=spacing.sm,
                tight=True,
            ),
            bgcolor=colors.surface,
            color=colors.text_primary,
            on_click=self._reset_changes,
            disabled=not self.has_changes,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=spacing.lg, vertical=spacing.md),
            ),
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(expand=True),  # Разделитель
                    self.reset_button,
                    self.save_button,
                ],
                spacing=spacing.md,
                alignment=ft.MainAxisAlignment.END,
            ),
            bgcolor=colors.surface,
            border_radius=spacing.border_radius_lg,
            padding=spacing.lg,
        )
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кеша"""
        try:
            # Получаем размер кеша от anime_service
            service_stats = anime_service.get_service_stats()
            cache_size = service_stats.get('poster_cache_size', 0) + service_stats.get('merge_cache_size', 0)
            
            return {
                'cache_size': f"{cache_size} записей",
                'poster_cache': service_stats.get('poster_cache_size', 0),
                'merge_cache': service_stats.get('merge_cache_size', 0),
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики кеша: {e}")
            return {'cache_size': 'Ошибка'}
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных"""
        try:
            stats = db_manager.get_stats()
            total_records = sum(stats.values())
            
            return {
                'total_records': total_records,
                'users': stats.get('users', 0),
                'comments': stats.get('comments', 0),
                'favorites': stats.get('favorites', 0),
                'watch_history': stats.get('watch_history', 0),
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики БД: {e}")
            return {'total_records': 'Ошибка'}
    
    def _mark_changed(self):
        """Отметить что есть несохраненные изменения"""
        self.has_changes = True
        self._update_action_buttons()
    
    def _update_action_buttons(self):
        """Обновление состояния кнопок действий"""
        if self.save_button:
            self.save_button.disabled = not self.has_changes
            self.save_button.update()
        
        if self.reset_button:
            self.reset_button.disabled = not self.has_changes
            self.reset_button.update()
    
    # Обработчики изменений настроек
    def _on_theme_change(self, e):
        """Обработка смены темы"""
        self.app_settings["theme"] = e.control.value
        self._mark_changed()
        
        if self.on_theme_change:
            self.on_theme_change(e.control.value)
    
    def _on_language_change(self, e):
        """Обработка смены языка"""
        self.app_settings["language"] = e.control.value
        self._mark_changed()
    
    def _on_sidebar_width_change(self, e):
        """Обработка изменения ширины сайдбара"""
        self.app_settings["sidebar_width"] = int(e.control.value)
        self._mark_changed()
    
    def _on_autoplay_change(self, e):
        """Обработка изменения автовоспроизведения"""
        self.app_settings["auto_play"] = e.control.value
        self._mark_changed()
    
    def _on_volume_change(self, e):
        """Обработка изменения громкости"""
        self.app_settings["player_volume"] = e.control.value
        self._mark_changed()
    
    def _on_quality_change(self, e):
        """Обработка изменения качества"""
        self.app_settings["quality_preference"] = e.control.value
        self._mark_changed()
    
    def _on_remember_position_change(self, e):
        """Обработка изменения запоминания позиции"""
        self.app_settings["remember_position"] = e.control.value
        self._mark_changed()
    
    def _on_auto_mark_change(self, e):
        """Обработка изменения автоотметки"""
        self.app_settings["auto_mark_watched"] = e.control.value
        self._mark_changed()
    
    def _on_notifications_change(self, e):
        """Обработка изменения уведомлений"""
        self.app_settings["notifications"] = e.control.value
        self._mark_changed()
    
    def _save_settings(self, e):
        """Сохранение настроек"""
        try:
            self.is_saving = True
            
            # Обновляем глобальные настройки
            USER_SETTINGS.update(self.app_settings)
            
            # Сохраняем настройки пользователя в БД (если авторизован)
            if self.current_user:
                for key, value in self.app_settings.items():
                    db_manager.set_user_setting(self.current_user['id'], key, value)
            
            self.has_changes = False
            self.is_saving = False
            
            self._update_action_buttons()
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Настройки сохранены"),
                        bgcolor=colors.success
                    )
                )
            
            logger.info("Настройки сохранены")
            
        except Exception as ex:
            logger.error(f"Ошибка сохранения настроек: {ex}")
            self.is_saving = False
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Ошибка сохранения настроек"),
                        bgcolor=colors.error
                    )
                )
    
    def _reset_changes(self, e):
        """Отмена изменений"""
        self.app_settings = USER_SETTINGS.copy()
        self.has_changes = False
        
        self._update_action_buttons()
        
        # Обновляем UI
        if self.page:
            self.update()
    
    def _clear_cache(self, e):
        """Очистка кеша"""
        try:
            # Очищаем кеш anime_service
            anime_service.clear_cache()
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Кеш очищен"),
                        bgcolor=colors.success
                    )
                )
            
            logger.info("Кеш очищен")
            
        except Exception as ex:
            logger.error(f"Ошибка очистки кеша: {ex}")
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Ошибка очистки кеша"),
                        bgcolor=colors.error
                    )
                )
    
    def _export_data(self, e):
        """Экспорт пользовательских данных"""
        try:
            # В будущем можно реализовать экспорт в JSON
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Экспорт данных будет добавлен в будущих версиях"),
                        bgcolor=colors.info
                    )
                )
            
            logger.info("Запрос экспорта данных")
            
        except Exception as ex:
            logger.error(f"Ошибка экспорта данных: {ex}")
    
    def _reset_settings(self, e):
        """Сброс настроек к значениям по умолчанию"""
        try:
            # Сбрасываем к изначальным значениям
            from config.settings import USER_SETTINGS as DEFAULT_SETTINGS
            
            self.app_settings = DEFAULT_SETTINGS.copy()
            USER_SETTINGS.update(self.app_settings)
            
            # Очищаем настройки пользователя в БД
            if self.current_user:
                # В реальной реализации нужно добавить метод очистки настроек
                pass
            
            self.has_changes = False
            self._update_action_buttons()
            
            if self.page:
                self.update()
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Настройки сброшены к значениям по умолчанию"),
                        bgcolor=colors.success
                    )
                )
            
            logger.info("Настройки сброшены")
            
        except Exception as ex:
            logger.error(f"Ошибка сброса настроек: {ex}")
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Ошибка сброса настроек"),
                        bgcolor=colors.error
                    )
                )
    
    def update_user(self, user: Optional[Dict]):
        """Обновление информации о пользователе"""
        self.current_user = user
        
        # Загружаем пользовательские настройки если есть
        if user:
            try:
                user_settings = db_manager.get_all_user_settings(user['id'])
                self.app_settings.update(user_settings)
            except Exception as e:
                logger.error(f"Ошибка загрузки пользовательских настроек: {e}")
        
        if self.page:
            self.update()
    
    def build(self):
        """Построение UI страницы настроек"""
        
        # Основные секции настроек
        content_sections = [
            ft.Text(
                "⚙️ Настройки приложения",
                size=typography.text_3xl,
                weight=typography.weight_bold,
                color=colors.text_primary,
            ),
            
            self._create_appearance_section(),
            self._create_player_section(),
            self._create_notifications_section(),
            self._create_data_section(),
            self._create_about_section(),
            
            self._create_action_buttons(),
        ]
        
        return ft.Container(
            content=ft.Column(
                controls=content_sections,
                spacing=spacing.md,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=spacing.xxl,
            expand=True,
        )

# ===== ЭКСПОРТ =====

__all__ = ["SettingsPage"]