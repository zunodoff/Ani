"""
🎯 ANIVEST DESKTOP - САЙДБАР С ИКОНКАМИ И ТЕКСТОМ
=================================================
Сайдбар 180px с иконками и подписями как в примере
"""

import flet as ft
import asyncio
from typing import Optional

class AnivesetDesktop:
    def __init__(self):
        self.current_page = "home"
        self.user_logged_in = False
        self.username = "Anime_Lover"
        self.page = None
        
        # 🎨 Обновленная цветовая палитра
        self.colors = {
            "primary": "#8B5CF6",      # Фиолетовый
            "primary_dark": "#7C3AED", # Темно-фиолетовый
            "primary_light": "#A78BFA", # Светло-фиолетовый
            "secondary": "#EC4899",    # Розовый  
            "accent": "#F59E0B",       # Янтарный
            "success": "#10B981",      # Зеленый
            "background": "#0F0F23",   # Темно-синий
            "surface": "#1A1B3A",      # Синий
            "surface_light": "#252550", # Светлее синий
            "card": "#2D2D5F",         # Светло-синий
            "card_hover": "#363670",   # Hover для карточек
            "hover": "#333366",        # Hover состояние
            "border": "#404080",       # Границы
            "border_light": "#50508080", # Светлые границы с прозрачностью
            "text_primary": "#FFFFFF", # Белый
            "text_secondary": "#E2E8F0", # Светло-серый
            "text_muted": "#94A3B8",   # Серый
            "shadow": "#00000060",     # Тень темнее
        }
        
        # 🔧 Универсальные иконки
        self.icons = {
            "play_circle": "play_circle",
            "search": "search", 
            "dark_mode": "dark_mode",
            "person": "person",
            "settings": "settings",
            "close": "close",
            "home": "home",
            "movie": "movie",
            "favorite": "favorite",
            "list": "list",
            "download": "download",
            "trending_up": "trending_up",
            "info": "info",
            "star": "star"
        }

    def main(self, page: ft.Page):
        """Главная функция приложения"""
        self.page = page
        
        # 🖥️ Жесткие ограничения размеров
        page.title = "Anivest Desktop - Сайдбар с иконками и текстом"
        
        # Устанавливаем размеры окна с жесткими ограничениями
        try:
            # Новый API
            page.window_width = 1400
            page.window_height = 900
            page.window_min_width = 1200  # МИНИМУМ 1200px
            page.window_min_height = 800  # МИНИМУМ 800px  
            page.window_max_width = 1920  # МАКСИМУМ Full HD
            page.window_max_height = 1080 # МАКСИМУМ Full HD
        except:
            try:
                # Старый API
                page.window.width = 1400
                page.window.height = 900
                page.window.min_width = 1200
                page.window.min_height = 800
                page.window.max_width = 1920
                page.window.max_height = 1080
            except:
                pass
                
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = self.colors["background"]
        page.padding = 0
        page.spacing = 0

        # 🎨 Тема
        try:
            page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=self.colors["primary"],
                    secondary=self.colors["secondary"],
                    background=self.colors["background"],
                    surface=self.colors["surface"],
                    on_primary=self.colors["text_primary"],
                    on_background=self.colors["text_secondary"]
                )
            )
        except:
            pass

        # 📱 Создание интерфейса
        self.create_ui(page)

    def create_ui(self, page: ft.Page):
        """Создание пользовательского интерфейса"""
        
        # 🔝 Заголовок приложения
        header = self.create_header()
        
        # 📱 ИСПРАВЛЕННЫЙ основной контент с фиксированной шириной сайдбара
        main_content = ft.Row(
            controls=[
                # ИСПРАВЛЕНО: Контейнер с увеличенной шириной для сайдбара с текстом
                ft.Container(
                    content=self.create_compact_sidebar(),
                    width=180,  # Увеличили ширину для иконки + текст
                    bgcolor=self.colors["surface"],
                ),
                # Тонкий разделитель
                ft.Container(
                    width=2,
                    bgcolor=self.colors["border"],
                ),
                # Контент занимает оставшееся место
                ft.Container(
                    content=self.create_content_area(),
                    expand=True,  # Расширяется на всё оставшееся место
                    bgcolor=self.colors["background"],
                )
            ],
            expand=True,
            spacing=0,
        )

        # 🖥️ Главный контейнер
        main_container = ft.Column(
            controls=[
                header,
                ft.Container(height=2, bgcolor=self.colors["border"]),  # Разделитель
                main_content
            ],
            expand=True,
            spacing=0,
        )

        page.add(main_container)
        page.update()

    def create_header(self) -> ft.Container:
        """Создание компактного заголовка"""
        
        # 🟣 Мини логотип
        logo = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            self.icons["play_circle"], 
                            color=self.colors["text_primary"], 
                            size=28
                        ),
                        bgcolor=self.colors["primary"],
                        border_radius=50,
                        width=36,
                        height=36,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        "Anivest", 
                        size=20, 
                        weight=ft.FontWeight.BOLD,
                        color=self.colors["text_primary"]
                    )
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=6, vertical=4),
        )

        # 🔍 Компактная поисковая строка
        search_field = ft.Container(
            content=ft.TextField(
                hint_text="Поиск аниме...",
                prefix_icon=self.icons["search"],
                border_color=self.colors["border"],
                focused_border_color=self.colors["primary"],
                bgcolor=self.colors["surface"],
                color=self.colors["text_primary"],
                border_radius=20,
                height=40,
                text_size=13,
                content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
            ),
            width=380,
        )

        # 👤 Компактные кнопки
        user_buttons = ft.Row(
            controls=[
                # Переключатель темы
                ft.IconButton(
                    icon=self.icons["dark_mode"],
                    icon_color=self.colors["text_muted"],
                    tooltip="Переключить тему",
                    on_click=self.toggle_theme,
                    icon_size=18,
                ),
                # Компактный профиль
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(self.icons["person"], color=self.colors["text_primary"], size=16),
                                bgcolor=self.colors["primary"],
                                border_radius=50,
                                width=28,
                                height=28,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(self.username, color=self.colors["text_primary"], size=13, weight=ft.FontWeight.W_500)
                        ],
                        spacing=8,
                    ),
                    bgcolor=self.colors["surface"],
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    on_click=self.open_profile,
                ),
                # Настройки
                ft.IconButton(
                    icon=self.icons["settings"],
                    icon_color=self.colors["text_muted"],
                    tooltip="Настройки",
                    on_click=self.open_settings,
                    icon_size=18,
                ),
                # Закрыть
                ft.IconButton(
                    icon=self.icons["close"],
                    icon_color=self.colors["text_muted"],
                    tooltip="Закрыть приложение",
                    on_click=self.close_app,
                    icon_size=18,
                ),
            ],
            spacing=6,
        )

        return ft.Container(
            content=ft.Row(
                controls=[logo, search_field, user_buttons],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.colors["surface"],
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            height=55,
        )

    def create_compact_sidebar(self) -> ft.Column:
        """Сайдбар с иконками и текстом"""
        
        # 📱 Элементы навигации (иконки + текст)
        nav_items = [
            {"icon": self.icons["home"], "text": "Главная", "page": "home"},
            {"icon": self.icons["movie"], "text": "Каталог", "page": "catalog"},
            {"icon": self.icons["favorite"], "text": "Избранное", "page": "favorites"},
            {"icon": self.icons["list"], "text": "Мой список", "page": "my_list"},
            {"icon": self.icons["download"], "text": "Загрузки", "page": "downloads"},
        ]

        profile_items = [
            {"icon": self.icons["trending_up"], "text": "Статистика", "page": "stats"},
            {"icon": self.icons["settings"], "text": "Настройки", "page": "settings"},
            {"icon": self.icons["info"], "text": "О программе", "page": "about"},
        ]

        def create_sidebar_button(item):
            is_active = item["page"] == self.current_page
            
            return ft.Container(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                item["icon"],
                                color=self.colors["text_primary"] if is_active else self.colors["text_muted"],
                                size=20,
                            ),
                            ft.Text(
                                item["text"],
                                color=self.colors["text_primary"] if is_active else self.colors["text_muted"],
                                size=14,
                                weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
                            )
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    on_click=lambda e, page=item["page"]: self.navigate_to(page),
                    ink=True,
                ),
                bgcolor=self.colors["primary"] if is_active else "transparent",
                border_radius=12,
                margin=ft.margin.symmetric(horizontal=8, vertical=2),
                height=48,  # Увеличили высоту кнопок
            )

        # Создаем кнопки навигации
        nav_buttons = [create_sidebar_button(item) for item in nav_items]
        
        # Разделитель с текстом "ПРОФИЛЬ"
        divider_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        height=1,
                        bgcolor=self.colors["border"],
                        margin=ft.margin.symmetric(horizontal=16, vertical=8),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "ПРОФИЛЬ",
                            size=11,
                            color=self.colors["text_muted"],
                            weight=ft.FontWeight.W_600,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=4),
                    )
                ],
                spacing=0,
            ),
        )
        
        profile_buttons = [create_sidebar_button(item) for item in profile_items]

        # Собираем сайдбар
        return ft.Column(
            controls=[
                ft.Container(height=12),  # Отступ сверху
                *nav_buttons,
                divider_section,
                *profile_buttons,
                ft.Container(height=12),  # Отступ снизу
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    def create_content_area(self) -> ft.Column:
        """Создание области основного контента"""
        
        # В зависимости от текущей страницы показываем разный контент
        if self.current_page == "home":
            content = self.create_improved_home_page()
        elif self.current_page == "catalog":
            content = self.create_catalog_page()
        elif self.current_page == "favorites":
            content = self.create_favorites_page()
        else:
            content = self.create_placeholder_page()

        # ИСПРАВЛЕНО: возвращаем контент напрямую с отступами
        return ft.Container(
            content=content,
            padding=35,  # Больше отступов благодаря супер-узкому сайдбару
            expand=True,
        )

    def create_improved_home_page(self) -> ft.Column:
        """УЛУЧШЕННАЯ главная страница с большим пространством"""
        
        # 🔥 Карточки аниме с увеличенным размером
        popular_cards = []
        anime_titles = [
            ("Attack on Titan", "9.2", "24 эп"),
            ("Demon Slayer", "8.5", "12 эп"),
            ("Jujutsu Kaisen", "8.8", "24 эп"),
            ("One Piece", "9.0", "1000+ эп"),
            ("Naruto", "8.3", "220 эп"),
            ("Death Note", "9.1", "37 эп"),
            ("My Hero Academia", "8.7", "150+ эп"),
            ("Tokyo Ghoul", "8.1", "48 эп"),
        ]

        for title, rating, episodes in anime_titles:
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        # Увеличенный постер
                        ft.Container(
                            content=ft.Stack(
                                controls=[
                                    ft.Container(
                                        bgcolor=self.colors["card"],
                                        border_radius=15,
                                        width=190,
                                        height=250,
                                    ),
                                    ft.Container(
                                        content=ft.Icon(
                                            self.icons["movie"], 
                                            size=65, 
                                            color=self.colors["text_muted"]
                                        ),
                                        alignment=ft.alignment.center,
                                        width=190,
                                        height=250,
                                    ),
                                    # Градиент снизу
                                    ft.Container(
                                        bgcolor=self.colors["background"] + "90",
                                        border_radius=ft.border_radius.only(
                                            bottom_left=15, bottom_right=15
                                        ),
                                        width=190,
                                        height=70,
                                        alignment=ft.alignment.bottom_center,
                                    )
                                ]
                            ),
                            width=190,
                            height=250,
                            border_radius=15,
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=20,
                                color=self.colors["shadow"],
                                offset=ft.Offset(0, 8),
                            ),
                        ),
                        # Информация
                        ft.Column(
                            controls=[
                                ft.Text(
                                    title, 
                                    size=15, 
                                    weight=ft.FontWeight.W_600,
                                    color=self.colors["text_primary"],
                                    text_align=ft.TextAlign.CENTER,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(self.icons["star"], color=self.colors["accent"], size=16),
                                            ft.Text(rating, color=self.colors["text_secondary"], size=13, weight=ft.FontWeight.W_500),
                                            ft.Text("•", color=self.colors["text_muted"], size=13),
                                            ft.Text(episodes, color=self.colors["text_secondary"], size=13),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=6,
                                    ),
                                    bgcolor=self.colors["surface"],
                                    border_radius=25,
                                    padding=ft.padding.symmetric(horizontal=15, vertical=6),
                                )
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ],
                    spacing=15,
                ),
                width=190,
                on_click=lambda e, t=title: self.open_anime(t),
                ink=True,
                border_radius=15,
                padding=10,
                bgcolor="transparent",
            )
            popular_cards.append(card)

        # 📱 Улучшенные секции
        def create_wide_section(title, emoji, cards):
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"{emoji} {title}", 
                                    size=24, 
                                    weight=ft.FontWeight.BOLD,
                                    color=self.colors["text_primary"]
                                ),
                                ft.Container(
                                    content=ft.TextButton(
                                        "Смотреть все →", 
                                        on_click=lambda e: self.navigate_to("catalog"),
                                        style=ft.ButtonStyle(
                                            color=self.colors["primary"],
                                        )
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            content=ft.Row(
                                controls=cards,
                                spacing=30,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                            padding=ft.padding.symmetric(vertical=15),
                        )
                    ],
                    spacing=20,
                ),
                bgcolor=self.colors["surface"],
                border_radius=20,
                padding=25,
                margin=ft.margin.symmetric(vertical=15),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=25,
                    color=self.colors["shadow"],
                    offset=ft.Offset(0, 8),
                ),
            )

        # Показываем больше карточек благодаря освобожденному пространству
        popular_section = create_wide_section("Популярные сейчас", "🔥", popular_cards[:6])
        new_section = create_wide_section("Новинки сезона ❄️ Зима 2025", "🆕", popular_cards[2:8])

        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Добро пожаловать в Anivest!", 
                                size=36,
                                weight=ft.FontWeight.BOLD,
                                color=self.colors["text_primary"]
                            ),
                            ft.Text(
                                "Смотрите аниме в лучшем качестве • Сайдбар с иконками и текстом • Удобная навигация", 
                                size=18, 
                                color=self.colors["text_secondary"]
                            ),
                        ]
                    ),
                    margin=ft.margin.only(bottom=25),
                ),
                popular_section,
                new_section,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    def create_catalog_page(self) -> ft.Column:
        """Страница каталога"""
        return ft.Column(
            controls=[
                ft.Text(
                    "📺 Каталог аниме", 
                    size=32, 
                    weight=ft.FontWeight.BOLD,
                    color=self.colors["text_primary"]
                ),
                ft.Text(
                    "Поиск и фильтрация аниме • Исправленный мини-сайдбар освобождает место", 
                    size=18, 
                    color=self.colors["text_secondary"]
                ),
                ft.Container(height=25),
                ft.Container(
                    content=ft.Text("Здесь будет расширенная сетка аниме...", color=self.colors["text_muted"], size=18),
                    alignment=ft.alignment.center,
                    height=300,
                    bgcolor=self.colors["surface"],
                    border_radius=15,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def create_favorites_page(self) -> ft.Column:
        """Страница избранного"""
        return ft.Column(
            controls=[
                ft.Text(
                    "⭐ Избранное", 
                    size=32, 
                    weight=ft.FontWeight.BOLD,
                    color=self.colors["text_primary"]
                ),
                ft.Text(
                    "Ваши любимые аниме • Исправленный мини-сайдбар = намного больше места", 
                    size=18, 
                    color=self.colors["text_secondary"]
                ),
                ft.Container(height=50),
                ft.Container(
                    content=ft.Text("Намного больше места для избранных аниме!", color=self.colors["primary"], size=20),
                    alignment=ft.alignment.center,
                    height=300,
                    bgcolor=self.colors["surface"],
                    border_radius=15,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def create_placeholder_page(self) -> ft.Column:
        """Создание страницы-заглушки"""
        return ft.Column(
            controls=[
                ft.Text(
                    "🚧 В разработке", 
                    size=32, 
                    weight=ft.FontWeight.BOLD,
                    color=self.colors["text_primary"]
                ),
                ft.Text(
                    "Эта страница еще в разработке • Исправленный мини-сайдбар готов!", 
                    size=18, 
                    color=self.colors["text_secondary"]
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # 🎛️ Обработчики событий
    def navigate_to(self, page_name: str):
        """Навигация между страницами"""
        self.current_page = page_name
        if self.page:
            self.page.clean()
            self.create_ui(self.page)
        print(f"🔄 Навигация на страницу: {page_name} (сайдбар с текстом)")

    def toggle_theme(self, e):
        """Переключение темы"""
        print("🎨 Переключение темы (сайдбар с текстом)")

    def open_profile(self, e):
        """Открыть профиль"""
        print("👤 Открыть профиль (сайдбар с текстом)")

    def open_settings(self, e):
        """Открыть настройки"""
        self.navigate_to("settings")

    def close_app(self, e):
        """Закрыть приложение"""
        try:
            e.page.window.close()
        except:
            try:
                e.page.window_close()
            except:
                import sys
                sys.exit()

    def open_anime(self, title: str):
        """Открыть страницу аниме"""
        print(f"🎬 Открыть аниме: {title} (намного больше места благодаря исправленному узкому сайдбару)")


def main(page: ft.Page):
    """Точка входа в приложение"""
    app = AnivesetDesktop()
    app.main(page)


if __name__ == "__main__":
    print("🚀 Запуск Anivest Desktop - САЙДБАР С ИКОНКАМИ И ТЕКСТОМ")
    print("✅ Добавлены подписи к кнопкам навигации")
    print("📱 Ширина сайдбара: 180px (иконка + текст)")
    print("🎯 Увеличенные кнопки 48px высотой")
    print("🔧 Жесткие ограничения: 1200x800 - 1920x1080")
    print("⭐ Удобная навигация с подписями!")
    
    # Запуск приложения
    ft.app(target=main)