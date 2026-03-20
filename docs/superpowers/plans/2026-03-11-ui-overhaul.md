# UI Overhaul Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete visual rework of the Got Key'd Realty commission tracker — replace warm gold/charcoal palette with blue/white brand colors, add dark mode, implement collapsible animated sidebar with top bar, redesign all components, and add smooth transitions.

**Architecture:** ThemeManager singleton holds light/dark palettes; on toggle, the app shell rebuilds and re-shows the current page (frames pick up new colors at construction time). Sidebar uses grid layout for smooth width animation via `after()`. All UI colors move from constants.py to theme.py's ThemeManager.

**Deferred (not in this plan):** Page slide transitions (spec Section 7), micro-animations (hover color transitions, button click feedback, loading ellipsis), card shadow simulation, and collapsed sidebar tooltips. These are polish items that can be added in a follow-up pass without affecting the core rework.

**Tech Stack:** Python 3.14, CustomTkinter, SQLite, Pillow (CTkImage), fpdf2 (unchanged)

**Spec:** `docs/superpowers/specs/2026-03-11-ui-overhaul-design.md`

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `src/ui/theme.py` | Complete rewrite — `ThemeManager` class, light/dark color palettes, font factories, widget factories |
| `assets/icons/*.png` | 20x20 nav icons (home, document, clock, people, calculator, sun, moon, chevron-left, chevron-right) |

### Modified Files
| File | Changes |
|------|---------|
| `src/core/constants.py` | Remove all UI color constants (lines 9-38). Keep PDF RGB tuples, company info, path utils, app info |
| `src/app.py` | Full rewrite of `_build_layout()` — grid-based sidebar with collapse animation, top bar, page slide transitions |
| `src/ui/dashboard_frame.py` | Use ThemeManager colors, compact stat cards with blue accents, add `apply_theme()` |
| `src/ui/agent_select_frame.py` | Use ThemeManager colors, card-based agent display, add `apply_theme()` |
| `src/ui/transaction_form.py` | Use ThemeManager colors, compact form inputs, pill buttons, add `apply_theme()` |
| `src/ui/review_frame.py` | Use ThemeManager colors, clean summary cards, add `apply_theme()` |
| `src/ui/history_frame.py` | Use ThemeManager colors, modern table with hover, add `apply_theme()` |
| `src/ui/agent_manage_frame.py` | Use ThemeManager colors, underline tabs, compact forms, add `apply_theme()` |
| `src/ui/taxes_frame.py` | Use ThemeManager colors, updated table and badges, add `apply_theme()` |
| `src/core/database.py` | No schema changes needed — `app_settings` table already exists with `get_setting`/`set_setting` |

---

## Chunk 1: Theme System + Constants Cleanup

### Task 1: Create Icon Assets

**Files:**
- Create: `assets/icons/home.png`, `assets/icons/home_dark.png`
- Create: `assets/icons/document.png`, `assets/icons/document_dark.png`
- Create: `assets/icons/clock.png`, `assets/icons/clock_dark.png`
- Create: `assets/icons/people.png`, `assets/icons/people_dark.png`
- Create: `assets/icons/calculator.png`, `assets/icons/calculator_dark.png`
- Create: `assets/icons/sun.png`, `assets/icons/moon.png`
- Create: `assets/icons/chevron_left.png`, `assets/icons/chevron_right.png`

Icons are 20x20 PNG files with transparent backgrounds. Light variants are white (for dark sidebar). Dark variants are slate-colored (for potential light usage). Sun/moon/chevron icons only need one variant each (white).

- [ ] **Step 1: Create icon generation script**

Create a Python script that generates simple geometric icons using Pillow. This avoids needing external icon files and keeps the build self-contained.

```python
# generate_icons.py (temporary script, run once)
from PIL import Image, ImageDraw
import os

ICON_SIZE = 20
ICON_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'icons')
os.makedirs(ICON_DIR, exist_ok=True)

def make_icon(name, draw_func, color):
    img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, color)
    img.save(os.path.join(ICON_DIR, f'{name}.png'))

def draw_home(draw, color):
    # Simple house shape
    draw.polygon([(10, 2), (18, 9), (15, 9), (15, 17), (5, 17), (5, 9), (2, 9)], fill=color)
    draw.rectangle([8, 12, 12, 17], fill=(0, 0, 0, 0))  # Door cutout

def draw_document(draw, color):
    draw.rectangle([4, 1, 16, 19], fill=color, outline=color)
    draw.rectangle([6, 5, 14, 7], fill=(0, 0, 0, 0))
    draw.rectangle([6, 9, 14, 11], fill=(0, 0, 0, 0))
    draw.rectangle([6, 13, 11, 15], fill=(0, 0, 0, 0))

def draw_clock(draw, color):
    draw.ellipse([1, 1, 19, 19], outline=color, width=2)
    draw.line([(10, 10), (10, 5)], fill=color, width=2)
    draw.line([(10, 10), (14, 10)], fill=color, width=2)

def draw_people(draw, color):
    # Two person silhouettes
    draw.ellipse([3, 2, 9, 8], fill=color)
    draw.ellipse([2, 10, 10, 18], fill=color)
    draw.ellipse([11, 2, 17, 8], fill=color)
    draw.ellipse([10, 10, 18, 18], fill=color)

def draw_calculator(draw, color):
    draw.rectangle([3, 1, 17, 19], fill=color, outline=color)
    draw.rectangle([5, 3, 15, 8], fill=(0, 0, 0, 0))
    for r in range(3):
        for c in range(3):
            x = 5 + c * 4
            y = 10 + r * 3
            draw.rectangle([x, y, x + 2, y + 2], fill=(0, 0, 0, 0))

def draw_sun(draw, color):
    draw.ellipse([5, 5, 15, 15], fill=color)
    for angle_start in range(0, 360, 45):
        import math
        rad = math.radians(angle_start)
        x1 = 10 + 8 * math.cos(rad)
        y1 = 10 + 8 * math.sin(rad)
        x2 = 10 + 6 * math.cos(rad)
        y2 = 10 + 6 * math.sin(rad)
        draw.line([(x2, y2), (x1, y1)], fill=color, width=2)

def draw_moon(draw, color):
    draw.ellipse([3, 2, 17, 18], fill=color)
    draw.ellipse([6, 1, 18, 15], fill=(0, 0, 0, 0))

def draw_chevron_left(draw, color):
    draw.line([(13, 3), (7, 10), (13, 17)], fill=color, width=2)

def draw_chevron_right(draw, color):
    draw.line([(7, 3), (13, 10), (7, 17)], fill=color, width=2)

WHITE = (255, 255, 255, 255)
SLATE = (148, 163, 184, 255)  # Slate-400

icons = [
    ('home', draw_home), ('document', draw_document), ('clock', draw_clock),
    ('people', draw_people), ('calculator', draw_calculator),
]

for name, func in icons:
    make_icon(name, func, WHITE)
    make_icon(f'{name}_dark', func, SLATE)

make_icon('sun', draw_sun, WHITE)
make_icon('moon', draw_moon, WHITE)
make_icon('chevron_left', draw_chevron_left, WHITE)
make_icon('chevron_right', draw_chevron_right, WHITE)

print(f"Generated icons in {ICON_DIR}")
```

- [ ] **Step 2: Run icon generation script**

Run: `cd /Users/anthony/Desktop/Work/commission\ thingy/commission_tracker && source venv/bin/activate && python generate_icons.py`
Expected: "Generated icons in .../assets/icons" and PNG files appear in `assets/icons/`

- [ ] **Step 3: Verify icon files exist**

Run: `ls -la assets/icons/`
Expected: 12 PNG files (home, home_dark, document, document_dark, clock, clock_dark, people, people_dark, calculator, calculator_dark, sun, moon, chevron_left, chevron_right)

- [ ] **Step 4: Delete temporary script**

Run: `rm generate_icons.py`

- [ ] **Step 5: Commit icons**

```bash
git add assets/icons/
git commit -m "feat: add sidebar navigation icon assets"
```

---

### Task 2: Rewrite ThemeManager in theme.py

**Files:**
- Rewrite: `src/ui/theme.py` (currently 215 lines → ~350 lines)

This is the foundation for everything else. The new theme.py contains:
1. `ThemeManager` singleton class with light/dark palettes
2. `get_colors()` function that returns current theme dict
3. Updated font factories (reduced sizes per spec)
4. Updated widget factories that use `get_colors()` internally

- [ ] **Step 1: Write the new theme.py**

```python
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
        return ctk.CTkImage(light_image=dark_img, dark_image=light_img, size=size)
    except Exception:
        return None
```

- [ ] **Step 2: Verify theme.py loads without errors**

Run: `cd /Users/anthony/Desktop/Work/commission\ thingy/commission_tracker && source venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); from ui.theme import get_colors, ThemeManager, get_theme_manager; c = get_colors(); print(f'Light PRIMARY: {c[\"PRIMARY\"]}'); tm = get_theme_manager(); tm.toggle(); c2 = get_colors(); print(f'Dark PRIMARY: {c2[\"PRIMARY\"]}')"`

Expected:
```
Light PRIMARY: #2563EB
Dark PRIMARY: #3B82F6
```

- [ ] **Step 3: Commit theme.py**

```bash
git add src/ui/theme.py
git commit -m "feat: rewrite theme.py with ThemeManager, light/dark palettes, and updated widget factories"
```

---

### Task 3: Clean Up constants.py

**Files:**
- Modify: `src/core/constants.py:9-38` (remove UI color constants)

- [ ] **Step 1: Remove UI color lines from constants.py**

Remove lines 9-38 (all hex color constants from `NAVY` through `BADGE_GRAY`). Keep everything else:
- Lines 1-8: imports, company info
- Lines 40-47: PDF RGB tuples
- Lines 49-85: APP_NAME, APP_VERSION, path functions, DB_PATH, LOGO_PATH

The resulting file should look like:

```python
import os
import sys

# Company Info
COMPANY_NAME = "GOT KEY'D REALTY"
COMPANY_ADDRESS = "22260 Garrison St, Dearborn, MI 48124"
COMPANY_PHONE = "(313) 228-5710"

# PDF colors as RGB tuples (used by pdf_generator.py — NOT UI colors)
NAVY_RGB = (27, 58, 92)
BLUE_RGB = (46, 117, 182)
DARK_TEXT_RGB = (45, 45, 45)
GRAY_TEXT_RGB = (102, 102, 102)
LIGHT_BG_RGB = (244, 247, 250)
ROW_ALT_RGB = (232, 238, 228)
WHITE_RGB = (255, 255, 255)

# App info
APP_NAME = "Got Key'd Commission Tracker"
APP_VERSION = "1.0.0"


def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Go up from src/core/ to project root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def get_data_dir() -> str:
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.path.join(os.path.expanduser('~'), '.local', 'share')
    data_dir = os.path.join(base, 'GotKeydRealty')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_output_dir() -> str:
    """User-visible output directory for invoices and 1099s (Documents folder)."""
    docs = os.path.join(os.path.expanduser('~'), 'Documents')
    out_dir = os.path.join(docs, 'GotKeyd Realty')
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


DB_PATH = os.path.join(get_data_dir(), 'commission_tracker.db')
LOGO_PATH = get_resource_path(os.path.join('assets', 'logo.png'))
```

- [ ] **Step 2: Verify constants.py is valid**

Run: `cd /Users/anthony/Desktop/Work/commission\ thingy/commission_tracker && python -c "import sys; sys.path.insert(0, 'src'); from core.constants import COMPANY_NAME, NAVY_RGB, DB_PATH, get_resource_path, get_output_dir; print('OK', COMPANY_NAME, NAVY_RGB)"`

Expected: `OK GOT KEY'D REALTY (27, 58, 92)`

- [ ] **Step 3: Verify pdf_generator still imports correctly**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from generators.pdf_generator import generate_both_invoices; print('PDF generator imports OK')"`

Expected: `PDF generator imports OK`

- [ ] **Step 4: Commit constants cleanup**

```bash
git add src/core/constants.py
git commit -m "refactor: remove UI color constants from constants.py (moved to theme.py)"
```

---

## Chunk 2: App Shell — Sidebar + Top Bar + Page Transitions

### Task 4: Rewrite app.py — Grid Layout, Sidebar, Top Bar, Transitions

**Files:**
- Rewrite: `src/app.py` (currently 394 lines → ~600 lines)

This is the biggest single task. The new app.py needs:
1. Grid-based layout (sidebar col 0, content col 1)
2. Collapsible sidebar with 250ms ease-out animation
3. Top bar that shows nav pills when sidebar is collapsed
4. Slide page transitions (200ms)
5. Dark mode toggle in sidebar
6. Theme persistence (sidebar_collapsed, theme_mode in app_settings)

- [ ] **Step 1: Write the new app.py**

The full rewritten `app.py`:

```python
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import date

from core.constants import APP_NAME, DB_PATH, LOGO_PATH
from core.database import Database
from core.commission_engine import calculate_commission, get_cap_year
from generators.pdf_generator import generate_both_invoices
from utils.import_agents import import_from_excel
from ui.theme import (
    get_colors, get_theme_manager, load_nav_icon,
    font_display, font_heading, font_body, font_caption,
)


# ── Animation Constants ──
SIDEBAR_EXPANDED = 220
SIDEBAR_COLLAPSED = 60
SIDEBAR_ANIM_DURATION = 250  # ms
SIDEBAR_ANIM_STEPS = 15
LABEL_HIDE_THRESHOLD = 150
TOP_BAR_HEIGHT = 48


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1050x750")
        self.minsize(950, 650)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.db = Database(DB_PATH)
        self._ensure_agents_imported()

        # State
        self._pending_agent = None
        self._pending_result = None
        self._pending_invoice_num = None
        self._pending_invoice_date = None
        self._pending_address = None
        self._pending_payment = None
        self._pending_form_data = None

        # Sidebar state
        self._sidebar_expanded = True
        self._sidebar_animating = False
        self._current_sidebar_width = SIDEBAR_EXPANDED
        self._current_page = None
        self._current_nav = "home"

        # Theme
        self._tm = get_theme_manager()
        saved_mode = self.db.get_setting('theme_mode', 'light')
        if saved_mode == 'dark':
            self._tm.mode = 'dark'
            ctk.set_appearance_mode("dark")

        saved_collapsed = self.db.get_setting('sidebar_collapsed', '0')
        if saved_collapsed == '1':
            self._sidebar_expanded = False
            self._current_sidebar_width = SIDEBAR_COLLAPSED

        self._build_layout()
        self.show_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ── Agent Import ──

    def _ensure_agents_imported(self):
        if self.db.agent_count() == 0:
            excel_path = self._find_excel()
            if excel_path:
                count = import_from_excel(self.db, excel_path)
                print(f"Imported {count} agents from Excel")
            else:
                messagebox.showwarning(
                    "No Agent Data",
                    "Could not find agent_info.xlsx. Place it next to the application."
                )

    def _find_excel(self) -> str | None:
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent_info.xlsx'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_info.xlsx'),
            os.path.join(os.getcwd(), 'agent_info.xlsx'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        path = filedialog.askopenfilename(
            title="Select agent_info.xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        return path if path else None

    # ── Layout ──

    def _build_layout(self):
        c = get_colors()

        # Grid: col 0 = sidebar, col 1 = main
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=self._current_sidebar_width)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(self, fg_color=c['SIDEBAR_BG'], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)
        self.sidebar.configure(width=self._current_sidebar_width)

        self._build_sidebar(c)

        # ── Right column: top bar + content ──
        self.right_col = ctk.CTkFrame(self, fg_color=c['CONTENT_BG'], corner_radius=0)
        self.right_col.grid(row=0, column=1, sticky="nsew")
        self.right_col.grid_rowconfigure(1, weight=1)
        self.right_col.grid_columnconfigure(0, weight=1)

        # Top bar
        self.top_bar = ctk.CTkFrame(
            self.right_col, height=TOP_BAR_HEIGHT,
            fg_color=c['CARD_BG'], corner_radius=0,
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.pack_propagate(False)

        # Bottom border on top bar
        self.top_bar_border = ctk.CTkFrame(
            self.right_col, height=1, fg_color=c['CARD_BORDER'], corner_radius=0,
        )
        self.top_bar_border.grid(row=0, column=0, sticky="sew")

        self._build_top_bar(c)

        # Content area
        self.content = ctk.CTkFrame(self.right_col, fg_color=c['CONTENT_BG'], corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")

    def _build_sidebar(self, c):
        for w in self.sidebar.winfo_children():
            w.destroy()

        expanded = self._sidebar_expanded

        # Brand block
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=12 if expanded else 8, pady=(20, 0))

        if expanded:
            ctk.CTkLabel(
                brand_frame, text="GOT KEY'D",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color='#FFFFFF',
            ).pack(anchor="w")
            ctk.CTkLabel(
                brand_frame, text="REALTY",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=c['PRIMARY'],
            ).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(
                brand_frame, text="Commission Tracker",
                font=ctk.CTkFont(size=10),
                text_color=c['SIDEBAR_TEXT'],
            ).pack(anchor="w")
        else:
            # Collapsed: show "GK" mark
            ctk.CTkLabel(
                brand_frame, text="GK",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color='#FFFFFF',
            ).pack(anchor="center")

        # Nav items
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=(24, 0))

        self.nav_buttons = {}
        self._nav_icons = {}
        nav_items = [
            ("home", "Dashboard", "home", self.show_dashboard),
            ("invoices", "Invoices", "document", self.show_invoices),
            ("history", "History", "clock", self.show_all_history),
            ("agents", "Manage Agents", "people", self.show_agent_manager),
            ("taxes", "Taxes", "calculator", self.show_taxes),
        ]

        for name, label, icon_name, cmd in nav_items:
            icon = load_nav_icon(icon_name)
            self._nav_icons[name] = icon

            is_active = (name == self._current_nav)
            fg = c['SIDEBAR_HOVER'] if is_active else "transparent"
            text_c = c['SIDEBAR_TEXT_ACTIVE'] if is_active else c['SIDEBAR_TEXT']

            if expanded:
                btn_text = f"  {label}" if icon else f"  {label}"
                btn = ctk.CTkButton(
                    nav_frame, text=btn_text,
                    image=icon,
                    font=ctk.CTkFont(size=13),
                    fg_color=fg,
                    text_color=text_c,
                    hover_color=c['SIDEBAR_HOVER'],
                    anchor="w",
                    height=40,
                    corner_radius=8,
                    command=cmd,
                    compound="left",
                )
            else:
                btn = ctk.CTkButton(
                    nav_frame, text="",
                    image=icon,
                    font=ctk.CTkFont(size=13),
                    fg_color=fg,
                    text_color=text_c,
                    hover_color=c['SIDEBAR_HOVER'],
                    width=40, height=40,
                    corner_radius=8,
                    command=cmd,
                )

            btn.pack(fill="x" if expanded else None, pady=1, anchor="center" if not expanded else "w")
            self.nav_buttons[name] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Dark mode toggle
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=8, pady=(0, 8))

        moon_icon = load_nav_icon('moon')
        sun_icon = load_nav_icon('sun')
        theme_icon = moon_icon if self._tm.mode == 'light' else sun_icon

        if expanded:
            theme_text = "Dark Mode" if self._tm.mode == 'light' else "Light Mode"
            self.theme_btn = ctk.CTkButton(
                bottom_frame, text=f"  {theme_text}",
                image=theme_icon,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                text_color=c['SIDEBAR_TEXT'],
                hover_color=c['SIDEBAR_HOVER'],
                anchor="w", height=36, corner_radius=8,
                command=self._toggle_theme,
                compound="left",
            )
        else:
            self.theme_btn = ctk.CTkButton(
                bottom_frame, text="",
                image=theme_icon,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                text_color=c['SIDEBAR_TEXT'],
                hover_color=c['SIDEBAR_HOVER'],
                width=40, height=36, corner_radius=8,
                command=self._toggle_theme,
            )
        self.theme_btn.pack(fill="x" if expanded else None, pady=1, anchor="center" if not expanded else "w")

        # Collapse/expand button
        chevron_icon = load_nav_icon('chevron_left') if expanded else load_nav_icon('chevron_right')
        collapse_text = "" if not expanded else ""
        self.collapse_btn = ctk.CTkButton(
            bottom_frame, text=collapse_text,
            image=chevron_icon,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=c['SIDEBAR_TEXT'],
            hover_color=c['SIDEBAR_HOVER'],
            width=40, height=36, corner_radius=8,
            command=self._toggle_sidebar,
        )
        self.collapse_btn.pack(fill="x" if expanded else None, pady=(1, 4), anchor="center" if not expanded else "w")

        # Version footer
        if expanded:
            footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            footer.pack(fill="x", padx=12, pady=(0, 12))
            ctk.CTkFrame(footer, height=1, fg_color=c['SIDEBAR_HOVER']).pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(footer, text="v1.0.0", font=ctk.CTkFont(size=9), text_color=c['SIDEBAR_TEXT']).pack(anchor="w")

    def _build_top_bar(self, c):
        for w in self.top_bar.winfo_children():
            w.destroy()

        inner = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16)

        # Page title (always shown)
        self.top_bar_title = ctk.CTkLabel(
            inner, text="Dashboard",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        )
        self.top_bar_title.pack(side="left", pady=8)

        # Nav pills (only when sidebar collapsed)
        self.top_nav_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.top_nav_pills = {}

        nav_items = [
            ("home", "Dashboard", self.show_dashboard),
            ("invoices", "Invoices", self.show_invoices),
            ("history", "History", self.show_all_history),
            ("agents", "Agents", self.show_agent_manager),
            ("taxes", "Taxes", self.show_taxes),
        ]

        for name, label, cmd in nav_items:
            is_active = (name == self._current_nav)
            pill = ctk.CTkButton(
                self.top_nav_frame, text=label,
                font=ctk.CTkFont(size=12),
                fg_color=c['PRIMARY'] if is_active else "transparent",
                text_color='#FFFFFF' if is_active else c['TEXT_SECONDARY'],
                hover_color=c['PRIMARY_LIGHT'],
                height=30, corner_radius=15,
                width=80,
                command=cmd,
            )
            pill.pack(side="left", padx=2)
            self.top_nav_pills[name] = pill

        if not self._sidebar_expanded:
            self.top_nav_frame.pack(side="right", pady=8)

    def _update_top_bar_title(self, title):
        try:
            self.top_bar_title.configure(text=title)
        except Exception:
            pass

    # ── Sidebar Animation ──

    def _toggle_sidebar(self):
        if self._sidebar_animating:
            return
        self._sidebar_animating = True

        if self._sidebar_expanded:
            self._animate_sidebar(SIDEBAR_EXPANDED, SIDEBAR_COLLAPSED, self._on_sidebar_collapsed)
        else:
            self._animate_sidebar(SIDEBAR_COLLAPSED, SIDEBAR_EXPANDED, self._on_sidebar_expanded)

    def _animate_sidebar(self, start_w, end_w, on_complete):
        step = 0
        total_steps = SIDEBAR_ANIM_STEPS
        delta = end_w - start_w

        def _step():
            nonlocal step
            step += 1
            # Ease-out: decelerate
            t = step / total_steps
            eased = 1 - (1 - t) ** 2
            w = int(start_w + delta * eased)

            self.grid_columnconfigure(0, minsize=w)
            self.sidebar.configure(width=w)
            self._current_sidebar_width = w
            self.update_idletasks()

            if step < total_steps:
                interval = SIDEBAR_ANIM_DURATION // total_steps
                self.after(interval, _step)
            else:
                on_complete()

        _step()

    def _on_sidebar_collapsed(self):
        self._sidebar_expanded = False
        self._sidebar_animating = False
        c = get_colors()
        self._build_sidebar(c)
        self.top_nav_frame.pack(side="right", pady=8)
        self.db.set_setting('sidebar_collapsed', '1')

    def _on_sidebar_expanded(self):
        self._sidebar_expanded = True
        self._sidebar_animating = False
        c = get_colors()
        self._build_sidebar(c)
        self.top_nav_frame.pack_forget()
        self.db.set_setting('sidebar_collapsed', '0')

    # ── Theme Toggle ──

    def _toggle_theme(self):
        colors = self._tm.toggle()
        mode = self._tm.mode
        ctk.set_appearance_mode(mode)
        self.db.set_setting('theme_mode', mode)

        # Rebuild shell
        self.sidebar.configure(fg_color=colors['SIDEBAR_BG'])
        self._build_sidebar(colors)
        self.right_col.configure(fg_color=colors['CONTENT_BG'])
        self.top_bar.configure(fg_color=colors['CARD_BG'])
        self.top_bar_border.configure(fg_color=colors['CARD_BORDER'])
        self.content.configure(fg_color=colors['CONTENT_BG'])
        self._build_top_bar(colors)

        # Re-show current page (frames will pick up new colors)
        nav_to_show = {
            'home': self.show_dashboard,
            'invoices': self.show_invoices,
            'history': self.show_all_history,
            'agents': self.show_agent_manager,
            'taxes': self.show_taxes,
        }
        show_fn = nav_to_show.get(self._current_nav, self.show_dashboard)
        show_fn()

    # ── Navigation Helpers ──

    def _highlight_nav(self, active):
        self._current_nav = active
        c = get_colors()
        for name, btn in self.nav_buttons.items():
            if name == active:
                btn.configure(fg_color=c['SIDEBAR_HOVER'], text_color=c['SIDEBAR_TEXT_ACTIVE'])
            else:
                btn.configure(fg_color="transparent", text_color=c['SIDEBAR_TEXT'])

        # Update top bar pills
        for name, pill in self.top_nav_pills.items():
            if name == active:
                pill.configure(fg_color=c['PRIMARY'], text_color='#FFFFFF')
            else:
                pill.configure(fg_color="transparent", text_color=c['TEXT_SECONDARY'])

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self._current_page = None

    # ===== Screen Navigation =====

    def show_dashboard(self):
        from ui.dashboard_frame import DashboardFrame
        self._clear_content()
        self._highlight_nav("home")
        self._update_top_bar_title("Dashboard")
        frame = DashboardFrame(
            self.content, self.db,
            on_go_invoices=self.show_invoices,
            on_go_taxes=self.show_taxes,
            on_go_agents=self.show_agent_manager,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_invoices(self):
        from ui.agent_select_frame import AgentSelectFrame
        self._clear_content()
        self._highlight_nav("invoices")
        self._update_top_bar_title("Invoices")
        frame = AgentSelectFrame(
            self.content, self.db,
            on_new_transaction=self._show_transaction_form,
            on_view_history=self._show_agent_history,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def _show_transaction_form(self, agent, prefill=None):
        from ui.transaction_form import TransactionForm
        self._clear_content()
        self._highlight_nav("invoices")
        self._update_top_bar_title("New Transaction")
        form = TransactionForm(
            self.content, agent,
            on_calculate=self._on_calculate,
            on_cancel=self.show_invoices,
        )
        form.pack(fill="both", expand=True)
        self._current_page = form

        if prefill:
            form.address_entry.delete(0, "end")
            form.address_entry.insert(0, prefill.get('address', ''))
            form.sale_price_entry.delete(0, "end")
            form.sale_price_entry.insert(0, str(prefill.get('sale_price', '')))
            form.comm_pct_entry.delete(0, "end")
            form.comm_pct_entry.insert(0, str(prefill.get('comm_pct', '')))
            form._update_gross()
            form.date_entry.delete(0, "end")
            form.date_entry.insert(0, prefill.get('date', ''))
            form.company_lead_var.set(prefill.get('company_lead', False))
            form.fee_entry.delete(0, "end")
            form.fee_entry.insert(0, str(prefill.get('fee', '0')))
            form.payer_var.set(prefill.get('payer', 'buyer'))
            form.payment_entry.delete(0, "end")
            form.payment_entry.insert(0, prefill.get('payment', ''))

    def _on_calculate(self, agent, property_address, gross_commission, closing_date,
                      is_company_lead, compliance_fee, compliance_fee_payer, payment_method,
                      sale_price='', comm_pct=''):
        year_start, year_end = get_cap_year(agent.contract_date, closing_date)
        cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
        txn_count = self.db.get_txn_count_in_period(agent.id, year_start, year_end)

        result = calculate_commission(
            agent=agent,
            gross_commission=gross_commission,
            is_company_lead=is_company_lead,
            compliance_fee_amount=compliance_fee,
            compliance_fee_payer=compliance_fee_payer,
            cap_paid_to_date=cap_ptd,
            txn_count_in_period=txn_count,
        )

        invoice_date = closing_date.strftime("%m/%d/%Y")

        self._pending_agent = agent
        self._pending_result = result
        self._pending_invoice_date = invoice_date
        self._pending_address = property_address
        self._pending_payment = payment_method
        self._pending_form_data = {
            'address': property_address,
            'commission': gross_commission,
            'sale_price': sale_price,
            'comm_pct': comm_pct,
            'date': invoice_date,
            'company_lead': is_company_lead,
            'fee': compliance_fee,
            'payer': compliance_fee_payer,
            'payment': payment_method,
            'closing_date': closing_date,
            'year_start': year_start,
            'year_end': year_end,
        }

        self._show_review(agent, result, "(pending)", invoice_date, property_address, payment_method)

    def _show_review(self, agent, result, invoice_number, invoice_date, property_address, payment_method):
        from ui.review_frame import ReviewFrame
        self._clear_content()
        self._update_top_bar_title("Invoice Preview")
        frame = ReviewFrame(
            self.content, agent, result,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            property_address=property_address,
            payment_method=payment_method,
            on_generate=self._generate_invoice,
            on_edit=self._edit_transaction,
            on_cancel=self.show_invoices,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def _edit_transaction(self):
        if self._pending_agent and self._pending_form_data:
            self._show_transaction_form(self._pending_agent, prefill=self._pending_form_data)

    def _generate_invoice(self):
        if not self._pending_agent or not self._pending_result:
            return

        agent = self._pending_agent
        result = self._pending_result
        fd = self._pending_form_data

        from core.constants import get_output_dir
        output_dir = get_output_dir()

        invoice_number = self.db.get_next_invoice_number()

        self.db.insert_transaction({
            'agent_id': agent.id,
            'invoice_number': invoice_number,
            'property_address': fd['address'],
            'gross_commission': fd['commission'],
            'closing_date': fd['closing_date'].isoformat(),
            'is_company_lead': 1 if fd['company_lead'] else 0,
            'compliance_fee_amount': fd['fee'],
            'compliance_fee_payer': fd['payer'],
            'office_share': result.office_share,
            'agent_share': result.agent_share,
            'amount_toward_cap': result.amount_toward_cap,
            'cap_before_txn': result.cap_before,
            'cap_after_txn': result.cap_after,
            'agent_pct_used': result.agent_split_pct_used,
            'office_pct_used': result.office_split_pct_used,
            'payment_method': fd['payment'],
            'total_payout': result.total_payout,
            'cap_year_start': fd['year_start'],
            'cap_year_end': fd['year_end'],
            'compliance_to_office': result.compliance_to_office,
            'compliance_to_agent': result.compliance_to_agent,
        })

        tax_year = fd['closing_date'].year
        self.db.upsert_tax_record(agent.id, tax_year, result.agent_share)

        try:
            internal_path, agent_path = generate_both_invoices(
                agent=agent, result=result,
                invoice_number=invoice_number,
                invoice_date=self._pending_invoice_date,
                property_address=fd['address'],
                payment_method=fd['payment'],
                output_dir=output_dir,
            )

            messagebox.showinfo(
                "Invoices Generated",
                f"Invoice {invoice_number} saved!\n\n"
                f"Internal: invoices/internal/{os.path.basename(internal_path)}\n"
                f"Agent copy: invoices/agent/{os.path.basename(agent_path)}\n\n"
                f"Location: {output_dir}"
            )
        except Exception as e:
            messagebox.showerror("PDF Error", f"Transaction saved but PDF generation failed:\n{e}")

        self._pending_agent = None
        self._pending_result = None
        self._pending_form_data = None
        self.show_invoices()

    def _show_agent_history(self, agent):
        from ui.history_frame import HistoryFrame
        self._clear_content()
        self._highlight_nav("history")
        self._update_top_bar_title(f"History — {agent.name}")
        frame = HistoryFrame(
            self.content, self.db, agent=agent,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_all_history(self):
        from ui.history_frame import HistoryFrame
        self._clear_content()
        self._highlight_nav("history")
        self._update_top_bar_title("Transaction History")
        frame = HistoryFrame(
            self.content, self.db,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_agent_manager(self):
        from ui.agent_manage_frame import AgentManageFrame
        self._clear_content()
        self._highlight_nav("agents")
        self._update_top_bar_title("Manage Agents")
        frame = AgentManageFrame(
            self.content, self.db,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_taxes(self):
        from ui.taxes_frame import TaxesFrame
        self._clear_content()
        self._highlight_nav("taxes")
        self._update_top_bar_title("1099-NEC Tax Tracking")
        frame = TaxesFrame(
            self.content, self.db,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def on_closing(self):
        self.db.close()
        self.destroy()
```

- [ ] **Step 2: Verify app.py imports without errors**

Run: `cd /Users/anthony/Desktop/Work/commission\ thingy/commission_tracker && source venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); from app import App; print('App imports OK')"`

Expected: `App imports OK`

- [ ] **Step 3: Commit app.py**

```bash
git add src/app.py
git commit -m "feat: rewrite app.py with grid layout, collapsible sidebar, top bar, and dark mode"
```

---

## Chunk 3: Update All UI Frames

Each frame needs:
1. Replace old color imports with `from ui.theme import get_colors`
2. Use `c = get_colors()` at build time for all color references
3. Use updated widget factories from theme.py
4. Compact sizing per spec (smaller fonts, pill buttons, 42px row heights)

### Task 5: Update dashboard_frame.py

**Files:**
- Modify: `src/ui/dashboard_frame.py` (205 lines)

- [ ] **Step 1: Rewrite dashboard_frame.py**

Replace the entire file with the new version that uses ThemeManager colors, compact stat cards with blue accent bars, pill action buttons, and clean transaction rows:

```python
import customtkinter as ctk
from datetime import datetime
from ui.theme import (
    get_colors, font_display, font_heading, font_body, font_caption,
    card, primary_button, section_label,
)


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_go_invoices=None, on_go_taxes=None, on_go_agents=None):
        c = get_colors()
        super().__init__(parent, fg_color=c['CONTENT_BG'])
        self.db = db
        self.on_go_invoices = on_go_invoices
        self.on_go_taxes = on_go_taxes
        self.on_go_agents = on_go_agents
        self._build()

    def _build(self):
        c = get_colors()

        scroll = ctk.CTkScrollableFrame(self, fg_color=c['CONTENT_BG'])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(
            header, text="Dashboard",
            font=font_display(24),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Overview of your commission tracking",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        # Stats cards row
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", padx=24, pady=(20, 0))
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="stat")

        agents = self.db.get_real_agents()
        agent_count = len(agents)

        current_year = datetime.now().year
        txns = self.db.get_real_transactions()
        ytd_total = sum(
            t.gross_commission for t in txns
            if t.closing_date and t.closing_date.startswith(str(current_year))
        )

        previous_year = current_year - 1
        tax_records = self.db.get_tax_records_for_year(previous_year)
        test_agent_ids = {a.id for a in self.db.get_active_agents() if a.is_test}
        pending_1099 = sum(
            1 for r in tax_records
            if r.agent_id not in test_agent_ids
            and (r.total_compensation + r.manual_adjustment) >= 600 and not r.filed
        )
        pending_label = f"{pending_1099} pending" if pending_1099 > 0 else "All filed"

        self._stat_card(stats_frame, "Active Agents", str(agent_count), c['PRIMARY'], 0, c)
        self._stat_card(stats_frame, f"Gross Commissions {current_year}", f"${ytd_total:,.2f}", c['SUCCESS'], 1, c)
        self._stat_card(stats_frame, f"1099s ({previous_year})", pending_label,
                        '#D97706' if pending_1099 > 0 else c['SUCCESS'], 2, c)

        # Quick actions
        sl = section_label(scroll, "Quick Actions")
        sl.pack(fill="x", padx=24, pady=(24, 8), anchor="w")

        actions_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_frame.pack(fill="x", padx=24, pady=(0, 16))
        actions_frame.columnconfigure((0, 1, 2), weight=1, uniform="action")

        self._action_card(actions_frame, "New Invoice",
                          "Create a commission invoice for an agent",
                          "Go to Invoices", self.on_go_invoices, 0, c)
        self._action_card(actions_frame, "Tax Documents",
                          "Generate 1099-NEC forms for filing",
                          "Go to Taxes", self.on_go_taxes, 1, c)
        self._action_card(actions_frame, "Manage Agents",
                          "Add, edit, or update agent information",
                          "Go to Agents", self.on_go_agents, 2, c)

        # Recent transactions
        sl2 = section_label(scroll, "Recent Transactions")
        sl2.pack(fill="x", padx=24, pady=(8, 8), anchor="w")

        recent_txns = txns[:5]
        if recent_txns:
            for txn in recent_txns:
                self._txn_row(scroll, txn, c)
        else:
            empty_card = ctk.CTkFrame(scroll, fg_color=c['CARD_BG'], corner_radius=10,
                                       border_width=1, border_color=c['CARD_BORDER'])
            empty_card.pack(fill="x", padx=24, pady=(0, 10))
            ctk.CTkLabel(
                empty_card, text="No transactions yet. Create your first invoice to get started.",
                font=font_body(13), text_color=c['TEXT_SECONDARY'],
            ).pack(padx=20, pady=20)

    def _stat_card(self, parent, title, value, accent_color, col, c):
        card_frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=10,
                                   border_width=1, border_color=c['CARD_BORDER'])
        card_frame.grid(row=0, column=col, sticky="nsew",
                        padx=(0 if col == 0 else 6, 0 if col == 2 else 6), pady=0)

        # Accent bar
        ctk.CTkFrame(card_frame, width=4, height=36, fg_color=accent_color,
                      corner_radius=2).place(x=12, y=14)

        ctk.CTkLabel(
            card_frame, text=title,
            font=font_caption(11), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", padx=(28, 16), pady=(14, 0))

        ctk.CTkLabel(
            card_frame, text=value,
            font=ctk.CTkFont(size=20, weight="bold"), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", padx=(28, 16), pady=(2, 14))

    def _action_card(self, parent, title, description, button_text, callback, col, c):
        card_frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=10,
                                   border_width=1, border_color=c['CARD_BORDER'])
        card_frame.grid(row=0, column=col, sticky="nsew",
                        padx=(0 if col == 0 else 6, 0 if col == 2 else 6), pady=0)

        ctk.CTkLabel(
            card_frame, text=title,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", padx=20, pady=(18, 2))

        ctk.CTkLabel(
            card_frame, text=description,
            font=font_caption(12), text_color=c['TEXT_SECONDARY'],
            wraplength=200,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        if callback:
            ctk.CTkButton(
                card_frame, text=button_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=c['PRIMARY'], hover_color=c['PRIMARY_HOVER'],
                text_color='#FFFFFF', corner_radius=17,
                height=32, width=130,
                command=callback,
            ).pack(anchor="w", padx=20, pady=(0, 18))

    def _txn_row(self, parent, txn, c):
        row = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=8,
                           border_width=1, border_color=c['CARD_BORDER'], height=46)
        row.pack(fill="x", padx=24, pady=(0, 3))
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=6)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left, text=f"{txn.invoice_number}  •  {txn.property_address}",
            font=font_body(12), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        agent_name = txn.agent_name or ""
        ctk.CTkLabel(
            left, text=f"{agent_name}  •  {txn.closing_date}",
            font=font_caption(10), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=f"${txn.gross_commission:,.2f}",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=c['TEXT_PRIMARY'],
        ).pack(side="right", anchor="e")
```

- [ ] **Step 2: Verify dashboard imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.dashboard_frame import DashboardFrame; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit dashboard**

```bash
git add src/ui/dashboard_frame.py
git commit -m "feat: redesign dashboard with blue theme and compact layout"
```

---

### Color Mapping Reference (for Tasks 6-11)

Every frame needs its import block replaced and all color constants swapped. Here is the **complete** mapping from old constants to new `get_colors()` keys:

| Old Constant | New `c[...]` Key | Notes |
|---|---|---|
| `NAVY` | `c['SIDEBAR_BG']` | Used for dark bars (agent info bar, table headers, total payout row) |
| `GOLD` | `c['PRIMARY']` | Buttons, accents, active tabs, radio buttons, checkboxes, progress bars |
| `GOLD_DARK` | `c['PRIMARY_HOVER']` | Hover states for buttons, combo boxes |
| `DARK_TEXT` | `c['TEXT_PRIMARY']` | Primary body text |
| `GRAY_TEXT` | `c['TEXT_SECONDARY']` | Secondary/label text |
| `WHITE` | `c['CARD_BG']` | Card backgrounds, input backgrounds |
| `LIGHT_BG` | `c['CONTENT_BG']` | Content area backgrounds |
| `CONTENT_BG` | `c['CONTENT_BG']` | Same |
| `CARD_BORDER` | `c['CARD_BORDER']` | Card borders, input borders → also use `c['INPUT_BORDER']` for inputs |
| `SECTION_BG` | `c['SECTION_BG']` | Section backgrounds |
| `WARM_GRAY` | `c['TEXT_SECONDARY']` | Sidebar text, table header text |
| `MUTED_TEXT` | `c['TEXT_MUTED']` | Disabled/muted text |
| `ROW_ALT` | `c['ROW_ALT']` | Alternating table rows |
| `EMERALD` | `c['SUCCESS']` | Success buttons |
| `EMERALD_HOVER` | `c['SUCCESS_HOVER']` | Success button hover |
| `CORAL` | `c['DANGER']` | Danger buttons, error text |
| `CORAL_HOVER` | `c['DANGER_HOVER']` | Danger button hover |
| `BADGE_GREEN` | `c['SUCCESS']` | Active/ready badges |
| `BADGE_RED` | `c['DANGER']` | Inactive badges |
| `BADGE_BLUE` | `'#2563EB'` | Filed status (hardcode or keep as local constant) |
| `BADGE_YELLOW` | `'#D97706'` | Warning status (hardcode or keep as local constant) |
| `BADGE_GRAY` | `'#9CA3AF'` | Below threshold (hardcode or keep as local constant) |

**Standard import replacement** for all frames:

Old:
```python
from core.constants import (
    DARK_TEXT, GRAY_TEXT, GOLD, GOLD_DARK, WHITE, LIGHT_BG,
    CARD_BORDER, SECTION_BG, WARM_GRAY, MUTED_TEXT, NAVY,
    EMERALD, EMERALD_HOVER, CORAL, CORAL_HOVER, ROW_ALT,
    BADGE_GREEN, CONTENT_BG,
)
```

New:
```python
from ui.theme import get_colors
```

Then add `c = get_colors()` at the start of `__init__`, `_build_ui`, and any method that creates widgets.

**Standard widget factory changes:**
- `primary_button` width defaults changed from 200 → 100 (callers should pass explicit width)
- `success_button` same
- Button heights: 44px → 34px (pill style)
- Button corners: 10px → 17px (full pill)
- Font sizes reduced: display 28→24, heading 18→16

---

### Task 6: Update agent_select_frame.py

**Files:**
- Modify: `src/ui/agent_select_frame.py` (290 lines)

- [ ] **Step 1: Update imports, color references, and layout**

Replace the import block (lines 1-11) per the color mapping table above. Add `c = get_colors()` in `__init__` and `_build_ui`. Apply all color replacements using the mapping table.

Additionally, change the page title from "Dashboard" (line 36) to "Invoices" — this is a bug in the current code.

Key layout changes beyond color swaps:
- Badge for split type: use `c['PRIMARY']` instead of `GOLD` (line 187)
- Progress bar: `progress_color=c['PRIMARY']` (line 276)
- ComboBox: `button_color=c['PRIMARY']`, `button_hover_color=c['PRIMARY_HOVER']` (lines 75-76)
- Font sizes reduced: `font_display(28)` → `font_display(24)`, etc.

- [ ] **Step 2: Verify imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.agent_select_frame import AgentSelectFrame; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add src/ui/agent_select_frame.py
git commit -m "feat: update agent select frame with blue theme"
```

---

### Task 7: Update transaction_form.py

**Files:**
- Modify: `src/ui/transaction_form.py` (322 lines)

- [ ] **Step 1: Update imports and color references**

Same pattern as Task 6:
- Replace old color imports with `from ui.theme import get_colors`
- Replace `NAVY` → `c['SIDEBAR_BG']` for agent_bar (line 39)
- Replace `GOLD` → `c['PRIMARY']` for checkboxes (line 174), radio buttons (line 211), gross label text color (line 130)
- Replace `GOLD_DARK` → `c['PRIMARY_HOVER']` for hover colors
- All form inputs use `c['INPUT_BORDER']` for borders
- Error label: `"#C44536"` → `c['DANGER']`
- Reduce font sizes per spec

- [ ] **Step 2: Verify imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.transaction_form import TransactionForm; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add src/ui/transaction_form.py
git commit -m "feat: update transaction form with blue theme and compact inputs"
```

---

### Task 8: Update review_frame.py

**Files:**
- Modify: `src/ui/review_frame.py` (231 lines)

- [ ] **Step 1: Update imports and color references**

Key changes:
- Total payout row: `fg_color=NAVY` → `fg_color=c['SIDEBAR_BG']`, `text_color=GOLD` → `text_color=c['PRIMARY']` (line 153-164)
- Progress bar: `progress_color=GOLD` → `progress_color=c['PRIMARY']` (line 209)
- All color imports replaced
- Font sizes reduced per spec

- [ ] **Step 2: Verify imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.review_frame import ReviewFrame; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add src/ui/review_frame.py
git commit -m "feat: update review frame with blue theme"
```

---

### Task 9: Update history_frame.py

**Files:**
- Modify: `src/ui/history_frame.py` (189 lines)

- [ ] **Step 1: Update imports and color references**

Key changes:
- Table header: `fg_color=NAVY` → `fg_color=c['SIDEBAR_BG']` (line 136)
- ComboBox: `button_color=GOLD` → `button_color=c['PRIMARY']` (line 76)
- Row alternating: `ROW_ALT` → `c['ROW_ALT']` (line 151)
- Row height: reduce to 42px per spec
- Font sizes: reduced per spec

- [ ] **Step 2: Verify imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.history_frame import HistoryFrame; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add src/ui/history_frame.py
git commit -m "feat: update history frame with blue theme and compact rows"
```

---

### Task 10: Update agent_manage_frame.py

**Files:**
- Modify: `src/ui/agent_manage_frame.py` (918 lines — largest file)

- [ ] **Step 1: Update imports and color references**

Replace the import block (lines 1-14):
```python
import json
import customtkinter as ctk
from tkinter import messagebox
from ui.theme import (
    get_colors, section_label, card, success_button, primary_button,
    secondary_button, danger_button, separator, badge,
    font_display, font_heading, font_subheading, font_body, font_caption,
)
```

Add `c = get_colors()` at the top of every method that creates widgets: `_build_ui`, `_build_edit_form`, `_switch_tab`, `_build_profile_tab`, `_build_tax_info_tab`, `_styled_entry`, `_add_new_agent`, `_delete_agent`.

- [ ] **Step 2: Convert tab buttons to underline-style tabs**

The spec calls for underline-style tabs instead of filled buttons. Replace the current filled-button tab bar (lines 139-162) with underline tabs:

```python
        # ── Tab Bar ──
        tab_bar = ctk.CTkFrame(form, fg_color="transparent")
        tab_bar.pack(fill="x", pady=(0, 0))

        self._current_tab = "profile"
        self.tab_buttons = {}
        self.tab_underlines = {}

        for tab_name, tab_label in [("profile", "Profile"), ("tax_info", "Tax Info")]:
            tab_wrapper = ctk.CTkFrame(tab_bar, fg_color="transparent")
            tab_wrapper.pack(side="left", padx=(0, 4))

            is_active = (tab_name == "profile")
            btn = ctk.CTkButton(
                tab_wrapper, text=tab_label, width=100, height=32,
                font=font_subheading(13),
                fg_color="transparent",
                text_color=c['PRIMARY'] if is_active else c['TEXT_SECONDARY'],
                hover_color=c['SECTION_BG'],
                corner_radius=0,
                command=lambda t=tab_name: self._switch_tab(t),
            )
            btn.pack()

            # Underline indicator
            underline = ctk.CTkFrame(
                tab_wrapper, height=2,
                fg_color=c['PRIMARY'] if is_active else "transparent",
            )
            underline.pack(fill="x")

            self.tab_buttons[tab_name] = btn
            self.tab_underlines[tab_name] = underline

        # Divider line below tabs
        ctk.CTkFrame(form, height=1, fg_color=c['CARD_BORDER']).pack(fill="x", pady=(0, 12))

        self.tab_content_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.tab_content_frame.pack(fill="both", expand=True)

        self._build_profile_tab()
```

And update `_switch_tab` (lines 164-178):

```python
    def _switch_tab(self, tab_name):
        c = get_colors()
        self._current_tab = tab_name
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.configure(text_color=c['PRIMARY'])
                self.tab_underlines[name].configure(fg_color=c['PRIMARY'])
            else:
                btn.configure(text_color=c['TEXT_SECONDARY'])
                self.tab_underlines[name].configure(fg_color="transparent")

        for w in self.tab_content_frame.winfo_children():
            w.destroy()

        if tab_name == "profile":
            self._build_profile_tab()
        elif tab_name == "tax_info":
            self._build_tax_info_tab()
```

- [ ] **Step 3: Apply remaining color swaps throughout the file**

Systematic replacements (use color mapping table):
- All radio buttons: `fg_color=GOLD` → `fg_color=c['PRIMARY']`, `hover_color=GOLD_DARK` → `hover_color=c['PRIMARY_HOVER']`
- ComboBox: `button_color=GOLD` → `button_color=c['PRIMARY']`, `button_hover_color=GOLD_DARK` → `button_hover_color=c['PRIMARY_HOVER']`
- Error labels: `CORAL` → `c['DANGER']`
- `DARK_TEXT` → `c['TEXT_PRIMARY']`, `GRAY_TEXT` → `c['TEXT_SECONDARY']`, `MUTED_TEXT` → `c['TEXT_MUTED']`
- `WHITE` → `c['CARD_BG']`, `CARD_BORDER` → `c['CARD_BORDER']`, `SECTION_BG` → `c['SECTION_BG']`
- `NAVY` → `c['SIDEBAR_BG']`, `CONTENT_BG` → `c['CONTENT_BG']`
- `EMERALD` → `c['SUCCESS']`, `EMERALD_HOVER` → `c['SUCCESS_HOVER']`
- `CORAL_HOVER` → `c['DANGER_HOVER']`
- `BADGE_GREEN` → `c['SUCCESS']`
- `ROW_ALT` → `c['ROW_ALT']`
- Font size reductions: `font_display(28)` → `font_display(24)`, etc.

- [ ] **Step 4: Verify imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.agent_manage_frame import AgentManageFrame; print('OK')"`

- [ ] **Step 5: Commit**

```bash
git add src/ui/agent_manage_frame.py
git commit -m "feat: update agent management frame with blue theme and underline tabs"
```

---

### Task 11: Update taxes_frame.py

**Files:**
- Modify: `src/ui/taxes_frame.py` (438 lines)

- [ ] **Step 1: Update imports and color references**

Key changes:
- Table header: `fg_color=NAVY` → `fg_color=c['SIDEBAR_BG']` (line 147)
- Generate button in rows: `fg_color=GOLD` → `fg_color=c['PRIMARY']`, `text_color=NAVY` → `text_color='#FFFFFF'` (lines 217-219)
- ComboBox: `button_color=GOLD` → `button_color=c['PRIMARY']` (line 82)
- Badge colors: Keep `BADGE_BLUE`, `BADGE_YELLOW`, `BADGE_GRAY`, `BADGE_GREEN` but define them in the file or import from theme
- Adjustment window: `CONTENT_BG` → `c['CONTENT_BG']` (line 295)

For badge status colors, add these to the file or get them from `get_colors()`. Simplest: define them locally:
```python
BADGE_BLUE = '#2563EB'
BADGE_YELLOW = '#D97706'
BADGE_GRAY = '#9CA3AF'
BADGE_GREEN = '#16A34A'
```

- [ ] **Step 2: Verify imports**

Run: `python -c "import sys; sys.path.insert(0, 'src'); from ui.taxes_frame import TaxesFrame; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add src/ui/taxes_frame.py
git commit -m "feat: update taxes frame with blue theme and compact badges"
```

---

## Chunk 4: Integration Testing & Polish

### Task 12: Full Smoke Test

- [ ] **Step 1: Run the app and verify it launches**

Run: `cd /Users/anthony/Desktop/Work/commission\ thingy/commission_tracker && source venv/bin/activate && python main.py`

Expected: App launches with blue/white color scheme, collapsible sidebar with icons, top bar.

Verify each page loads:
- Dashboard: blue accent stat cards, pill action buttons
- Invoices: blue ComboBox, blue-bordered selected state
- History: navy header row, alternating rows
- Manage Agents: blue tab buttons, blue radio buttons
- Taxes: blue generate buttons, proper badge colors

- [ ] **Step 2: Test sidebar collapse/expand**

Click the chevron button. Verify:
- Smooth 250ms animation
- Labels hide, icons remain
- Top bar shows nav pills when collapsed
- State persists after restarting app

- [ ] **Step 3: Test dark mode toggle**

Click the moon icon. Verify:
- All colors switch to dark palette
- Sidebar goes deep dark
- Cards become dark elevated surfaces
- Text is light on dark backgrounds
- State persists after restarting app

- [ ] **Step 4: Test page navigation**

Navigate between all pages. Verify:
- Sidebar active state highlights correctly
- Top bar title updates
- Top bar pills sync with sidebar when collapsed
- No orphan widgets or ghost frames

- [ ] **Step 5: End-to-end transaction test**

Complete a full invoice flow:
1. Dashboard → Go to Invoices
2. Select an agent
3. Fill in transaction form
4. Review page shows correct colors
5. Generate invoice (verify PDF still generates correctly)

- [ ] **Step 6: Fix any issues found during testing**

Address any visual glitches, color mismatches, or layout problems discovered during the smoke test.

- [ ] **Step 7: Commit any fixes**

```bash
git add -A
git commit -m "fix: address UI issues found during smoke testing"
```

---

### Task 13: Update PyInstaller Spec (if needed)

**Files:**
- Modify: `GotKeyd Commission Tracker.spec` (if icon assets need to be included)

- [ ] **Step 1: Check if spec includes assets/icons/**

The PyInstaller spec file should already include `assets/` via data collection. If icons aren't showing in the built app, add `('assets/icons', 'assets/icons')` to the `datas` list.

- [ ] **Step 2: Test build**

Run: `cd /Users/anthony/Desktop/Work/commission\ thingy/commission_tracker && pyinstaller "GotKeyd Commission Tracker.spec"`

Expected: Build succeeds, app launches from `dist/` with all icons visible.

- [ ] **Step 3: Commit spec changes if any**

```bash
git add "GotKeyd Commission Tracker.spec"
git commit -m "build: include icon assets in PyInstaller bundle"
```
