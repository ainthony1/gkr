"""
Theme system for Got Key'd Realty Commission Tracker.
Provides ThemeManager with light/dark mode support and consistent styling primitives.
"""
import customtkinter as ctk
from core.constants import get_resource_path
import os


# ── Color Palettes ──

LIGHT_COLORS = {
    'PRIMARY': '#2563EB',
    'PRIMARY_HOVER': '#1D4ED8',
    'PRIMARY_LIGHT': '#EFF6FF',
    'SIDEBAR_BG': '#1E3A5F',
    'SIDEBAR_HOVER': '#264A73',
    'SIDEBAR_TEXT': '#CBD5E1',
    'SIDEBAR_TEXT_ACTIVE': '#FFFFFF',
    'CONTENT_BG': '#F8FAFC',
    'CARD_BG': '#FFFFFF',
    'CARD_BORDER': '#E2E8F0',
    'TEXT_PRIMARY': '#1E293B',
    'TEXT_SECONDARY': '#64748B',
    'TEXT_MUTED': '#94A3B8',
    'SUCCESS': '#16A34A',
    'SUCCESS_HOVER': '#15803D',
    'DANGER': '#DC2626',
    'DANGER_HOVER': '#B91C1C',
    'ROW_ALT': '#F1F5F9',
    'SECTION_BG': '#F1F5F9',
    'INPUT_BORDER': '#CBD5E1',
    'INPUT_FOCUS': '#2563EB',
}

DARK_COLORS = {
    'PRIMARY': '#3B82F6',
    'PRIMARY_HOVER': '#2563EB',
    'PRIMARY_LIGHT': '#1E3A5F',
    'SIDEBAR_BG': '#0F172A',
    'SIDEBAR_HOVER': '#1E293B',
    'SIDEBAR_TEXT': '#94A3B8',
    'SIDEBAR_TEXT_ACTIVE': '#FFFFFF',
    'CONTENT_BG': '#1A1F2E',
    'CARD_BG': '#242937',
    'CARD_BORDER': '#334155',
    'TEXT_PRIMARY': '#F1F5F9',
    'TEXT_SECONDARY': '#94A3B8',
    'TEXT_MUTED': '#64748B',
    'SUCCESS': '#22C55E',
    'SUCCESS_HOVER': '#16A34A',
    'DANGER': '#EF4444',
    'DANGER_HOVER': '#DC2626',
    'ROW_ALT': '#1E2433',
    'SECTION_BG': '#1E2433',
    'INPUT_BORDER': '#475569',
    'INPUT_FOCUS': '#3B82F6',
}


class ThemeManager:
    """Singleton theme manager. On toggle, app rebuilds current page (no observer pattern needed)."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._mode = 'light'

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value in ('light', 'dark'):
            self._mode = value

    def get_colors(self) -> dict:
        return LIGHT_COLORS.copy() if self._mode == 'light' else DARK_COLORS.copy()

    def toggle(self):
        """Toggle between light and dark mode. Returns new colors dict."""
        self._mode = 'dark' if self._mode == 'light' else 'light'
        return self.get_colors()


# Module-level convenience
_theme = ThemeManager()


def get_theme_manager() -> ThemeManager:
    return _theme


def get_colors() -> dict:
    return _theme.get_colors()


# ── Font Factories (reduced sizes per spec) ──

def font_display(size=24):
    """Page title font."""
    return ctk.CTkFont(size=size, weight="bold")


def font_heading(size=16):
    """Section heading font."""
    return ctk.CTkFont(size=size, weight="bold")


def font_subheading(size=14):
    """Card title / subsection font."""
    return ctk.CTkFont(size=size, weight="bold")


def font_body(size=13):
    """Standard body text."""
    return ctk.CTkFont(size=size)


def font_caption(size=11):
    """Small captions and labels."""
    return ctk.CTkFont(size=size)


def font_label(size=12):
    """Form labels — medium weight."""
    return ctk.CTkFont(size=size, weight="bold")


def font_mono(size=14):
    """Monospaced for financial figures."""
    import sys
    if sys.platform == 'darwin':
        family = "Menlo"
    elif sys.platform == 'win32':
        family = "Consolas"
    else:
        family = "Courier"
    return ctk.CTkFont(family=family, size=size, weight="bold")


# ── Widget Factories ──
# All factories call get_colors() internally so they always reflect current theme.

def page_title(parent, text):
    """Large page title label."""
    c = get_colors()
    return ctk.CTkLabel(
        parent, text=text,
        font=font_display(24),
        text_color=c['TEXT_PRIMARY'],
    )


def section_label(parent, text):
    """Blue-accented section header."""
    c = get_colors()
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    accent = ctk.CTkFrame(frame, width=4, height=20, fg_color=c['PRIMARY'], corner_radius=2)
    accent.pack(side="left", padx=(0, 10))

    ctk.CTkLabel(
        frame, text=text.upper(),
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=c['TEXT_SECONDARY'],
    ).pack(side="left")

    return frame


def card(parent, **kwargs):
    """Styled card frame with border and rounded corners."""
    c = get_colors()
    return ctk.CTkFrame(
        parent,
        fg_color=c['CARD_BG'],
        corner_radius=10,
        border_width=1,
        border_color=c['CARD_BORDER'],
        **kwargs,
    )


def input_field(parent, label_text, width=350, placeholder="", default=""):
    """Labeled input field with consistent styling."""
    c = get_colors()
    container = ctk.CTkFrame(parent, fg_color="transparent")

    ctk.CTkLabel(
        container, text=label_text,
        font=font_label(12),
        text_color=c['TEXT_SECONDARY'],
    ).pack(anchor="w", pady=(0, 4))

    entry = ctk.CTkEntry(
        container, width=width, height=36,
        font=font_body(13),
        corner_radius=8,
        border_width=1,
        border_color=c['INPUT_BORDER'],
        fg_color=c['CARD_BG'],
        placeholder_text=placeholder,
    )
    if default:
        entry.insert(0, default)
    entry.pack(anchor="w")

    return container, entry


def primary_button(parent, text, command, width=100):
    """Blue pill primary button (34px height, full radius)."""
    c = get_colors()
    btn = ctk.CTkButton(
        parent, text=text,
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color=c['PRIMARY'],
        hover_color=c['PRIMARY_HOVER'],
        text_color='#FFFFFF',
        height=34,
        width=max(width, 100),
        corner_radius=17,
        command=command,
    )
    return btn


def success_button(parent, text, command, width=100):
    """Green pill success button."""
    c = get_colors()
    return ctk.CTkButton(
        parent, text=text,
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color=c['SUCCESS'],
        hover_color=c['SUCCESS_HOVER'],
        text_color='#FFFFFF',
        height=34,
        width=max(width, 100),
        corner_radius=17,
        command=command,
    )


def secondary_button(parent, text, command, width=100):
    """Outlined pill secondary button."""
    c = get_colors()
    return ctk.CTkButton(
        parent, text=text,
        font=font_body(13),
        fg_color="transparent",
        hover_color=c['PRIMARY_LIGHT'],
        text_color=c['PRIMARY'],
        border_width=1,
        border_color=c['PRIMARY'],
        height=32,
        width=max(width, 100),
        corner_radius=16,
        command=command,
    )


def danger_button(parent, text, command, width=100):
    """Red pill danger button."""
    c = get_colors()
    return ctk.CTkButton(
        parent, text=text,
        font=font_body(13),
        fg_color=c['DANGER'],
        hover_color=c['DANGER_HOVER'],
        text_color='#FFFFFF',
        height=34,
        width=max(width, 100),
        corner_radius=17,
        command=command,
    )


def ghost_button(parent, text, command, width=100):
    """Subtle ghost button — no border, no background."""
    c = get_colors()
    return ctk.CTkButton(
        parent, text=text,
        font=font_body(13),
        fg_color="transparent",
        hover_color=c['SECTION_BG'],
        text_color=c['TEXT_SECONDARY'],
        height=32,
        width=max(width, 100),
        corner_radius=16,
        command=command,
    )


def badge(parent, text, color=None):
    """Small colored pill badge."""
    c = get_colors()
    bg = color or c['SUCCESS']
    return ctk.CTkLabel(
        parent, text=f"  {text}  ",
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color='#FFFFFF',
        fg_color=bg,
        corner_radius=10,
        height=22,
    )


def separator(parent):
    """Thin separator line."""
    c = get_colors()
    return ctk.CTkFrame(parent, height=1, fg_color=c['CARD_BORDER'])


def stat_block(parent, label, value, value_color=None):
    """Vertical stat display (label above, value below)."""
    c = get_colors()
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    ctk.CTkLabel(
        frame, text=label.upper(),
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=c['TEXT_MUTED'],
    ).pack()

    ctk.CTkLabel(
        frame, text=value,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=value_color or c['TEXT_PRIMARY'],
    ).pack(pady=(2, 0))

    return frame


# ── Icon Loading ──

def load_nav_icon(name, size=(20, 20)):
    """Load a nav icon as CTkImage with light/dark variants.

    Light variant (white) used on dark sidebar.
    Returns CTkImage or None if files not found.
    """
    light_path = get_resource_path(os.path.join('assets', 'icons', f'{name}.png'))
    dark_path = get_resource_path(os.path.join('assets', 'icons', f'{name}_dark.png'))

    try:
        from PIL import Image
        light_img = Image.open(light_path)
        dark_img = Image.open(dark_path) if os.path.exists(dark_path) else light_img
        return ctk.CTkImage(light_image=light_img, dark_image=dark_img, size=size)
    except Exception:
        return None
