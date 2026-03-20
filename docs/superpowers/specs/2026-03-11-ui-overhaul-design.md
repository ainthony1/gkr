# UI Overhaul Design Spec

**Date**: 2026-03-11
**Status**: Draft
**Scope**: Full visual rework of the Got Key'd Realty commission tracker desktop app

## Overview

Complete UI modernization: replace the warm gold/charcoal palette with blue/white brand colors, add dark mode, implement a collapsible animated sidebar, redesign all components (buttons, cards, forms, tables) to feel compact and modern, and add smooth transitions throughout. The app should feel lightweight, clean, and professional — not clunky or barebones.

## 1. Color System

### Design Tokens

All colors are accessed via a `get_colors()` function that returns the active theme's palette. No component references color constants directly.

#### Light Mode

| Token | Hex | Description |
|-------|-----|-------------|
| `PRIMARY` | `#2563EB` | Primary blue — buttons, active nav, accents |
| `PRIMARY_HOVER` | `#1D4ED8` | Darker blue for hover states |
| `PRIMARY_LIGHT` | `#EFF6FF` | Ice blue — active row highlights, subtle backgrounds |
| `SIDEBAR_BG` | `#1E3A5F` | Deep navy — sidebar background |
| `SIDEBAR_HOVER` | `#264A73` | Lighter navy — sidebar hover/active state |
| `SIDEBAR_TEXT` | `#CBD5E1` | Slate-300 — sidebar default text |
| `SIDEBAR_TEXT_ACTIVE` | `#FFFFFF` | White — active sidebar item text |
| `CONTENT_BG` | `#F8FAFC` | Cool off-white — main content area |
| `CARD_BG` | `#FFFFFF` | White — card backgrounds |
| `CARD_BORDER` | `#E2E8F0` | Slate-200 — card borders |
| `TEXT_PRIMARY` | `#1E293B` | Slate-900 — primary body text |
| `TEXT_SECONDARY` | `#64748B` | Slate-500 — secondary/label text |
| `TEXT_MUTED` | `#94A3B8` | Slate-400 — disabled/muted text |
| `SUCCESS` | `#16A34A` | Green-600 — success states |
| `SUCCESS_HOVER` | `#15803D` | Green-700 — success hover |
| `DANGER` | `#DC2626` | Red-600 — danger/delete actions |
| `DANGER_HOVER` | `#B91C1C` | Red-700 — danger hover |
| `ROW_ALT` | `#F1F5F9` | Slate-100 — alternating table rows |
| `SECTION_BG` | `#F1F5F9` | Slate-100 — section backgrounds |
| `INPUT_BORDER` | `#CBD5E1` | Slate-300 — input borders |
| `INPUT_FOCUS` | `#2563EB` | Blue — input focus ring |

#### Dark Mode

| Token | Hex | Description |
|-------|-----|-------------|
| `PRIMARY` | `#3B82F6` | Blue-500 — slightly brighter for dark bg visibility |
| `PRIMARY_HOVER` | `#2563EB` | Blue-600 |
| `PRIMARY_LIGHT` | `#1E3A5F` | Navy tint for highlights on dark |
| `SIDEBAR_BG` | `#0F172A` | Slate-950 — deep dark sidebar |
| `SIDEBAR_HOVER` | `#1E293B` | Slate-800 |
| `SIDEBAR_TEXT` | `#94A3B8` | Slate-400 |
| `SIDEBAR_TEXT_ACTIVE` | `#FFFFFF` | White |
| `CONTENT_BG` | `#1A1F2E` | Dark charcoal — content area |
| `CARD_BG` | `#242937` | Elevated dark — card surfaces |
| `CARD_BORDER` | `#334155` | Slate-700 |
| `TEXT_PRIMARY` | `#F1F5F9` | Slate-100 — light text on dark |
| `TEXT_SECONDARY` | `#94A3B8` | Slate-400 |
| `TEXT_MUTED` | `#64748B` | Slate-500 |
| `SUCCESS` | `#22C55E` | Green-500 — brighter on dark |
| `SUCCESS_HOVER` | `#16A34A` | Green-600 |
| `DANGER` | `#EF4444` | Red-500 — brighter on dark |
| `DANGER_HOVER` | `#DC2626` | Red-600 |
| `ROW_ALT` | `#1E2433` | Subtle alternating row |
| `SECTION_BG` | `#1E2433` | Section background |
| `INPUT_BORDER` | `#475569` | Slate-600 |
| `INPUT_FOCUS` | `#3B82F6` | Blue-500 |

### Theme Implementation

- New `ThemeManager` class in `src/ui/theme.py` holds current mode (`"light"` or `"dark"`) and provides `get_colors() -> dict`
- `src/core/constants.py` retains only non-UI constants (company info, paths, `get_resource_path()`, `get_output_dir()`, `get_data_dir()`). PDF RGB tuples (`NAVY_RGB`, `BLUE_RGB`, etc.) are preserved as-is for `pdf_generator.py`. All UI color constants are removed from `constants.py`.
- Preference stored in `app_settings` table (key: `theme_mode`, values: `"light"` / `"dark"`)
- All `theme.py` helper functions (`create_card`, `create_button`, etc.) call `get_colors()` internally

#### Theme Propagation

Each UI frame implements an `apply_theme(colors: dict)` method that re-configures all its widgets with the new color values. `ThemeManager` maintains a list of registered frames/callbacks. When `ThemeManager.toggle()` is called:
1. Mode flips (`"light"` <-> `"dark"`)
2. New colors dict is computed via `get_colors()`
3. `apply_theme(colors)` is called on every registered frame
4. Sidebar and top bar update themselves
5. Preference is saved to `app_settings`

Frames register themselves in their constructor: `ThemeManager.register(self)`. Frames deregister on destroy to avoid stale references.

## 2. Collapsible Sidebar

### States

| Property | Expanded | Collapsed |
|----------|----------|-----------|
| Width | 220px | 60px |
| Brand | Full logo + "GOT KEY'D REALTY" | Logo mark only |
| Nav items | Icon + label text | Icon only |
| Nav tooltip | None | Show label on hover |
| Dark mode toggle | Icon + "Dark Mode" text | Icon only |
| Collapse button | Chevron-left at bottom | Chevron-right at bottom |

### Icons

Use Unicode/emoji or simple drawn indicators for nav items (CustomTkinter doesn't support icon fonts natively). Each nav item gets a small icon drawn as a CTkLabel with a fixed-width font character or a small CTkImage from bundled PNG assets.

Suggested icon mapping:
- Dashboard: grid/home icon
- Invoices: document icon
- History: clock icon
- Manage Agents: people icon
- Taxes: calculator icon
- Dark mode: sun/moon icon
- Collapse: chevron icon

Icon assets: 20x20 PNG files in `assets/icons/`, loaded via `get_resource_path()`. Each icon has a light and dark variant (white for sidebar, slate for potential light sidebar usage).

### Animation

- Duration: 250ms
- Steps: ~15 frames (16ms per step via `after()`)
- Easing: ease-out (larger steps at start, smaller at end)
- During animation: sidebar width updates incrementally, content area expands/contracts to fill
- Labels hide when width shrinks below 150px threshold; icons remain visible throughout
- Collapse state saved to `app_settings` (key: `sidebar_collapsed`, values: `"0"` / `"1"`)

#### Layout Manager

The sidebar and content area must use `grid()` layout (not `pack()`) to enable smooth width animation. The sidebar column width is configured via `grid_columnconfigure(0, minsize=X)` and updated each animation frame with `self.update_idletasks()` to force geometry recalculation. `pack_propagate(False)` is set on the sidebar frame so `configure(width=X)` takes effect.

### Top Bar

- Always present as a horizontal strip at the top of the content area
- When sidebar **expanded**: Shows page title only (left-aligned)
- When sidebar **collapsed**: Shows page title (left) + horizontal nav buttons (center/right). Collapsed sidebar still shows icons — top bar nav buttons are the *only* text-labeled navigation when collapsed. Clicking a top bar nav button also updates the sidebar icon's active state (synced).
- Nav buttons in top bar: compact pill style, icon + short label, blue active state
- Top bar height: 48px
- Background: `CARD_BG` with a subtle bottom border (`CARD_BORDER`)

## 3. Button System

### Variants

#### Primary Button
- Height: 34px
- Corner radius: 17px (full pill)
- Font: 13px, semi-bold
- Background: `PRIMARY`
- Text: white
- Hover: `PRIMARY_HOVER`
- Shadow: subtle (simulated with border or frame layering in CTk)
- Min-width: 100px, padding 16px horizontal

#### Secondary Button
- Height: 32px
- Corner radius: 16px (full pill)
- Background: transparent
- Border: 1px `PRIMARY`
- Text: `PRIMARY`
- Hover: `PRIMARY_LIGHT` background

#### Danger Button
- Same dimensions as primary
- Background: `DANGER`
- Hover: `DANGER_HOVER`

#### Ghost Button
- No border, no background
- Text: `TEXT_SECONDARY`
- Hover: `SECTION_BG` background + `TEXT_PRIMARY` text
- Used for less prominent actions

#### Icon Button
- 32x32px square with corner radius 8px
- Transparent background
- Icon centered
- Hover: `SECTION_BG` background

### Click Feedback

On click, buttons briefly darken (~50ms) to give tactile press feedback. Implemented via `after()` scheduling a color change and reverting.

## 4. Card System

### Standard Card
- Background: `CARD_BG`
- Corner radius: 10px
- Border: 1px `CARD_BORDER`
- Shadow: simulated with a slightly darker frame behind (2px offset) or border gradient effect
- Padding: 20px internal

### Stat Card (Dashboard)
- Same as standard card
- Large number: 28px bold `TEXT_PRIMARY`
- Label: 12px `TEXT_SECONDARY`
- Optional accent bar on left (4px, `PRIMARY`) or top

### Clickable Card
- Same as standard card
- Hover: border shifts to `PRIMARY` (or lighter tint), subtle bg tint
- Cursor: hand pointer

## 5. Form Inputs

- Height: 36px
- Corner radius: 8px
- Border: 1px `INPUT_BORDER`
- Focus: border changes to `INPUT_FOCUS` (blue), subtle glow effect if possible
- Background: `CARD_BG`
- Font: 13px regular
- Label: 12px medium `TEXT_SECONDARY`, positioned above input with 4px gap
- Dropdowns: same styling, with blue focus ring
- Consistent 12px gap between form fields

## 6. Tables & Lists

### Table Rows
- Row height: 42px
- Alternating background: `CARD_BG` / `ROW_ALT`
- Hover: `PRIMARY_LIGHT` background tint
- No heavy borders between rows — color alternation provides separation
- Header row: `TEXT_SECONDARY` 11px uppercase bold, bottom border 1px `CARD_BORDER`

### Agent Select List
- Cards instead of flat list items
- Each agent: name (bold), license number (secondary), split info (muted)
- Hover highlight
- Selected state: blue left border + `PRIMARY_LIGHT` background

## 7. Page Transitions

### Frame Swap Animation — Slide Transition

CustomTkinter does not support per-widget alpha/opacity. Page transitions use a **slide animation** instead:

1. New frame is created off-screen to the right (x = content_width)
2. New frame slides in from the right over ~200ms (x animates from content_width to 0)
3. Old frame slides out to the left simultaneously (x animates from 0 to -content_width)
4. Old frame is destroyed after animation completes

Implementation: Use `place()` geometry manager for both frames during transition. Animate `x` coordinate via `after()` calls with ease-out timing. Content area must use `place()` (not `pack()`) to support coordinate-based animation.

### Micro-animations
- **Sidebar hover**: Background color transitions smoothly (step color values over 100ms)
- **Button hover**: Background color transition (~100ms)
- **Card hover**: Border color transition
- **Loading states**: Button text changes to "Generating..." with an animated ellipsis (cycle through ".", "..", "..." via `after()`)

## 8. Layout Structure

### App Window
```
+-----+----------------------------------------------+
|     |  Top Bar (48px) - title + nav when collapsed  |
|  S  +----------------------------------------------+
|  I  |                                              |
|  D  |         Content Area (scrollable)            |
|  E  |                                              |
|  B  |                                              |
|  A  |                                              |
|  R  |                                              |
|     |                                              |
+-----+----------------------------------------------+
```

### Content Padding
- Page padding: 24px horizontal, 20px top
- Section gaps: 16px between major sections
- Card internal padding: 20px

### Dashboard Layout
- 3 stat cards in a row (equal width, flex)
- Quick action cards below (3-column grid)
- Recent transactions table at bottom

### Responsive Behavior
- Minimum window size: 950x650 (unchanged)
- Sidebar collapse gives more content space on smaller windows
- Card grids reflow if content area is narrow (2-column fallback)

## 9. Typography

| Level | Size | Weight | Color |
|-------|------|--------|-------|
| Page title | 24px | Bold | `TEXT_PRIMARY` |
| Section heading | 16px | Semi-bold | `TEXT_PRIMARY` |
| Card title | 14px | Semi-bold | `TEXT_PRIMARY` |
| Body | 13px | Regular | `TEXT_PRIMARY` |
| Label | 12px | Medium | `TEXT_SECONDARY` |
| Caption | 11px | Regular | `TEXT_MUTED` |
| Mono/financial | 14px | Bold | `TEXT_PRIMARY` |

Reduced from current sizes (28px title down to 24px, etc.) for a tighter, less clunky feel.

## 10. Specific Frame Updates

### Dashboard (`src/ui/dashboard_frame.py`)
- Stat cards: compact with blue accent bars, smaller numbers
- Quick action cards: icon + label, pill-shaped action button. Existing navigation callbacks (`on_go_invoices`, `on_go_taxes`, `on_go_agents`) are preserved for these cards.
- Recent transactions: clean table with hover rows

### Agent Select (`src/ui/agent_select_frame.py`)
- Card-based list instead of flat rows
- Search input at top with blue focus ring
- Selected agent: blue left border highlight

### Transaction Form (`src/ui/transaction_form.py`)
- Compact form layout with proper label-above-input pattern
- Form sections with subtle dividers
- Pill buttons for actions
- Step indicator if multi-step flow

### Review Frame (`src/ui/review_frame.py`)
- Clean summary card layout
- Financial figures in mono font with proper alignment
- Action buttons at bottom: compact pills

### History (`src/ui/history_frame.py`)
- Clean table with alternating rows
- Hover highlight
- Compact row height (42px)
- Pill badge for transaction status/type

### Agent Management (`src/ui/agent_manage_frame.py`)
- Tab buttons: underline-style tabs instead of filled buttons
- Form fields: compact with proper spacing
- Agent list: card-based

### Taxes (`src/ui/taxes_frame.py`)
- Summary bar: stat cards style
- Agent table: clean alternating rows
- Status badges: small pills (generated/pending)
- Action buttons: compact pills

## 11. Files Changed

| File | Changes |
|------|---------|
| `src/core/constants.py` | Remove old UI color constants; preserve PDF RGB tuples, company info, and path utilities |
| `src/ui/theme.py` | Complete rewrite — `ThemeManager` class, updated helper functions for all component styles |
| `src/app.py` | New sidebar implementation with collapse animation, top bar, page transition system |
| `src/ui/dashboard_frame.py` | Redesigned stat cards, action cards, transactions table |
| `src/ui/agent_select_frame.py` | Card-based agent list, search styling |
| `src/ui/transaction_form.py` | Compact form layout, new input styling |
| `src/ui/review_frame.py` | Clean summary cards, updated buttons |
| `src/ui/history_frame.py` | Modern table with hover states |
| `src/ui/agent_manage_frame.py` | Underline tabs, compact forms |
| `src/ui/taxes_frame.py` | Updated summary bar, table, badges |
| `src/core/database.py` | New `app_settings` keys: `theme_mode`, `sidebar_collapsed` |
| `assets/icons/` | New icon PNGs for sidebar nav items |

## 12. Out of Scope

- No new functional features (commission logic, PDF generation, etc. unchanged)
- No responsive/mobile layout (desktop app, fixed min size)
- No drag-and-drop or complex gesture interactions
- No custom window chrome (title bar stays native)
