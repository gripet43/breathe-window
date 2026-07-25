#!/usr/bin/env python3
"""
Generate unique window-frame CSS for all 300 cities in locations.json.
Skips the 15 manually-designed themes already in index.html.
Outputs: public/assets/data/window-themes.css
"""

import json
import os
import sys
import hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOCATIONS_PATH = os.path.join(PROJECT_ROOT, "public", "assets", "data", "locations.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "public", "assets", "data", "window-themes.css")

# The 15 manually-designed themes to skip (already in index.html)
MANUAL_THEMES = {
    "loc-kyoto", "loc-reykjavik", "loc-bamboo", "loc-paris",
    "loc-marrakech", "loc-tromso", "loc-alps", "loc-venice",
    "loc-santorini", "loc-london", "loc-quebec", "loc-cairo",
    "loc-finland", "loc-hobbiton", "loc-suzhou"
}

# ─── Region classification ───────────────────────────────────────────────
# Maps country code → region tag
COUNTRY_TO_REGION = {
    # East Asia
    "cn": "east_asia", "jp": "east_asia", "kr": "east_asia",
    # Southeast Asia
    "th": "se_asia", "vn": "se_asia", "my": "se_asia", "id": "se_asia",
    "ph": "se_asia", "kh": "se_asia", "mm": "se_asia", "la": "se_asia",
    "sg": "se_asia",
    # South Asia
    "in": "south_asia", "lk": "south_asia", "np": "south_asia",
    "bt": "south_asia", "pk": "south_asia", "af": "south_asia", "bd": "south_asia",
    # Central Asia
    "uz": "central_asia", "kz": "central_asia", "kg": "central_asia",
    "tj": "central_asia", "tm": "central_asia",
    # Middle East
    "tr": "mid_east", "ae": "mid_east", "sa": "mid_east", "ir": "mid_east",
    "jo": "mid_east", "lb": "mid_east", "qa": "mid_east", "kw": "mid_east",
    "om": "mid_east", "iq": "mid_east", "il": "mid_east",
    # Western Europe
    "fr": "west_europe", "it": "west_europe", "es": "west_europe",
    "pt": "west_europe", "de": "west_europe", "at": "west_europe",
    "ch": "west_europe", "nl": "west_europe", "be": "west_europe",
    "lu": "west_europe", "mc": "west_europe", "li": "west_europe",
    # Northern Europe
    "gb": "north_europe", "ie": "north_europe", "no": "north_europe",
    "se": "north_europe", "fi": "north_europe", "is": "north_europe",
    "dk": "north_europe", "ee": "north_europe", "lv": "north_europe",
    "lt": "north_europe",
    # Eastern Europe
    "pl": "east_europe", "cz": "east_europe", "hu": "east_europe",
    "hr": "east_europe", "ro": "east_europe", "sk": "east_europe",
    "si": "east_europe", "ua": "east_europe", "ge": "east_europe",
    "am": "east_europe", "az": "east_europe", "rs": "east_europe",
    "bg": "east_europe", "ba": "east_europe", "me": "east_europe",
    "mk": "east_europe", "al": "east_europe", "md": "east_europe",
    # Russia
    "ru": "east_europe",
    # Africa
    "eg": "africa", "ma": "africa", "za": "africa", "ke": "africa",
    "tz": "africa", "tn": "africa", "dz": "africa", "mg": "africa",
    "ng": "africa", "gh": "africa", "et": "africa", "sn": "africa",
    "cm": "africa", "ci": "africa", "ao": "africa", "na": "africa",
    "bw": "africa", "zw": "africa", "ug": "africa", "rw": "africa",
    "bf": "africa", "ml": "africa", "ne": "africa", "td": "africa",
    "gm": "africa", "gn": "africa", "sl": "africa", "lr": "africa",
    "tg": "africa", "bj": "africa", "mw": "africa", "mz": "africa",
    "zm": "africa", "cd": "africa", "cg": "africa", "ga": "africa",
    "gq": "africa", "st": "africa", "cv": "africa", "sc": "africa",
    "mu": "africa", "dj": "africa", "so": "africa", "er": "africa",
    "sd": "africa", "ss": "africa", "cf": "africa", "bi": "africa",
    "sc": "africa",
    # Americas - North
    "us": "north_america", "ca": "north_america", "mx": "north_america",
    "cu": "north_america", "jm": "north_america", "ht": "north_america",
    "do": "north_america", "bs": "north_america", "cr": "north_america",
    "pa": "north_america", "gt": "north_america", "hn": "north_america",
    "sv": "north_america", "ni": "north_america", "bz": "north_america",
    "pr": "north_america", "tt": "north_america",
    # Americas - South
    "br": "south_america", "ar": "south_america", "pe": "south_america",
    "cl": "south_america", "co": "south_america", "bo": "south_america",
    "ec": "south_america", "ve": "south_america", "py": "south_america",
    "uy": "south_america", "gy": "south_america", "sr": "south_america",
    "gf": "south_america",
    # Oceania
    "au": "oceania", "nz": "oceania", "fj": "oceania",
    "pg": "oceania", "ws": "oceania", "to": "oceania",
    "vu": "oceania", "sb": "oceania", "fm": "oceania",
    "pw": "oceania", "mh": "oceania", "ki": "oceania",
    "nr": "oceania", "tv": "oceania",
}

# ─── Pattern library ──────────────────────────────────────────────────────
# Each function returns (background_image, background_size, border)
# The functions take a seed (hash of city name) for variation

def _alpha(color, a):
    """Convert hex color to rgba with opacity."""
    c = color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"rgba({r},{g},{b},{a})"

def pattern_grid_sm(wood_dark, seed):
    """Dense small grid - Japanese shoji style."""
    s = seed % 4
    sizes = [("25%", "16.6%"), ("20%", "20%"), ("33.3%", "25%"), ("25%", "25%")]
    w, h = sizes[s]
    opacity = 0.10 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} 1.5px, transparent 1.5px), linear-gradient(90deg, {c} 1.5px, transparent 1.5px)",
        f"{w} {h}",
        f"1px solid {_alpha(wood_dark, 0.12)}"
    )

def pattern_grid_md(wood_dark, seed):
    """Medium grid - Nordic style."""
    s = seed % 3
    sizes = [("50%", "50%"), ("40%", "40%"), ("50%", "33.3%")]
    w, h = sizes[s]
    thickness = 1.5 + (seed % 3) * 0.5
    opacity = 0.12 + (seed % 4) * 0.03
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{w} {h}",
        f"1px solid {_alpha(wood_dark, 0.15)}"
    )

def pattern_grid_lg(wood_dark, seed):
    """Large grid - French/Italian style."""
    s = seed % 3
    sizes = [("50%", "33.3%"), ("66.6%", "33.3%"), ("50%", "50%")]
    w, h = sizes[s]
    thickness = 2.5 + (seed % 3) * 0.5
    opacity = 0.14 + (seed % 4) * 0.03
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{w} {h}",
        f"1px solid {_alpha(wood_dark, 0.18)}"
    )

def pattern_vertical(wood_dark, seed):
    """Vertical stripes - bamboo/reed style."""
    spacing = 8 + seed % 6
    thickness = 1.5 + (seed % 3) * 0.5
    opacity = 0.06 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{spacing}px 100%",
        f"1px solid {_alpha(wood_dark, 0.08)}"
    )

def pattern_horizontal(wood_dark, seed):
    """Horizontal stripes - Aegean style."""
    spacing = 20 + seed % 15
    thickness = 2 + (seed % 3) * 0.5
    opacity = 0.10 + (seed % 4) * 0.03
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px)",
        f"100% {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.12)}"
    )

def pattern_diagonal(wood_dark, seed):
    """Diagonal lines."""
    spacing = 12 + seed % 8
    thickness = 1 + (seed % 3) * 0.5
    opacity = 0.08 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(-45deg, {c} {thickness}px, transparent {thickness}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_diamond(wood_dark, seed):
    """Diamond lattice - Chinese ice-crack style."""
    spacing = 20 + seed % 12
    thickness = 1 + (seed % 3) * 0.5
    opacity = 0.07 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(-45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.12)}"
    )

def pattern_dots(wood_dark, seed):
    """Dot pattern - Moroccan/Middle Eastern style."""
    spacing = 14 + seed % 8
    radius = 2.5 + (seed % 3) * 0.5
    opacity = 0.08 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"radial-gradient(circle at center, {c} {radius}px, transparent {radius + 0.5}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_cross(wood_dark, seed):
    """Cross pattern - Alpine chalet style."""
    spacing = 40 + seed % 20
    thickness = 2 + (seed % 3) * 0.5
    opacity = 0.12 + (seed % 4) * 0.03
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px), linear-gradient({c} {thickness}px, transparent {thickness}px)",
        f"50% 50%",
        f"1px solid {_alpha(wood_dark, 0.15)}"
    )

def pattern_four_square(wood_dark, seed):
    """Four-square grid - Scandinavian style."""
    thickness = 1.5 + (seed % 3) * 0.5
    opacity = 0.14 + (seed % 4) * 0.03
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        "50% 50%",
        f"1px solid {_alpha(wood_dark, 0.18)}"
    )

def pattern_brick(wood_dark, seed):
    """Brick pattern - ancient city walls."""
    w = 30 + seed % 15
    h = 15 + seed % 8
    thickness = 1 + (seed % 2) * 0.5
    opacity = 0.08 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{w}px {h}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_hex(wood_dark, seed):
    """Hexagonal dot pattern - Islamic geometric."""
    spacing = 18 + seed % 10
    radius = 3 + (seed % 3) * 0.5
    opacity = 0.07 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"radial-gradient(circle at center, {c} {radius}px, transparent {radius + 0.5}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.08)}"
    )

def pattern_star(wood_dark, seed):
    """Star/compass pattern - Central Asian style."""
    spacing = 24 + seed % 12
    thickness = 1 + (seed % 2) * 0.5
    opacity = 0.06 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(0deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(-45deg, {c} {thickness}px, transparent {thickness}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_mosaic(wood_dark, seed):
    """Mosaic tile pattern - Mediterranean."""
    size = 16 + seed % 10
    thickness = 1 + (seed % 2) * 0.5
    opacity = 0.06 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(-45deg, {c} {thickness}px, transparent {thickness}px)",
        f"{size}px {size}px",
        f"1px solid {_alpha(wood_dark, 0.08)}"
    )

def pattern_wave(wood_dark, seed):
    """Wave-like horizontal lines - coastal."""
    spacing = 10 + seed % 6
    thickness = 1 + (seed % 2) * 0.5
    opacity = 0.06 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px)",
        f"100% {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.06)}"
    )

def pattern_arch(wood_dark, seed):
    """Arch/pointed arch pattern - Islamic/Mughal."""
    spacing = 28 + seed % 14
    thickness = 1.5 + (seed % 2) * 0.5
    opacity = 0.07 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"radial-gradient(ellipse at 50% 0%, transparent {spacing//2 - 2}px, {c} {spacing//2 - 1}px, {c} {spacing//2}px, transparent {spacing//2 + 1}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_lattice(wood_dark, seed):
    """Flower lattice - Chinese garden window."""
    spacing = 22 + seed % 12
    thickness = 1 + (seed % 3) * 0.5
    opacity = 0.07 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(-45deg, {c} {thickness}px, transparent {thickness}px), linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{spacing}px {spacing}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_slate(wood_dark, seed):
    """Slate/stone texture - mountainous regions."""
    w = 40 + seed % 20
    h = 20 + seed % 10
    thickness = 1 + (seed % 2) * 0.5
    opacity = 0.06 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{w}px {h}px",
        f"1px solid {_alpha(wood_dark, 0.08)}"
    )

def pattern_timber(wood_dark, seed):
    """Timber/wood plank pattern - forest regions."""
    spacing = 12 + seed % 8
    thickness = 1 + (seed % 2) * 0.5
    opacity = 0.05 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px)",
        f"{spacing}px 100%",
        f"1px solid {_alpha(wood_dark, 0.06)}"
    )

def pattern_tile(wood_dark, seed):
    """Decorative tile pattern - Southern European/Latin."""
    size = 20 + seed % 12
    thickness = 1.5 + (seed % 2) * 0.5
    opacity = 0.07 + (seed % 5) * 0.02
    c = _alpha(wood_dark, opacity)
    return (
        f"linear-gradient({c} {thickness}px, transparent {thickness}px), linear-gradient(90deg, {c} {thickness}px, transparent {thickness}px), linear-gradient(45deg, {c} {thickness * 0.5}px, transparent {thickness * 0.5}px), linear-gradient(-45deg, {c} {thickness * 0.5}px, transparent {thickness * 0.5}px)",
        f"{size}px {size}px",
        f"1px solid {_alpha(wood_dark, 0.10)}"
    )

def pattern_minimal(wood_dark, seed):
    """Minimal single line - modern urban."""
    s = seed % 2
    if s == 0:
        return (
            f"linear-gradient(90deg, {_alpha(wood_dark, 0.08)} 2px, transparent 2px)",
            "50% 100%",
            f"1px solid {_alpha(wood_dark, 0.06)}"
        )
    else:
        return (
            f"linear-gradient({_alpha(wood_dark, 0.08)} 2px, transparent 2px)",
            "100% 50%",
            f"1px solid {_alpha(wood_dark, 0.06)}"
        )

# ─── Region → pattern mapping ─────────────────────────────────────────────
# Each region maps to a list of (pattern_fn, weight) tuples
# Weight determines probability; higher = more likely

REGION_PATTERNS = {
    "east_asia": [
        (pattern_lattice, 3),      # Chinese garden lattice
        (pattern_grid_sm, 3),      # Japanese shoji grid
        (pattern_diamond, 2),      # Diamond lattice
        (pattern_grid_md, 1),      # Medium grid
        (pattern_vertical, 1),     # Bamboo vertical
    ],
    "se_asia": [
        (pattern_vertical, 3),     # Bamboo/reed vertical
        (pattern_timber, 2),       # Wood planks
        (pattern_lattice, 1),      # Lattice
        (pattern_tile, 1),         # Decorative tiles
    ],
    "south_asia": [
        (pattern_arch, 3),         # Mughal arches
        (pattern_diamond, 2),      # Geometric diamond
        (pattern_hex, 1),          # Hexagonal
        (pattern_mosaic, 1),       # Mosaic
        (pattern_star, 1),         # Star pattern
    ],
    "central_asia": [
        (pattern_star, 3),         # Islamic star
        (pattern_hex, 2),          # Hexagonal
        (pattern_arch, 1),         # Arches
        (pattern_diamond, 1),      # Diamond
    ],
    "mid_east": [
        (pattern_arch, 3),         # Islamic arches
        (pattern_star, 2),         # Star/geometric
        (pattern_hex, 2),          # Hexagonal
        (pattern_dots, 1),         # Dots
    ],
    "west_europe": [
        (pattern_grid_lg, 2),      # French large grid
        (pattern_tile, 2),         # Decorative tiles
        (pattern_cross, 2),        # Cross pattern
        (pattern_lattice, 1),      # Lattice
        (pattern_grid_md, 1),      # Medium grid
    ],
    "north_europe": [
        (pattern_grid_md, 2),      # Nordic grid
        (pattern_four_square, 2),  # Four-square
        (pattern_slate, 2),        # Stone texture
        (pattern_cross, 1),        # Cross
        (pattern_minimal, 1),      # Minimal
    ],
    "east_europe": [
        (pattern_brick, 2),        # Brick walls
        (pattern_cross, 2),        # Cross pattern
        (pattern_grid_md, 2),      # Medium grid
        (pattern_mosaic, 1),       # Mosaic
        (pattern_tile, 1),         # Tiles
    ],
    "africa": [
        (pattern_dots, 2),         # Dots
        (pattern_hex, 2),          # Hexagonal
        (pattern_mosaic, 2),       # Mosaic
        (pattern_diamond, 1),      # Diamond
        (pattern_brick, 1),        # Brick
    ],
    "north_america": [
        (pattern_minimal, 2),      # Modern minimal
        (pattern_grid_md, 1),      # Grid
        (pattern_timber, 1),       # Timber
        (pattern_slate, 1),        # Stone
        (pattern_cross, 1),        # Cross
        (pattern_tile, 1),         # Tile
    ],
    "south_america": [
        (pattern_tile, 3),         # Decorative tiles
        (pattern_mosaic, 2),       # Mosaic
        (pattern_brick, 1),        # Brick
        (pattern_diamond, 1),      # Diamond
        (pattern_cross, 1),        # Cross
    ],
    "oceania": [
        (pattern_timber, 2),       # Timber
        (pattern_slate, 2),        # Stone
        (pattern_minimal, 2),      # Minimal
        (pattern_wave, 1),         # Wave
        (pattern_grid_md, 1),      # Grid
    ],
}


def city_hash(name):
    """Deterministic hash for a city name."""
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def select_pattern(region, seed):
    """Select a pattern function based on region and seed."""
    patterns = REGION_PATTERNS.get(region, REGION_PATTERNS["north_america"])
    # Weighted selection using seed
    total_weight = sum(w for _, w in patterns)
    target = seed % total_weight
    cumulative = 0
    for fn, weight in patterns:
        cumulative += weight
        if target < cumulative:
            return fn
    return patterns[-1][0]


def generate_css(loc):
    """Generate CSS for a single location."""
    name = loc["name"]
    loc_class = loc["locClass"]
    wood = loc.get("wood", "#8B7355")
    wood_dark = loc.get("woodDark", "#5E4E3A")
    glow = loc.get("glow", f"radial-gradient(circle at center, #FFF8EF 20%, #E5D3B3 100%)")

    cc = (loc.get("countryCode") or "").lower()
    region = COUNTRY_TO_REGION.get(cc, "north_america")
    seed = city_hash(name)

    pattern_fn = select_pattern(region, seed)
    bg_image, bg_size, border = pattern_fn(wood_dark, seed)

    return f"""  .{loc_class} {{
    --wood: {wood};
    --wood-dark: {wood_dark};
    --glow: {glow};
  }}
  .{loc_class} .shutter-grid {{
    background-image: {bg_image};
    background-size: {bg_size};
    border: {border};
  }}"""


def main():
    with open(LOCATIONS_PATH, "r", encoding="utf-8") as f:
        locations = json.load(f)

    generated = []
    skipped = []

    for loc in locations:
        loc_class = loc.get("locClass", "")
        if loc_class in MANUAL_THEMES:
            skipped.append(loc_class)
            continue
        generated.append(generate_css(loc))

    css = f"""/* ==========================================================================
   Auto-generated window themes for {len(generated)} cities
   Generated by scripts/generate_window_css.py
   Skipped {len(skipped)} manually-designed themes: {', '.join(sorted(skipped))}
   ========================================================================== */

"""
    css += "\n\n".join(generated)
    css += "\n"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(css)

    print(f"Generated CSS for {len(generated)} cities")
    print(f"Skipped {len(skipped)} manual themes")
    print(f"Output: {OUTPUT_PATH}")
    print(f"File size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
