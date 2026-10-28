"""
StarLink: Constellation Weaver
Theme Definition & Antique Star Atlas Visual System

Palette Rules:
- Background: deep ink navy #0E1420
- Primary line/ink: warm parchment #E8DFC8
- Accent (used sparingly): brass/gold #C9A24A
- Danger/limited: muted vermilion #B5483A
- Muted secondary text: #8A8F9C
- NO cyan, NO purple, NO gradients, NO glow, NO pure white, NO pure black.
"""

import os
import random
import pygame

# ==============================================================================
# 1. STRICT PALETTE CONSTANTS
# ==============================================================================
COLOR_BG = (14, 20, 32)           # #0E1420 Deep ink navy
COLOR_PRIMARY = (232, 223, 200)   # #E8DFC8 Warm parchment line/ink
COLOR_ACCENT = (201, 162, 74)     # #C9A24A Brass/gold accent
COLOR_DANGER = (181, 72, 58)      # #B5483A Muted vermilion
COLOR_MUTED = (138, 143, 156)     # #8A8F9C Muted secondary text

# Alpha/translucent derivatives of the 5 canonical colors only
COLOR_GRID_LINE = (201, 162, 74, 7)       # Near invisible brass graticule grid
COLOR_GRID_CROSS = (201, 162, 74, 10)     # Near invisible grid intersections
COLOR_TICK_MAJOR = (201, 162, 74, 200)    # Neatline border tick (major)
COLOR_TICK_MINOR = (201, 162, 74, 100)    # Neatline border tick (minor)
COLOR_DIVIDER = (138, 143, 156, 60)       # Thin horizontal/vertical rule
COLOR_CANDIDATE_EDGE = (138, 143, 156, 95)# Muted dashed ink line for unchosen corridors
COLOR_LABEL_OUTLINE = COLOR_BG
COLOR_STAR_RING = COLOR_PRIMARY
COLOR_STAR_SPIKE = COLOR_PRIMARY
COLOR_EDGE_HOVER = COLOR_PRIMARY
COLOR_VIGNETTE = (14, 20, 32, 90)
COLOR_BG_STAR = (138, 143, 156, 35)
COLOR_SUBTITLE = (190, 183, 163)
COLOR_MISSION = (190, 183, 163)
COLOR_ENERGY_SPENT = (45, 52, 65)
COLOR_LEDGER_DIM = (100, 108, 122)
COLOR_LEDGER_STRIKE = (115, 122, 136)
COLOR_LEDGER_CHOSEN = (115, 122, 136)
COLOR_PROGRESS_IDLE = (80, 83, 91)
COLOR_HOVER_RING = COLOR_ACCENT
COLOR_BUTTON_HOVER = (235, 195, 105)
COLOR_GHOST = (82, 88, 101)

# ==============================================================================
# 2. RESOLUTION & GEOMETRY CONSTANTS (Base 1024x736, resolution-independent)
# ==============================================================================
BASE_WIDTH = 1024
BASE_HEIGHT = 736

# Main chart neatline frame (board)
BOARD_RECT = pygame.Rect(51, 112, 691, 486)
BOARD_INNER_RECT = pygame.Rect(58, 119, 677, 472)

# Right ledger column
LEDGER_RECT = pygame.Rect(764, 112, 216, 486)

# Title cartouche (top-left)
CARTOUCHE_X = 52
CARTOUCHE_Y = 40

# Energy meter (top-right)
ENERGY_X = 764
ENERGY_Y = 44

# Bottom navigation & mission caption
BOTTOM_BAR_Y = 642
BOTTOM_CAPTION_Y = 684

# ==============================================================================
# 3. TYPOGRAPHY & FONT MANAGER
# ==============================================================================
FONT_SERIF_REGULAR = os.path.join("assets", "fonts", "CormorantGaramond-Regular.ttf")
FONT_SERIF_ITALIC = os.path.join("assets", "fonts", "CormorantGaramond-Italic.ttf")
FONT_MONO = os.path.join("assets", "fonts", "JetBrainsMono-Regular.ttf")

_FONT_CACHE = {}

def get_font(font_path, size, fallback_name="georgia", bold=False, italic=False):
    """Retrieves a cached Pygame Font object, gracefully falling back to system fonts."""
    key = (font_path, size, bold, italic)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    font_obj = None
    if os.path.exists(font_path):
        try:
            font_obj = pygame.font.Font(font_path, size)
        except Exception:
            font_obj = None

    if font_obj is None:
        font_obj = pygame.font.SysFont(fallback_name, size, bold=bold, italic=italic)

    _FONT_CACHE[key] = font_obj
    return font_obj

# Semantic font accessors
def font_title():
    return get_font(FONT_SERIF_ITALIC, 38, fallback_name="georgia", italic=True)

def font_subtitle():
    return get_font(FONT_SERIF_REGULAR, 18, fallback_name="georgia")

def font_star_name():
    return get_font(FONT_SERIF_REGULAR, 20, fallback_name="georgia")

def font_edge_weight():
    return get_font(FONT_SERIF_REGULAR, 19, fallback_name="georgia")

def font_ledger_title():
    return get_font(FONT_SERIF_ITALIC, 23, fallback_name="georgia", italic=True)

def font_ledger_item():
    return get_font(FONT_SERIF_REGULAR, 16, fallback_name="georgia")

def font_mono(size=14):
    return get_font(FONT_MONO, size, fallback_name="consolas")

def font_button():
    return get_font(FONT_SERIF_REGULAR, 18, fallback_name="georgia")

def font_button_active():
    return get_font(FONT_SERIF_REGULAR, 18, fallback_name="georgia", bold=True)

def font_caption():
    return get_font(FONT_SERIF_ITALIC, 16, fallback_name="georgia", italic=True)

# ==============================================================================
# 4. STAR COORDINATE MAPPER (Resolution & Padding Preservation)
# ==============================================================================
def map_star_coordinates(star_x, star_y, all_stars, target_rect=BOARD_INNER_RECT, padding=44):
    """
    Deterministically maps raw level authoring coordinates into the neatline board rect,
    guaranteeing that star points and labels never touch or exceed the border.
    """
    if not all_stars:
        return int(star_x), int(star_y)

    xs = [s.x for s in all_stars]
    ys = [s.y for s in all_stars]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max(1.0, float(max_x - min_x))
    span_y = max(1.0, float(max_y - min_y))

    usable_w = float(target_rect.width - padding * 2)
    usable_h = float(target_rect.height - padding * 2)

    norm_x = (star_x - min_x) / span_x
    norm_y = (star_y - min_y) / span_y

    screen_x = target_rect.x + padding + norm_x * usable_w
    screen_y = target_rect.y + padding + norm_y * usable_h
    return int(round(screen_x)), int(round(screen_y))

# ==============================================================================
# 5. PRE-RENDERED ANTIQUE OBSERVATORY BACKDROP & NEATLINE FRAME
# ==============================================================================
def create_antique_backdrop(width=BASE_WIDTH, height=BASE_HEIGHT):
    """
    Pre-renders the static antique star atlas surface once:
    - #0E1420 ink navy background
    - Subtle paper-grain texture
    - Sparse 1px celestial background dots in 3 subtle brightness levels
    - Faint margin constellation asterisms
    - Double brass neatline frame with coordinate border ticks
    - Interior chart graticule grid lines with intersection crosshairs
    - Elegant divider rules for the ledger and navigation
    """
    backdrop = pygame.Surface((width, height)).convert()
    backdrop.fill(COLOR_BG)

    rng = random.Random(88)

    # A. Subtle Paper Grain / Noise Texture
    grain_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(18000):
        gx = rng.randint(0, width - 1)
        gy = rng.randint(0, height - 1)
        val = rng.choice([170, 210, 45, 10])
        alpha = rng.randint(3, 11)
        grain_surf.set_at((gx, gy), (val, val, val, alpha))
    backdrop.blit(grain_surf, (0, 0))

    # B. Sparse Background Stars (Tiny 1px dots in 3 subtle brightness levels)
    dots_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(110):
        dx = rng.randint(12, width - 12)
        dy = rng.randint(12, height - 12)
        # Never place directly under the main title or ledger headers
        if (dx < 280 and dy < 95) or (dx > 740 and dy < 150):
            continue
        level = rng.choice([
            COLOR_BG_STAR
        ])
        dots_surf.set_at((dx, dy), level)

    # C. Faint Historical Constellation Lines in the Margins
    margin_asterism = [
        ((880, 25), (920, 20)),
        ((920, 20), (955, 32)),
        ((955, 32), (990, 24)),
        ((990, 24), (1010, 40)),
        # Bottom left margin asterism
        ((15, 680), (35, 660)),
        ((35, 660), (42, 630)),
    ]
    for p1, p2 in margin_asterism:
        pygame.draw.line(dots_surf, (COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2], 25), p1, p2, 1)

    backdrop.blit(dots_surf, (0, 0))

    # D. Antique Neatline Frame (Outer & Inner Brass Lines)
    outer_rect = BOARD_RECT
    inner_rect = BOARD_INNER_RECT
    pygame.draw.rect(backdrop, COLOR_ACCENT, outer_rect, 1)
    pygame.draw.rect(backdrop, COLOR_ACCENT, inner_rect, 1)

    # E. Chart-Style Border Ticks (Graticule ticks in the 7px neatline band)
    tick_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    step = 28

    # Horizontal neatline borders (top and bottom)
    for x in range(outer_rect.left, outer_rect.right + 1, step // 2):
        is_major = ((x - outer_rect.left) % step == 0)
        col = COLOR_TICK_MAJOR if is_major else COLOR_TICK_MINOR
        y_top = inner_rect.top if is_major else outer_rect.top + 4
        y_bot = inner_rect.bottom if is_major else outer_rect.bottom - 4
        pygame.draw.line(tick_surf, col, (x, outer_rect.top), (x, y_top), 1)
        pygame.draw.line(tick_surf, col, (x, outer_rect.bottom), (x, y_bot), 1)

    # Vertical neatline borders (left and right)
    for y in range(outer_rect.top, outer_rect.bottom + 1, step // 2):
        is_major = ((y - outer_rect.top) % step == 0)
        col = COLOR_TICK_MAJOR if is_major else COLOR_TICK_MINOR
        x_left = inner_rect.left if is_major else outer_rect.left + 4
        x_right = inner_rect.right if is_major else outer_rect.right - 4
        pygame.draw.line(tick_surf, col, (outer_rect.left, y), (x_left, y), 1)
        pygame.draw.line(tick_surf, col, (outer_rect.right, y), (x_right, y), 1)

    backdrop.blit(tick_surf, (0, 0))

    # F. Interior Celestial Graticule Grid Lines & Coordinate Crosshairs
    grid_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for gx in range(outer_rect.left + step * 2, outer_rect.right - step, step * 2):
        pygame.draw.line(grid_surf, COLOR_GRID_LINE, (gx, inner_rect.top), (gx, inner_rect.bottom), 1)
    for gy in range(outer_rect.top + step * 2, outer_rect.bottom - step, step * 2):
        pygame.draw.line(grid_surf, COLOR_GRID_LINE, (inner_rect.left, gy), (inner_rect.right, gy), 1)

    # Subtle crosshairs at grid intersections
    for gx in range(outer_rect.left + step * 2, outer_rect.right - step, step * 2):
        for gy in range(outer_rect.top + step * 2, outer_rect.bottom - step, step * 2):
            pygame.draw.line(grid_surf, COLOR_GRID_CROSS, (gx - 2, gy), (gx + 2, gy), 1)
            pygame.draw.line(grid_surf, COLOR_GRID_CROSS, (gx, gy - 2), (gx, gy + 2), 1)

    backdrop.blit(grid_surf, (0, 0))

    # Faint corner vignette, kept inside the atlas board.
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for inset, alpha in ((0, 28), (18, 18), (36, 10)):
        edge = outer_rect.inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(vignette, (*COLOR_VIGNETTE[:3], alpha), edge, 16)
    backdrop.blit(vignette, (0, 0))

    # G. Structural Dividers (Ledger & Bottom Bar Rules)
    rule_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    # Ledger top rule under title
    pygame.draw.line(rule_surf, COLOR_DIVIDER, (LEDGER_RECT.left, LEDGER_RECT.top + 32), (LEDGER_RECT.right + 20, LEDGER_RECT.top + 32), 1)
    # Ledger bottom rule above link tally
    pygame.draw.line(rule_surf, COLOR_DIVIDER, (LEDGER_RECT.left, LEDGER_RECT.bottom - 42), (LEDGER_RECT.right + 20, LEDGER_RECT.bottom - 42), 1)
    # Bottom navigation top rule
    pygame.draw.line(rule_surf, COLOR_DIVIDER, (outer_rect.left, BOTTOM_BAR_Y - 14), (LEDGER_RECT.right + 20, BOTTOM_BAR_Y - 14), 1)

    backdrop.blit(rule_surf, (0, 0))
    return backdrop

