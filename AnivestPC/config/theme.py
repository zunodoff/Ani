"""
🎨 ANIVEST DESKTOP - ЦВЕТОВАЯ СХЕМА И СТИЛИ
==========================================
Темная фиолетово-розовая тема из Flask сайта
"""

import flet as ft
from dataclasses import dataclass
from typing import Dict, Any

# ===== ОСНОВНАЯ ЦВЕТОВАЯ ПАЛИТРА =====

@dataclass
class AnivesetColors:
    """Цвета Anivest (перенесены из Flask сайта)"""
    
    # Основные цвета
    primary: str = "#8B5CF6"           # Фиолетовый
    primary_dark: str = "#7C3AED"      # Темно-фиолетовый  
    primary_light: str = "#A78BFA"     # Светло-фиолетовый
    secondary: str = "#EC4899"         # Розовый
    accent: str = "#F59E0B"            # Янтарный
    success: str = "#10B981"           # Зеленый
    
    # Фоны
    background: str = "#0F0F23"        # Темно-синий (основной фон)
    surface: str = "#1A1B3A"           # Синий (карточки и панели)
    surface_light: str = "#252550"     # Светлее синий
    card: str = "#2D2D5F"              # Светло-синий (карточки)
    card_hover: str = "#363670"        # Hover для карточек
    
    # Интерактивные элементы
    hover: str = "#333366"             # Hover состояние
    border: str = "#404080"            # Границы
    border_light: str = "#50508080"    # Светлые границы с прозрачностью
    
    # Текст
    text_primary: str = "#FFFFFF"      # Белый (основной текст)
    text_secondary: str = "#E2E8F0"    # Светло-серый (вторичный текст)
    text_muted: str = "#94A3B8"        # Серый (приглушенный текст)
    
    # Тени и эффекты
    shadow: str = "#00000060"          # Тень (60% прозрачности)
    
    # Статусы и состояния
    error: str = "#EF4444"             # Красный (ошибки)
    warning: str = "#F59E0B"           # Желтый (предупреждения)
    info: str = "#3B82F6"              # Синий (информация)
    
    # Специальные цвета для рейтингов
    rating_excellent: str = "#10B981"  # Зеленый (9-10)
    rating_good: str = "#F59E0B"       # Янтарный (7-8)
    rating_average: str = "#EF4444"    # Красный (5-6)
    rating_poor: str = "#6B7280"       # Серый (1-4)

# Создаем экземпляр цветов
colors = AnivesetColors()

# ===== ИКОНКИ =====

class AnivesetIcons:
    """Набор иконок для приложения"""
    
    # Навигация
    home = ft.icons.HOME
    catalog = ft.icons.MOVIE
    favorites = ft.icons.FAVORITE
    my_list = ft.icons.LIST
    downloads = ft.icons.DOWNLOAD
    
    # Пользователь
    person = ft.icons.PERSON
    settings = ft.icons.SETTINGS
    logout = ft.icons.LOGOUT
    login = ft.icons.LOGIN
    
    # Управление
    play_circle = ft.icons.PLAY_CIRCLE
    pause_circle = ft.icons.PAUSE_CIRCLE
    stop = ft.icons.STOP
    next_track = ft.icons.SKIP_NEXT
    prev_track = ft.icons.SKIP_PREVIOUS
    
    # Интерфейс
    search = ft.icons.SEARCH
    close = ft.icons.CLOSE
    menu = ft.icons.MENU
    more_vert = ft.icons.MORE_VERT
    filter_list = ft.icons.FILTER_LIST
    
    # Статусы
    star = ft.icons.STAR
    star_border = ft.icons.STAR_BORDER
    trending_up = ft.icons.TRENDING_UP
    info = ft.icons.INFO
    check_circle = ft.icons.CHECK_CIRCLE
    
    # Управление темой
    dark_mode = ft.icons.DARK_MODE
    light_mode = ft.icons.LIGHT_MODE
    
    # Социальные
    comment = ft.icons.COMMENT
    thumb_up = ft.icons.THUMB_UP
    thumb_down = ft.icons.THUMB_DOWN
    share = ft.icons.SHARE

icons = AnivesetIcons()

# ===== РАЗМЕРЫ И ОТСТУПЫ =====

class AnivesetSpacing:
    """Размеры и отступы"""
    
    # Базовые отступы
    xs = 4
    sm = 8
    md = 16
    lg = 24
    xl = 32
    xxl = 48
    
    # Радиусы скругления
    border_radius_sm = 8
    border_radius_md = 12
    border_radius_lg = 16
    border_radius_xl = 20
    
    # Размеры компонентов
    sidebar_width = 180
    header_height = 60
    card_height = 280
    button_height = 40
    
    # Размеры иконок
    icon_sm = 16
    icon_md = 20
    icon_lg = 24
    icon_xl = 32

spacing = AnivesetSpacing()

# ===== ТИПОГРАФИКА =====

class AnivesetTypography:
    """Настройки шрифтов и размеров текста"""
    
    # Размеры шрифтов
    text_xs = 11
    text_sm = 13
    text_md = 14
    text_lg = 16
    text_xl = 18
    text_2xl = 24
    text_3xl = 30
    text_4xl = 36
    
    # Веса шрифтов
    weight_normal = ft.FontWeight.NORMAL
    weight_medium = ft.FontWeight.W_500
    weight_semibold = ft.FontWeight.W_600
    weight_bold = ft.FontWeight.BOLD
    
    # Семейства шрифтов
    font_family = "Roboto"  # Можно изменить на кастомный шрифт

typography = AnivesetTypography()

# ===== ТЕМЫ FLET =====

def create_anivest_theme() -> ft.Theme:
    """Создание темы Flet с цветами Anivest"""
    
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=colors.primary,
            secondary=colors.secondary,
            background=colors.background,
            surface=colors.surface,
            error=colors.error,
            on_primary=colors.text_primary,
            on_secondary=colors.text_primary,
            on_background=colors.text_secondary,
            on_surface=colors.text_secondary,
            on_error=colors.text_primary,
        ),
        # Можно добавить кастомные шрифты
        font_family=typography.font_family
    )

# ===== СТИЛИ КОМПОНЕНТОВ =====

def get_card_style() -> Dict[str, Any]:
    """Стиль для карточек аниме"""
    return {
        "bgcolor": colors.card,
        "border_radius": spacing.border_radius_lg,
        "shadow": ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=colors.shadow,
            offset=ft.Offset(0, 8)
        )
    }

def get_button_style(variant: str = "primary") -> Dict[str, Any]:
    """Стили для кнопок"""
    
    styles = {
        "primary": {
            "bgcolor": colors.primary,
            "color": colors.text_primary,
            "border_radius": spacing.border_radius_md
        },
        "secondary": {
            "bgcolor": colors.surface,
            "color": colors.text_secondary,
            "border_radius": spacing.border_radius_md,
            "border": ft.border.all(1, colors.border)
        },
        "ghost": {
            "bgcolor": "transparent",
            "color": colors.text_muted,
            "border_radius": spacing.border_radius_md
        }
    }
    
    return styles.get(variant, styles["primary"])

def get_input_style() -> Dict[str, Any]:
    """Стиль для полей ввода"""
    return {
        "bgcolor": colors.surface,
        "border_color": colors.border,
        "focused_border_color": colors.primary,
        "color": colors.text_primary,
        "border_radius": spacing.border_radius_md
    }

def get_sidebar_button_style(is_active: bool = False) -> Dict[str, Any]:
    """Стиль для кнопок сайдбара"""
    return {
        "bgcolor": colors.primary if is_active else "transparent",
        "color": colors.text_primary if is_active else colors.text_muted,
        "border_radius": spacing.border_radius_md,
        "padding": ft.padding.symmetric(
            horizontal=spacing.md, 
            vertical=spacing.sm
        )
    }

# ===== АНИМАЦИИ =====

class AnivesetAnimations:
    """Настройки анимаций"""
    
    # Длительности
    duration_fast = 150      # Быстрые переходы
    duration_normal = 250    # Обычные переходы
    duration_slow = 400      # Медленные переходы
    
    # Кривые анимации
    ease_in = ft.AnimationCurve.EASE_IN
    ease_out = ft.AnimationCurve.EASE_OUT
    ease_in_out = ft.AnimationCurve.EASE_IN_OUT

animations = AnivesetAnimations()

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def get_rating_color(rating: float) -> str:
    """Получение цвета для рейтинга"""
    if rating >= 9.0:
        return colors.rating_excellent
    elif rating >= 7.0:
        return colors.rating_good
    elif rating >= 5.0:
        return colors.rating_average
    else:
        return colors.rating_poor

def get_status_color(status: str) -> str:
    """Получение цвета для статуса аниме"""
    status_colors = {
        "released": colors.success,
        "ongoing": colors.info,
        "anons": colors.warning
    }
    return status_colors.get(status.lower(), colors.text_muted)

def create_gradient_container(start_color: str, end_color: str) -> ft.Container:
    """Создание контейнера с градиентом"""
    return ft.Container(
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[start_color, end_color]
        )
    )

# ===== ЭКСПОРТ =====

__all__ = [
    "colors", "icons", "spacing", "typography", "animations",
    "create_anivest_theme", "get_card_style", "get_button_style",
    "get_input_style", "get_sidebar_button_style", "get_rating_color",
    "get_status_color", "create_gradient_container", "AnivesetColors",
    "AnivesetIcons", "AnivesetSpacing", "AnivesetTypography",
    "AnivesetAnimations"
]