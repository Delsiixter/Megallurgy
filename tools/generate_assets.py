#!/usr/bin/env python3
"""
Genere toutes les ressources de Metallia (textures, modeles, langues, recettes,
loot tables, tags, generation de minerais).

Usage : python3 tools/generate_assets.py
Dependance : Pillow (pip install pillow)

Pour ajouter un metal, ajoutez-le dans METALS puis relancez le script
(et ajoutez le code Java correspondant : tier, materiau d'armure, objets, blocs).
"""
import json
import os
import random

from PIL import Image

MOD = "metallia"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources")
ASSETS = os.path.join(ROOT, "assets", MOD)
DATA = os.path.join(ROOT, "data", MOD)

# ----------------------------------------------------------------------------
# Definition des metaux
# ----------------------------------------------------------------------------
METALS = {
    "tin": dict(
        en="Tin", fr="étain", fr_de="d'étain", ore="overworld", raw=True,
        pal=dict(M=(196, 204, 212), L=(236, 241, 246), D=(128, 138, 152), A=(255, 255, 255)),
        needs="minecraft:needs_stone_tool", block_needs="minecraft:needs_stone_tool",
    ),
    "bronze": dict(
        en="Bronze", fr="bronze", fr_de="de bronze", ore=None, raw=False,
        pal=dict(M=(190, 120, 58), L=(232, 170, 96), D=(122, 72, 34), A=(246, 206, 130)),
        block_needs="minecraft:needs_stone_tool",
    ),
    "ignatium": dict(
        en="Ignatium", fr="ignatium", fr_de="d'ignatium", ore="nether", raw=True,
        pal=dict(M=(214, 76, 30), L=(255, 150, 48), D=(128, 32, 16), A=(255, 224, 90)),
        needs="minecraft:needs_iron_tool", block_needs="minecraft:needs_iron_tool",
    ),
    "voidium": dict(
        en="Voidium", fr="voidium", fr_de="de voidium", ore="end", raw=True,
        pal=dict(M=(98, 54, 150), L=(172, 112, 234), D=(42, 22, 74), A=(224, 182, 255)),
        needs="minecraft:needs_diamond_tool", block_needs="minecraft:needs_diamond_tool",
    ),
}

TOOLS = ["sword", "pickaxe", "axe", "shovel", "hoe"]
ARMORS = ["helmet", "chestplate", "leggings", "boots"]

TOOL_NAMES = {
    "sword": ("Sword", "Épée"), "pickaxe": ("Pickaxe", "Pioche"), "axe": ("Axe", "Hache"),
    "shovel": ("Shovel", "Pelle"), "hoe": ("Hoe", "Houe"),
    "helmet": ("Helmet", "Casque"), "chestplate": ("Chestplate", "Plastron"),
    "leggings": ("Leggings", "Jambières"), "boots": ("Boots", "Bottes"),
}


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def save_png(path, img):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, f):
    return tuple(clamp(x * f) for x in c[:3])


def jitter(c, rng, amount):
    d = rng.randint(-amount, amount)
    return tuple(clamp(x + d) for x in c[:3])


# ----------------------------------------------------------------------------
# Sprites d'objets (16x16) dessines sur une grille de codes
# ----------------------------------------------------------------------------
HANDLE = {"H": (122, 86, 48), "K": (162, 120, 72), "h": (82, 56, 30)}


def new_grid():
    return [[None] * 16 for _ in range(16)]


def put(g, x, y, code):
    if 0 <= x < 16 and 0 <= y < 16:
        g[y][x] = code


def line(g, x0, y0, x1, y1, code):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        put(g, x0, y0, code)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def rect(g, x0, y0, x1, y1, code):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(g, x, y, code)


def pixels(g, pts, code):
    for (x, y) in pts:
        put(g, x, y, code)


def empty(g, x, y):
    return not (0 <= x < 16 and 0 <= y < 16) or g[y][x] is None


def render_grid(g, pal, seed):
    rng = random.Random(seed)
    # 1) ombrage des metaux et des manches
    shaded = [row[:] for row in g]
    for y in range(16):
        for x in range(16):
            c = g[y][x]
            if c == "M":
                if empty(g, x - 1, y) or empty(g, x, y - 1):
                    shaded[y][x] = "L"
                elif empty(g, x + 1, y) or empty(g, x, y + 1):
                    shaded[y][x] = "D"
            elif c == "H":
                if empty(g, x - 1, y) or empty(g, x, y - 1):
                    shaded[y][x] = "K"
                elif empty(g, x + 1, y) or empty(g, x, y + 1):
                    shaded[y][x] = "h"
    # 2) petits eclats d'accent
    for y in range(16):
        for x in range(16):
            if shaded[y][x] in ("M", "L") and rng.random() < 0.10:
                shaded[y][x] = "A"
    # 3) contour
    outline = shade(pal["D"], 0.42)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y in range(16):
        for x in range(16):
            c = shaded[y][x]
            if c is None:
                near = any(not empty(g, x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if near:
                    px[x, y] = outline + (255,)
                continue
            if c in pal:
                col = pal[c]
            elif c == "G":
                col = shade(pal["D"], 1.1)
            else:
                col = HANDLE[c]
            px[x, y] = tuple(col[:3]) + (255,)
    return img


def sprite_sword():
    g = new_grid()
    for t in range(5, 14):
        put(g, t, 15 - t, "M")
        put(g, t + 1, 15 - t, "M")
    put(g, 14, 1, "M")
    line(g, 3, 8, 7, 12, "G")
    line(g, 4, 11, 2, 13, "H")
    put(g, 1, 14, "h")
    return g


def sprite_pickaxe():
    g = new_grid()
    line(g, 3, 13, 12, 4, "H")
    pixels(g, [(4, 6), (5, 5), (6, 4), (7, 3), (8, 2), (9, 2), (10, 2), (11, 2), (12, 3), (13, 4),
               (14, 5), (14, 6)], "M")
    pixels(g, [(5, 6), (6, 5), (7, 4), (8, 3), (9, 3), (10, 3), (11, 3), (12, 4), (13, 5)], "M")
    return g


def sprite_axe():
    g = new_grid()
    line(g, 3, 13, 10, 6, "H")
    rect(g, 10, 2, 12, 2, "M")
    rect(g, 9, 3, 13, 4, "M")
    rect(g, 10, 5, 12, 5, "M")
    rect(g, 10, 6, 11, 6, "M")
    return g


def sprite_shovel():
    g = new_grid()
    line(g, 3, 13, 10, 6, "H")
    rect(g, 12, 1, 13, 1, "M")
    rect(g, 11, 2, 14, 3, "M")
    rect(g, 11, 4, 13, 4, "M")
    pixels(g, [(11, 5), (12, 5)], "M")
    return g


def sprite_hoe():
    g = new_grid()
    line(g, 3, 13, 11, 5, "H")
    rect(g, 9, 2, 12, 2, "M")
    rect(g, 8, 3, 12, 3, "M")
    pixels(g, [(8, 4), (9, 4), (8, 5)], "M")
    return g


def sprite_ingot():
    g = new_grid()
    for y, (x0, x1) in zip(range(5, 9), [(6, 13), (5, 12), (4, 11), (3, 10)]):
        rect(g, x0, y, x1, y, "M")
    rect(g, 3, 9, 10, 10, "M")
    return g


def sprite_helmet():
    g = new_grid()
    rect(g, 4, 2, 11, 2, "M")
    rect(g, 3, 3, 12, 8, "M")
    rect(g, 3, 9, 5, 11, "M")
    rect(g, 10, 9, 12, 11, "M")
    return g


def sprite_chestplate():
    g = new_grid()
    rect(g, 4, 3, 11, 13, "M")
    rect(g, 2, 2, 5, 4, "M")
    rect(g, 10, 2, 13, 4, "M")
    rect(g, 1, 5, 3, 9, "M")
    rect(g, 12, 5, 14, 9, "M")
    rect(g, 6, 2, 9, 3, None)
    return g


def sprite_leggings():
    g = new_grid()
    rect(g, 4, 2, 11, 7, "M")
    rect(g, 4, 8, 6, 13, "M")
    rect(g, 9, 8, 11, 13, "M")
    return g


def sprite_boots():
    g = new_grid()
    rect(g, 3, 4, 6, 9, "M")
    rect(g, 2, 10, 6, 12, "M")
    rect(g, 9, 4, 12, 9, "M")
    rect(g, 9, 10, 13, 12, "M")
    return g


SPRITES = {
    "sword": sprite_sword, "pickaxe": sprite_pickaxe, "axe": sprite_axe,
    "shovel": sprite_shovel, "hoe": sprite_hoe, "ingot": sprite_ingot,
    "helmet": sprite_helmet, "chestplate": sprite_chestplate,
    "leggings": sprite_leggings, "boots": sprite_boots,
}


def sprite_raw(pal, seed):
    rng = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    rock = (128, 118, 108)
    cells = []
    for y in range(16):
        for x in range(16):
            dx, dy = (x - 7.5) / 5.6, (y - 8.5) / 4.6
            if dx * dx + dy * dy <= 1.0 + rng.uniform(-0.18, 0.18):
                cells.append((x, y))
    cellset = set(cells)
    for (x, y) in cells:
        r = rng.random()
        if r < 0.42:
            col = jitter(pal["M"], rng, 14)
        elif r < 0.55:
            col = pal["L"]
        else:
            col = jitter(rock, rng, 12)
        if (x, y + 1) not in cellset or (x + 1, y) not in cellset:
            col = shade(col, 0.75)
        elif (x - 1, y) not in cellset or (x, y - 1) not in cellset:
            col = shade(col, 1.12)
        px[x, y] = tuple(col) + (255,)
    outline = shade(pal["D"], 0.42)
    for y in range(16):
        for x in range(16):
            if (x, y) in cellset:
                continue
            if any((x + dx, y + dy) in cellset for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = outline + (255,)
    return img


# ----------------------------------------------------------------------------
# Textures de blocs (16x16)
# ----------------------------------------------------------------------------
def noise_base(base, seed, amount=10):
    rng = random.Random(seed)
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = jitter(base, rng, amount) + (255,)
    return img


def ore_texture(host, pal, seed):
    rng = random.Random(seed)
    img = noise_base(host, seed, 9)
    px = img.load()
    # petites fissures sombres
    for _ in range(14):
        x, y = rng.randint(0, 15), rng.randint(0, 15)
        px[x, y] = shade(host, 0.78) + (255,)
    # filons de metal
    for _ in range(7):
        cx, cy = rng.randint(1, 14), rng.randint(1, 14)
        for _ in range(rng.randint(3, 5)):
            x = max(0, min(15, cx + rng.randint(-1, 1)))
            y = max(0, min(15, cy + rng.randint(-1, 1)))
            r = rng.random()
            col = pal["L"] if r < 0.25 else pal["D"] if r < 0.45 else pal["M"]
            px[x, y] = tuple(col) + (255,)
    return img


def metal_block_texture(pal, seed):
    rng = random.Random(seed)
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            col = jitter(pal["M"], rng, 6)
            if x == 0 or y == 0 or x == 15 or y == 15:
                col = shade(pal["D"], 1.0)
            elif x == 1 or y == 1:
                col = pal["L"]
            elif x == 14 or y == 14:
                col = shade(pal["M"], 0.85)
            px[x, y] = tuple(col) + (255,)
    for (x, y) in [(3, 3), (12, 3), (3, 12), (12, 12)]:
        px[x, y] = shade(pal["D"], 0.9) + (255,)
    for i in range(3, 13):
        px[i, 8] = shade(pal["M"], 0.88) + (255,)
        px[8, i] = shade(pal["M"], 0.88) + (255,)
    return img


def furnace_textures():
    stone = (122, 122, 128)
    out = {}
    # cote : briques
    rng = random.Random(7)
    side = Image.new("RGBA", (16, 16))
    px = side.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = jitter(stone, rng, 8) + (255,)
    for y in (3, 7, 11, 15):
        for x in range(16):
            px[x, y] = shade(stone, 0.62) + (255,)
    for row, y0 in enumerate((0, 4, 8, 12)):
        off = 0 if row % 2 == 0 else 4
        for x in (off, off + 8):
            for y in range(y0, y0 + 3):
                if x < 16:
                    px[x, y] = shade(stone, 0.68) + (255,)
    out["side"] = side

    # dessus : plaque de bronze
    top = Image.new("RGBA", (16, 16))
    px = top.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = jitter(shade(stone, 0.92), rng, 6) + (255,)
    bronze = ((190, 120, 58), (232, 170, 96), (122, 72, 34))
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)):
            px[x, y] = bronze[2] + (255,)
        for (x, y) in ((i, 1), (1, i)):
            if 1 <= i <= 14:
                px[x, y] = bronze[1] + (255,)
        for (x, y) in ((i, 14), (14, i)):
            if 1 <= i <= 14:
                px[x, y] = bronze[0] + (255,)
    for y in range(5, 11):
        for x in range(5, 11):
            d = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d < 9:
                px[x, y] = shade(stone, 0.45) + (255,)
            elif d < 14:
                px[x, y] = bronze[0] + (255,)
    out["top"] = top

    def front(lit):
        img = Image.new("RGBA", (16, 16))
        p = img.load()
        r = random.Random(11)
        for y in range(16):
            for x in range(16):
                p[x, y] = jitter(stone, r, 8) + (255,)
        # liseres de bronze en haut et en bas
        for x in range(16):
            for y in (0, 1, 14, 15):
                p[x, y] = (bronze[0] if y in (1, 14) else bronze[2]) + (255,)
        # ouverture
        for y in range(4, 13):
            for x in range(3, 13):
                if y == 4 and x in (3, 12):
                    continue
                if lit:
                    t = (y - 4) / 8.0
                    col = (255, clamp(120 + 110 * t), clamp(20 + 40 * t))
                    if (x + y) % 5 == 0:
                        col = (255, 200, 60)
                else:
                    col = (28, 24, 24)
                p[x, y] = col + (255,)
        # grille
        for x in range(3, 13):
            p[x, 12] = shade(stone, 0.5) + (255,)
        for y in range(4, 13):
            p[3, y] = shade(stone, 0.55) + (255,)
            p[12, y] = shade(stone, 0.55) + (255,)
        return img

    out["front"] = front(False)
    out["front_on"] = front(True)
    return out


# ----------------------------------------------------------------------------
# Textures d'armure (couches 64x32)
# ----------------------------------------------------------------------------
FACES = {
    "head": [(8, 0, 8, 8), (16, 0, 8, 8), (0, 8, 8, 8), (8, 8, 8, 8), (16, 8, 8, 8), (24, 8, 8, 8)],
    "body": [(20, 16, 8, 4), (28, 16, 8, 4), (16, 20, 4, 12), (20, 20, 8, 12), (28, 20, 4, 12), (32, 20, 8, 12)],
    "arm": [(44, 16, 4, 4), (48, 16, 4, 4), (40, 20, 4, 12), (44, 20, 4, 12), (48, 20, 4, 12), (52, 20, 4, 12)],
    "leg": [(4, 16, 4, 4), (8, 16, 4, 4), (0, 20, 4, 12), (4, 20, 4, 12), (8, 20, 4, 12), (12, 20, 4, 12)],
}


def paint_face(px, rect_, pal, rng, factor, accent_rate):
    x0, y0, w, h = rect_
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            lx, ly = x - x0, y - y0
            col = jitter(pal["M"], rng, 7)
            if ly == 0 or lx == 0:
                col = pal["L"]
            elif ly == h - 1 or lx == w - 1:
                col = pal["D"]
            elif (ly % 4 == 3) and w >= 8:
                col = shade(pal["M"], 0.86)
            if rng.random() < accent_rate:
                col = pal["A"]
            px[x, y] = shade(col, factor) + (255,)
    # rivet central sur les grandes faces
    if w >= 8 and h >= 8:
        cx, cy = x0 + w // 2, y0 + h // 2
        px[cx, cy] = pal["A"] + (255,)
        px[cx - 1, cy] = pal["D"] + (255,)


def armor_layer(pal, layer, seed, accent_rate):
    rng = random.Random(seed)
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    px = img.load()
    factor = 1.0 if layer == 1 else 0.9
    parts = ["head", "body", "arm", "leg"] if layer == 1 else ["body", "leg"]
    for part in parts:
        for r in FACES[part]:
            paint_face(px, r, pal, rng, factor, accent_rate)
    return img


# ----------------------------------------------------------------------------
# Interface du fourneau a alliages (256x256, zone utile 176x166)
# ----------------------------------------------------------------------------
def gui_texture():
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    px = img.load()
    bg, light, dark = (198, 198, 198), (255, 255, 255), (85, 85, 85)
    for y in range(166):
        for x in range(176):
            px[x, y] = bg + (255,)
    for x in range(176):
        for y in (0, 1):
            px[x, y] = light + (255,)
        for y in (164, 165):
            px[x, y] = dark + (255,)
    for y in range(166):
        for x in (0, 1):
            px[x, y] = light + (255,)
        for x in (174, 175):
            px[x, y] = dark + (255,)
    for (x, y) in ((0, 0), (175, 165)):
        px[x, y] = (0, 0, 0, 255)

    def slot(sx, sy, size=18):
        for y in range(sy, sy + size):
            for x in range(sx, sx + size):
                px[x, y] = (139, 139, 139, 255)
        for i in range(size):
            px[sx + i, sy] = (55, 55, 55, 255)
            px[sx, sy + i] = (55, 55, 55, 255)
            px[sx + i, sy + size - 1] = (255, 255, 255, 255)
            px[sx + size - 1, sy + i] = (255, 255, 255, 255)

    slot(37, 16)    # ingredient A
    slot(73, 16)    # ingredient B
    slot(55, 52)    # combustible
    slot(112, 31, 26)  # resultat
    for row in range(3):
        for col in range(9):
            slot(7 + col * 18, 83 + row * 18)
    for col in range(9):
        slot(7 + col * 18, 141)

    arrow = [(x, y) for y in range(17) for x in range(24) if
             (6 <= y <= 10 and x <= 15) or (x >= 16 and abs(y - 8) <= (23 - x))]

    # fond de la fleche et de la flamme
    for (x, y) in arrow:
        px[84 + x, 35 + y] = (139, 139, 139, 255)
    flame = flame_pixels()
    for (x, y) in flame:
        px[56 + x, 36 + y] = (110, 110, 110, 255)
    # superpositions (animees par le code)
    for (x, y) in flame:
        px[176 + x, 0 + y] = (255, 170 + (y * 6) % 60, 20, 255)
    for (x, y) in arrow:
        px[176 + x, 14 + y] = (240, 150, 40, 255)
    return img


def flame_pixels():
    pts = []
    for y in range(14):
        if y < 3:
            half = 1
        elif y < 8:
            half = 3
        else:
            half = 5
        if y == 13:
            half = 4
        cx = 6.5
        for x in range(14):
            if abs(x - cx) <= half:
                pts.append((x, y))
    return pts


# ----------------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------------
def gen_textures():
    for name, m in METALS.items():
        pal = m["pal"]
        seed = sum(ord(c) for c in name)
        # lingot
        save_png(os.path.join(ASSETS, "textures", "item", f"{name}_ingot.png"),
                 render_grid(SPRITES["ingot"](), pal, seed))
        # outils et armures
        for t in TOOLS + ARMORS:
            save_png(os.path.join(ASSETS, "textures", "item", f"{name}_{t}.png"),
                     render_grid(SPRITES[t](), pal, seed + len(t)))
        # brut
        if m["raw"]:
            save_png(os.path.join(ASSETS, "textures", "item", f"raw_{name}.png"), sprite_raw(pal, seed))
        # bloc de metal
        save_png(os.path.join(ASSETS, "textures", "block", f"{name}_block.png"),
                 metal_block_texture(pal, seed))
        # armure portee
        rate = {"tin": 0.02, "bronze": 0.02, "ignatium": 0.07, "voidium": 0.06}[name]
        for layer in (1, 2):
            save_png(os.path.join(ASSETS, "textures", "models", "armor", f"{name}_layer_{layer}.png"),
                     armor_layer(pal, layer, seed * 3 + layer, rate))

    hosts = {"overworld": (125, 125, 125), "nether": (112, 46, 46), "end": (221, 224, 160)}
    for name, m in METALS.items():
        if m["ore"]:
            save_png(os.path.join(ASSETS, "textures", "block", f"{name}_ore.png"),
                     ore_texture(hosts[m["ore"]], m["pal"], sum(ord(c) for c in name) * 7))

    ft = furnace_textures()
    for key, img in ft.items():
        save_png(os.path.join(ASSETS, "textures", "block", f"alloy_furnace_{key}.png"), img)

    save_png(os.path.join(ASSETS, "textures", "gui", "alloy_furnace_gui.png"), gui_texture())


def all_item_ids():
    ids = []
    for name, m in METALS.items():
        ids.append(f"{name}_ingot")
        if m["raw"]:
            ids.append(f"raw_{name}")
        ids += [f"{name}_{t}" for t in TOOLS + ARMORS]
    return ids


def all_block_ids():
    blocks = [f"{n}_block" for n in METALS] + [f"{n}_ore" for n, m in METALS.items() if m["ore"]]
    return blocks + ["alloy_furnace"]


def gen_models():
    for name, m in METALS.items():
        write_json(os.path.join(ASSETS, "models", "item", f"{name}_ingot.json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}_ingot"}})
        if m["raw"]:
            write_json(os.path.join(ASSETS, "models", "item", f"raw_{name}.json"),
                       {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/raw_{name}"}})
        for t in TOOLS:
            write_json(os.path.join(ASSETS, "models", "item", f"{name}_{t}.json"),
                       {"parent": "minecraft:item/handheld", "textures": {"layer0": f"{MOD}:item/{name}_{t}"}})
        for t in ARMORS:
            write_json(os.path.join(ASSETS, "models", "item", f"{name}_{t}.json"),
                       {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}_{t}"}})

    for b in all_block_ids():
        if b == "alloy_furnace":
            continue
        write_json(os.path.join(ASSETS, "models", "block", f"{b}.json"),
                   {"parent": "minecraft:block/cube_all", "textures": {"all": f"{MOD}:block/{b}"}})
        write_json(os.path.join(ASSETS, "blockstates", f"{b}.json"),
                   {"variants": {"": {"model": f"{MOD}:block/{b}"}}})
        write_json(os.path.join(ASSETS, "models", "item", f"{b}.json"), {"parent": f"{MOD}:block/{b}"})

    # fourneau a alliages
    for suffix, front in (("", "alloy_furnace_front"), ("_on", "alloy_furnace_front_on")):
        write_json(os.path.join(ASSETS, "models", "block", f"alloy_furnace{suffix}.json"), {
            "parent": "minecraft:block/orientable",
            "textures": {
                "top": f"{MOD}:block/alloy_furnace_top",
                "front": f"{MOD}:block/{front}",
                "side": f"{MOD}:block/alloy_furnace_side",
            },
        })
    variants = {}
    for facing, rot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for lit in ("false", "true"):
            model = f"{MOD}:block/alloy_furnace" + ("_on" if lit == "true" else "")
            v = {"model": model}
            if rot:
                v["y"] = rot
            variants[f"facing={facing},lit={lit}"] = v
    write_json(os.path.join(ASSETS, "blockstates", "alloy_furnace.json"), {"variants": variants})
    write_json(os.path.join(ASSETS, "models", "item", "alloy_furnace.json"),
               {"parent": f"{MOD}:block/alloy_furnace"})


def gen_lang():
    en = {"itemGroup.metallia": "Metallia", "block.metallia.alloy_furnace": "Alloy Furnace"}
    fr = {"itemGroup.metallia": "Metallia", "block.metallia.alloy_furnace": "Fourneau à alliages"}
    for name, m in METALS.items():
        en[f"item.{MOD}.{name}_ingot"] = f"{m['en']} Ingot"
        fr[f"item.{MOD}.{name}_ingot"] = f"Lingot {m['fr_de']}"
        en[f"block.{MOD}.{name}_block"] = f"Block of {m['en']}"
        fr[f"block.{MOD}.{name}_block"] = f"Bloc {m['fr_de']}"
        if m["raw"]:
            en[f"item.{MOD}.raw_{name}"] = f"Raw {m['en']}"
            fr[f"item.{MOD}.raw_{name}"] = f"{m['fr'].capitalize()} brut"
            en[f"block.{MOD}.{name}_ore"] = f"{m['en']} Ore"
            fr[f"block.{MOD}.{name}_ore"] = f"Minerai {m['fr_de']}"
        for t in TOOLS + ARMORS:
            e, f = TOOL_NAMES[t]
            en[f"item.{MOD}.{name}_{t}"] = f"{m['en']} {e}"
            prep = "en " + m["fr"]
            fr[f"item.{MOD}.{name}_{t}"] = f"{f} {prep}"
    write_json(os.path.join(ASSETS, "lang", "en_us.json"), en)
    write_json(os.path.join(ASSETS, "lang", "fr_fr.json"), fr)


def ing(item):
    return {"item": f"{MOD}:{item}"}


def gen_recipes():
    rdir = os.path.join(DATA, "recipes")
    for name, m in METALS.items():
        ingot = f"{MOD}:{name}_ingot"
        # bloc <-> lingots
        write_json(os.path.join(rdir, f"{name}_block.json"), {
            "type": "minecraft:crafting_shaped", "category": "building",
            "pattern": ["III", "III", "III"], "key": {"I": {"item": ingot}},
            "result": {"item": f"{MOD}:{name}_block"}})
        write_json(os.path.join(rdir, f"{name}_ingot_from_{name}_block.json"), {
            "type": "minecraft:crafting_shapeless", "category": "misc",
            "ingredients": [{"item": f"{MOD}:{name}_block"}],
            "result": {"item": ingot, "count": 9}})

        stick = {"item": "minecraft:stick"}
        x = {"item": ingot}
        shaped = {
            "sword": (["X", "X", "S"], "equipment"),
            "pickaxe": (["XXX", " S ", " S "], "equipment"),
            "axe": (["XX", "XS", " S"], "equipment"),
            "shovel": (["X", "S", "S"], "equipment"),
            "hoe": (["XX", " S", " S"], "equipment"),
            "helmet": (["XXX", "X X"], "equipment"),
            "chestplate": (["X X", "XXX", "XXX"], "equipment"),
            "leggings": (["XXX", "X X", "X X"], "equipment"),
            "boots": (["X X", "X X"], "equipment"),
        }
        for t, (pattern, cat) in shaped.items():
            key = {"X": x}
            if "S" in "".join(pattern):
                key["S"] = stick
            write_json(os.path.join(rdir, f"{name}_{t}.json"), {
                "type": "minecraft:crafting_shaped", "category": cat,
                "pattern": pattern, "key": key, "result": {"item": f"{MOD}:{name}_{t}"}})

        if m["raw"]:
            for src, label in ((f"raw_{name}", "raw"), (f"{name}_ore", "ore")):
                tag_item = {"item": f"{MOD}:{src}"}
                write_json(os.path.join(rdir, f"{name}_ingot_from_smelting_{label}.json"), {
                    "type": "minecraft:smelting", "category": "misc", "ingredient": tag_item,
                    "result": ingot, "experience": 0.7, "cookingtime": 200})
                write_json(os.path.join(rdir, f"{name}_ingot_from_blasting_{label}.json"), {
                    "type": "minecraft:blasting", "category": "misc", "ingredient": tag_item,
                    "result": ingot, "experience": 0.7, "cookingtime": 100})

    # fourneau a alliages
    write_json(os.path.join(rdir, "alloy_furnace.json"), {
        "type": "minecraft:crafting_shaped", "category": "misc",
        "pattern": ["BBB", "BFB", "BBB"],
        "key": {"B": {"item": "minecraft:brick"}, "F": {"item": "minecraft:furnace"}},
        "result": {"item": f"{MOD}:alloy_furnace"}})

    # alliage : bronze = 3 cuivre + 1 etain -> 4 bronze
    write_json(os.path.join(rdir, "alloying", "bronze_ingot.json"), {
        "type": f"{MOD}:alloying",
        "ingredient_a": {"tag": "forge:ingots/copper"}, "count_a": 3,
        "ingredient_b": {"tag": "forge:ingots/tin"}, "count_b": 1,
        "result": {"item": f"{MOD}:bronze_ingot", "count": 4},
        "time": 200})


def self_drop(block):
    return {
        "type": "minecraft:block",
        "pools": [{
            "rolls": 1.0, "bonus_rolls": 0.0,
            "entries": [{"type": "minecraft:item", "name": f"{MOD}:{block}"}],
            "conditions": [{"condition": "minecraft:survives_explosion"}],
        }],
    }


def ore_drop(block, raw):
    return {
        "type": "minecraft:block",
        "pools": [{
            "rolls": 1.0, "bonus_rolls": 0.0,
            "entries": [{
                "type": "minecraft:alternatives",
                "children": [
                    {"type": "minecraft:item",
                     "conditions": [{"condition": "minecraft:match_tool", "predicate": {
                         "enchantments": [{"enchantment": "minecraft:silk_touch", "levels": {"min": 1}}]}}],
                     "name": f"{MOD}:{block}"},
                    {"type": "minecraft:item",
                     "functions": [
                         {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                          "formula": "minecraft:ore_drops"},
                         {"function": "minecraft:explosion_decay"}],
                     "name": f"{MOD}:{raw}"},
                ],
            }],
        }],
    }


def gen_loot_and_tags():
    ldir = os.path.join(DATA, "loot_tables", "blocks")
    for name, m in METALS.items():
        write_json(os.path.join(ldir, f"{name}_block.json"), self_drop(f"{name}_block"))
        if m["ore"]:
            write_json(os.path.join(ldir, f"{name}_ore.json"), ore_drop(f"{name}_ore", f"raw_{name}"))
    write_json(os.path.join(ldir, "alloy_furnace.json"), self_drop("alloy_furnace"))

    # tags de minage
    pick = [f"{MOD}:{b}" for b in all_block_ids()]
    write_json(os.path.join(ROOT, "data", "minecraft", "tags", "blocks", "mineable", "pickaxe.json"),
               {"replace": False, "values": pick})
    tiers = {"minecraft:needs_stone_tool": [], "minecraft:needs_iron_tool": [], "minecraft:needs_diamond_tool": []}
    for name, m in METALS.items():
        tiers[m["block_needs"]].append(f"{MOD}:{name}_block")
        if m["ore"]:
            tiers[m["needs"]].append(f"{MOD}:{name}_ore")
    for tag, values in tiers.items():
        ns, path = tag.split(":")
        write_json(os.path.join(ROOT, "data", ns, "tags", "blocks", f"{path}.json"),
                   {"replace": False, "values": values})
    write_json(os.path.join(DATA, "tags", "blocks", "needs_voidium_tool.json"),
               {"replace": False, "values": []})

    # tags Forge (compatibilite avec les autres mods)
    fdir = os.path.join(ROOT, "data", "forge", "tags")
    for name, m in METALS.items():
        write_json(os.path.join(fdir, "items", "ingots", f"{name}.json"),
                   {"replace": False, "values": [f"{MOD}:{name}_ingot"]})
        write_json(os.path.join(fdir, "items", "storage_blocks", f"{name}.json"),
                   {"replace": False, "values": [f"{MOD}:{name}_block"]})
        write_json(os.path.join(fdir, "blocks", "storage_blocks", f"{name}.json"),
                   {"replace": False, "values": [f"{MOD}:{name}_block"]})
        if m["raw"]:
            write_json(os.path.join(fdir, "items", "raw_materials", f"{name}.json"),
                       {"replace": False, "values": [f"{MOD}:raw_{name}"]})
            write_json(os.path.join(fdir, "items", "ores", f"{name}.json"),
                       {"replace": False, "values": [f"{MOD}:{name}_ore"]})
            write_json(os.path.join(fdir, "blocks", "ores", f"{name}.json"),
                       {"replace": False, "values": [f"{MOD}:{name}_ore"]})


def gen_worldgen():
    configs = {
        "tin": dict(size=9, count=14, lo=-16, hi=112, dim="#minecraft:is_overworld", target="overworld"),
        "ignatium": dict(size=7, count=10, lo=10, hi=110, dim="#minecraft:is_nether", target="nether"),
        "voidium": dict(size=5, count=6, lo=0, hi=80, dim="#minecraft:is_end", target="end"),
    }
    for name, c in configs.items():
        block = {"Name": f"{MOD}:{name}_ore"}
        if c["target"] == "overworld":
            targets = [
                {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"},
                 "state": block},
                {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"},
                 "state": block},
            ]
        elif c["target"] == "nether":
            targets = [{"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:base_stone_nether"},
                        "state": block}]
        else:
            targets = [{"target": {"predicate_type": "minecraft:block_match", "block": "minecraft:end_stone"},
                        "state": block}]
        write_json(os.path.join(DATA, "worldgen", "configured_feature", f"{name}_ore.json"), {
            "type": "minecraft:ore",
            "config": {"size": c["size"], "discard_chance_on_air_exposure": 0.0, "targets": targets}})
        write_json(os.path.join(DATA, "worldgen", "placed_feature", f"{name}_ore.json"), {
            "feature": f"{MOD}:{name}_ore",
            "placement": [
                {"type": "minecraft:count", "count": c["count"]},
                {"type": "minecraft:in_square"},
                {"type": "minecraft:height_range", "height": {
                    "type": "minecraft:uniform",
                    "min_inclusive": {"absolute": c["lo"]},
                    "max_inclusive": {"absolute": c["hi"]}}},
                {"type": "minecraft:biome"},
            ]})
        write_json(os.path.join(DATA, "forge", "biome_modifier", f"add_{name}_ore.json"), {
            "type": "forge:add_features",
            "biomes": c["dim"],
            "features": f"{MOD}:{name}_ore",
            "step": "underground_ores"})


if __name__ == "__main__":
    gen_textures()
    gen_models()
    gen_lang()
    gen_recipes()
    gen_loot_and_tags()
    gen_worldgen()
    print("Ressources generees dans", os.path.abspath(ROOT))
