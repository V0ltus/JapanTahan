import pyxel
import os
import subprocess
import sys
import math
import random
from PIL import Image

# ── Musique MP3 via pygame (optionnel) ──────────────────────
try:
    import pygame
    _PYGAME_OK = True
except ImportError:
    _PYGAME_OK = False

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===========================================================
#  CONSTANTES
# ===========================================================
W, H = 256, 256
FPS  = 30

C_BLACK  = 0
C_NAVY   = 1
C_PURPLE = 2
C_GREEN  = 3
C_BROWN  = 4
C_DGRAY  = 5
C_LGRAY  = 6
C_WHITE  = 7
C_RED    = 8
C_ORANGE = 9
C_YELLOW = 10
C_LGREEN = 11
C_LBLUE  = 12
C_PINK   = 13
C_PEACH  = 14
C_BGRAY  = 15

IMG_BG   = 0
IMG_LOGO = 1

# ===========================================================
#  PRÉPARATION ASSETS
# ===========================================================
def prepare_assets():
    os.makedirs("assets", exist_ok=True)
    src_bg = "assets/fond_depart.jpg"
    dst_bg = "assets/fond_depart_small.jpg"
    if not os.path.exists(dst_bg) and os.path.exists(src_bg):
        img = Image.open(src_bg).convert("RGB").resize((256, 256), Image.LANCZOS)
        img.save(dst_bg, quality=95)
    dst_logo = "assets/logo_menu.png"
    src_logo = "assets/logo.png"
    if not os.path.exists(dst_logo) and os.path.exists(src_logo):
        logo   = Image.open(src_logo).convert("RGB").resize((110, 110), Image.LANCZOS)
        canvas = Image.new("RGB", (256, 256), (0, 0, 0))
        canvas.paste(logo, (73, 0))
        canvas.save(dst_logo)

prepare_assets()

# ===========================================================
#  HIGHSCORES (lecture seule pour affichage)
# ===========================================================
def load_highscores():
    import json
    try:
        if os.path.exists("highscores.json"):
            with open("highscores.json") as f:
                return json.load(f)
    except Exception:
        pass
    return []

# ===========================================================
#  PÉTALE SAKURA (avancé : taille variable, rotation)
# ===========================================================
class Sakura:
    def __init__(self, x=None, y=None, fast=False):
        self.reset(x, y, fast)

    def reset(self, x=None, y=None, fast=False):
        self.x      = x if x is not None else random.randint(0, W)
        self.y      = y if y is not None else random.randint(-20, H)
        self.vx     = random.uniform(-0.5, 0.3)
        self.vy     = random.uniform(0.25, 0.85) * (1.6 if fast else 1.0)
        self.angle  = random.uniform(0, math.pi * 2)
        self.dangle = random.uniform(-0.07, 0.07)
        self.wobble = random.uniform(0, math.pi * 2)
        self.size   = random.choice([1, 1, 1, 2, 2])
        self.color  = random.choice([C_PINK, C_PINK, C_PEACH, C_WHITE, C_PINK])
        self.life   = random.randint(150, 450)
        self.alpha  = random.randint(60, 100)  # opacité simulée via life

    def update(self):
        self.wobble += 0.04
        self.x      += self.vx + math.sin(self.wobble) * 0.35
        self.y      += self.vy
        self.angle  += self.dangle
        self.life   -= 1
        if self.life <= 0 or self.y > H + 6:
            self.reset(x=random.randint(0, W), y=-6)

    def draw(self):
        ix, iy = int(self.x), int(self.y)
        if not (0 <= ix < W and -2 <= iy < H + 2):
            return
        if self.size >= 2:
            pyxel.circ(ix, iy, 1, self.color)
        else:
            pyxel.pset(ix, iy, self.color)

# ===========================================================
#  ÉTINCELLE (logo)
# ===========================================================
class Spark:
    def __init__(self, cx=128, cy=55):
        self.cx = cx
        self.cy = cy
        self.reset()

    def reset(self):
        angle    = random.uniform(0, math.pi * 2)
        speed    = random.uniform(0.4, 2.2)
        r        = random.randint(28, 58)
        self.x   = self.cx + math.cos(angle) * r
        self.y   = self.cy + math.sin(angle) * r
        self.vx  = math.cos(angle) * speed * 0.25 + random.uniform(-0.4, 0.4)
        self.vy  = -random.uniform(0.4, 1.8)
        self.life= random.randint(12, 32)
        self.color = random.choice([C_YELLOW, C_ORANGE, C_RED, C_WHITE, C_YELLOW])
        self.alive = True

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.07
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive and 0 <= self.x < W and 0 <= self.y < H:
            pyxel.pset(int(self.x), int(self.y), self.color)

# ===========================================================
#  PARTICULE D'EXPLOSION (lors du flash JOUER)
# ===========================================================
class BurstParticle:
    def __init__(self, x, y):
        angle  = random.uniform(0, math.pi * 2)
        speed  = random.uniform(1.0, 4.5)
        self.x  = x
        self.y  = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(10, 28)
        self.color = random.choice([C_RED, C_ORANGE, C_YELLOW, C_WHITE])
        self.alive = True

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.1
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive and 0 <= self.x < W and 0 <= self.y < H:
            pyxel.pset(int(self.x), int(self.y), self.color)

# ===========================================================
#  LANTERNE ANIMÉE
# ===========================================================
class Lantern:
    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.base_y= y
        self.timer = random.randint(0, 60)
        self.glow  = 0

    def update(self):
        self.timer += 1
        self.y      = self.base_y + math.sin(self.timer * 0.06) * 1.5
        self.glow   = (math.sin(self.timer * 0.1) + 1) / 2  # 0..1

    def draw(self):
        x, y = int(self.x), int(self.y)
        gc = C_YELLOW if self.glow > 0.5 else C_ORANGE
        # Corps lanterne
        pyxel.rect(x - 3, y,      6, 9,  C_RED)
        pyxel.rect(x - 2, y + 1,  4, 7,  C_ORANGE)
        # Lueur centrale
        pyxel.pset(x, y + 4, gc)
        pyxel.pset(x - 1, y + 4, gc)
        pyxel.pset(x + 1, y + 4, gc)
        # Toit
        pyxel.rect(x - 4, y - 2,  8, 3,  C_RED)
        pyxel.rect(x - 5, y - 3,  10, 2, C_NAVY)
        # Corde
        pyxel.pset(x, y - 4, C_BROWN)
        pyxel.pset(x, y - 5, C_BROWN)
        # Frange bas
        pyxel.rect(x - 3, y + 9,  6, 2,  C_RED)
        pyxel.pset(x - 3, y + 11, C_ORANGE)
        pyxel.pset(x,     y + 11, C_ORANGE)
        pyxel.pset(x + 2, y + 11, C_ORANGE)

# ===========================================================
#  NUAGE DE BRUME (bas de l'écran)
# ===========================================================
class MistCloud:
    def __init__(self, x=None):
        self.reset(x)

    def reset(self, x=None):
        self.x   = x if x is not None else random.randint(-40, W + 40)
        self.y   = random.randint(180, H - 20)
        self.vx  = random.uniform(0.08, 0.22)
        self.w   = random.randint(30, 70)
        self.h   = random.randint(6, 14)
        self.alpha = random.randint(1, 3)  # 1=très transparent
        self.life = random.randint(300, 800)

    def update(self):
        self.x   += self.vx
        self.life -= 1
        if self.x > W + 80 or self.life <= 0:
            self.reset(-60)

    def draw(self):
        ix, iy = int(self.x), int(self.y)
        # Dessin brume : lignes alternées
        for dy in range(0, self.h, 2):
            if (iy + dy) % 4 < 2:
                pyxel.rect(ix, iy + dy, self.w, 1, C_LGRAY)

# ===========================================================
#  TORII ANIMÉ (fond)
# ===========================================================
class ToriiBackground:
    """Grand torii pixel art en arrière-plan."""
    def __init__(self):
        self.timer = 0

    def update(self):
        self.timer += 1

    def draw(self, alpha_anim):
        t  = self.timer
        # Position centrée
        cx = W // 2
        base_y = 200

        # Piliers (légère ondulation)
        sway = int(math.sin(t * 0.015) * 0.5)
        # Pilier gauche
        pyxel.rect(cx - 55 + sway, 90,  6, 110, C_RED)
        # Pilier droit
        pyxel.rect(cx + 49 + sway, 90,  6, 110, C_RED)
        # Kasagi (barre haute courbée)
        pyxel.rect(cx - 62 + sway, 85, 124,  5, C_RED)
        pyxel.rect(cx - 58 + sway, 82, 116,  4, C_NAVY)
        # Nuki (barre basse)
        pyxel.rect(cx - 50 + sway, 105, 100, 4, C_RED)
        # Shimaki (anneau de renfort)
        for px_off in [-52, 46]:
            pyxel.rect(cx + px_off + sway, 112, 8, 5, C_ORANGE)
        # Glow ambiant quand pulsation
        if (t % 60) < 30:
            pyxel.pset(cx - 2 + sway, 83, C_ORANGE)
            pyxel.pset(cx + 2 + sway, 83, C_ORANGE)

# ===========================================================
#  TEXTE DÉFILANT (scroll de bas vers haut pour l'écran Records)
# ===========================================================
class ScrollText:
    def __init__(self, lines):
        self.lines = lines
        self.y     = H
        self.speed = 0.4

    def update(self):
        self.y -= self.speed
        total_h = len(self.lines) * 10
        if self.y < -total_h:
            self.y = H

    def draw(self):
        for i, (txt, c) in enumerate(self.lines):
            ty = int(self.y) + i * 10
            if -8 < ty < H:
                tx = (W - len(txt) * 4) // 2
                pyxel.text(tx, ty, txt, c)

# ===========================================================
#  ÉCRAN INSTRUCTIONS (amélioré)
# ===========================================================
class ScreenInstructions:
    def __init__(self):
        self.timer  = 0
        self.page   = 0  # 0 = Tours, 1 = Ennemis, 2 = Contrôles
        self.pages  = ["TOURS & STRATEGIE", "ENNEMIS", "CONTROLES & ULTS"]

    def update(self):
        self.timer += 1
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN):
            return "menu"
        if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
            self.page = (self.page + 1) % len(self.pages)
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
            self.page = (self.page - 1) % len(self.pages)
        return "instructions"

    def draw(self):
        pyxel.rect(8, 6, W - 16, H - 12, C_BLACK)
        pyxel.rectb(8, 6, W - 16, H - 12, C_RED)
        for cx, cy in [(8,6),(W-11,6),(8,H-9),(W-11,H-9)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW)

        # Titre page
        title = self.pages[self.page]
        pyxel.text((W - len(title) * 4) // 2, 12, title, C_YELLOW)
        pyxel.rect(18, 20, W - 36, 1, C_RED)

        if self.page == 0:
            self._draw_tours()
        elif self.page == 1:
            self._draw_ennemis()
        else:
            self._draw_controles()

        # Navigation pages
        pyxel.text(12, H - 18, "< A", C_DGRAY)
        pyxel.text(W - 20, H - 18, "D >", C_DGRAY)
        for i in range(len(self.pages)):
            c = C_YELLOW if i == self.page else C_DGRAY
            pyxel.rect(W//2 - len(self.pages)*4 + i*10, H - 12, 6, 3, c)
        pyxel.text(60, H - 9, "ECHAP/ENTREE = retour", C_DGRAY)

    def _draw_tours(self):
        tours = [
            ("1 Archer",    50,  "~55", "1/2/3",  "Polyvalent, longue portee", C_LGREEN),
            ("2 Katana",    80,  "~35", "2/4/7",  "Rapide, BRULE les ennemis",  C_RED),
            ("3 Tamiko",    120, "~80", "3/6/10", "Longue portee, RALENTIT",    C_PINK),
            ("4 Ninja",     100, "~50", "2/3/5",  "AoE splash + EMPOISONNE",    C_NAVY),
            ("5 Oni Canon", 200, "~95", "8/14/22","Lourd, PERCE les ennemis",   C_BGRAY),
        ]
        y = 26
        for name, cost, rng, dmg, desc, c in tours:
            pyxel.text(14, y, name, c)
            pyxel.text(90, y, f"{cost}or", C_YELLOW)
            pyxel.text(130, y, f"p:{rng}", C_LGRAY)
            pyxel.text(165, y, f"d:{dmg}", C_WHITE)
            y += 8
            pyxel.text(18, y, desc, C_LGRAY)
            y += 11
        pyxel.text(14, y + 2, "U=upgrade  V=vendre (50% val.)", C_ORANGE)

    def _draw_ennemis(self):
        ennemis = [
            ("Grunt",    "4",  "norm",  "10",  C_RED,     "Standard"),
            ("Rapide",   "3",  "rapide","15",  C_YELLOW,  "Ignore ralentissement"),
            ("Tank",     "18", "lent",  "35",  C_LGRAY,   "Immunise slow"),
            ("BOSS",     "70", "lent",  "120", C_PURPLE,  "Enorme dommages base"),
            ("Kamikaze", "5",  "moyen", "20",  C_ORANGE,  "EXPLOSE a la mort!"),
            ("Aerien",   "6",  "rapide","25",  C_LBLUE,   "Seuls Tamiko+Oni touchent"),
        ]
        y = 26
        pyxel.text(14, y, "Nom", C_ORANGE)
        pyxel.text(72, y, "HP", C_ORANGE)
        pyxel.text(98, y, "Vit.", C_ORANGE)
        pyxel.text(130, y, "Or", C_ORANGE)
        pyxel.text(156, y, "Note", C_ORANGE)
        y += 8
        pyxel.rect(14, y, W - 28, 1, C_DGRAY)
        y += 4
        for name, hp, spd, rwd, c, note in ennemis:
            pyxel.text(14, y, name, c)
            pyxel.text(72, y, hp, C_WHITE)
            pyxel.text(98, y, spd, C_WHITE)
            pyxel.text(130, y, rwd, C_YELLOW)
            pyxel.text(156, y, note, C_LGRAY)
            y += 10

    def _draw_controles(self):
        lines = [
            ("PLACEMENT",        C_ORANGE),
            ("Clic G = poser tour selectionnee",     C_WHITE),
            ("Clic G/tour = selectionner",           C_WHITE),
            ("Clic D = deselectionner",              C_LGRAY),
            ("",                 C_BLACK),
            ("GESTION TOURS",    C_ORANGE),
            ("U = Ameliorer  V = Vendre",            C_YELLOW),
            ("",                 C_BLACK),
            ("ULTIMES (recharge auto)",  C_ORANGE),
            ("Q = Samurai Fury  (30s)",  C_RED),
            ("   -8 HP a tous les ennemis",          C_LGRAY),
            ("W = Blizzard      (40s)",  C_LBLUE),
            ("   Ralentit tout 6 secondes",          C_LGRAY),
            ("E = Pluie fleches (35s)",  C_LGREEN),
            ("   12 impacts aleatoires",             C_LGRAY),
            ("",                 C_BLACK),
            ("P = Pause   M = Musique",              C_LGRAY),
            ("Shop = auto apres chaque vague",       C_YELLOW),
        ]
        y = 26
        for txt, c in lines:
            if y > H - 22:
                break
            pyxel.text(14, y, txt, c)
            y += 9

# ===========================================================
#  ÉCRAN CRÉDITS (amélioré)
# ===========================================================
class ScreenCredits:
    def __init__(self):
        self.timer  = 0
        self.scroll = ScrollText([
            ("", C_BLACK),
            ("--- JAPANTAHAN ---", C_YELLOW),
            ("Tower Defense Japonais", C_ORANGE),
            ("", C_BLACK),
            ("Code & Game Design", C_WHITE),
            ("Equipe JapanTahan", C_LGREEN),
            ("", C_BLACK),
            ("Graphismes", C_WHITE),
            ("Assets IA + Pixel Art", C_LGREEN),
            ("", C_BLACK),
            ("Musique", C_WHITE),
            ("Shattered Shogun.mp3", C_LBLUE),
            ("", C_BLACK),
            ("Moteur", C_WHITE),
            ("Pyxel v2.x — Takashi Kitao", C_LBLUE),
            ("", C_BLACK),
            ("5 tours uniques", C_ORANGE),
            ("6 types d ennemis", C_ORANGE),
            ("3 ultimes devastateurs", C_ORANGE),
            ("Shop inter-vague", C_ORANGE),
            ("9 achievements", C_ORANGE),
            ("Mode survie infini", C_ORANGE),
            ("", C_BLACK),
            ("Merci d avoir joue !", C_YELLOW),
            ("Protegez le Japon !", C_RED),
            ("", C_BLACK),
            ("", C_BLACK),
        ])

    def update(self):
        self.timer += 1
        self.scroll.update()
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN) \
                or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return "menu"
        return "credits"

    def draw(self):
        # Fond semi-transparent
        pyxel.rect(15, 15, W - 30, H - 30, C_BLACK)
        pyxel.rectb(15, 15, W - 30, H - 30, C_RED)
        for cx, cy in [(15,15),(W-18,15),(15,H-18),(W-18,H-18)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW)

        t = self.timer
        pyxel.text(76, 20, "CREDITS", C_YELLOW)
        pyxel.rect(22, 28, W - 44, 1, C_RED)

        # Zone scroll clippée
        for line_i, (txt, c) in enumerate(self.scroll.lines):
            ty = int(self.scroll.y) + line_i * 10
            if 30 <= ty <= H - 26:
                tx = (W - len(txt) * 4) // 2
                pyxel.text(tx, ty, txt, c)

        # Torii animé bas
        rx = W // 2
        ry = H - 28
        pyxel.rect(rx - 18, ry,     36, 3,  C_RED)
        pyxel.rect(rx - 14, ry + 3, 28, 2,  C_RED)
        pyxel.rect(rx - 16, ry + 5,  3, 10, C_RED)
        pyxel.rect(rx + 13, ry + 5,  3, 10, C_RED)
        # Glow clignotant
        gc = C_YELLOW if (t % 20 < 10) else C_ORANGE
        pyxel.pset(rx - 1, ry - 1, gc)
        pyxel.pset(rx + 1, ry - 1, gc)

        pyxel.text(55, H - 12, "ECHAP/ENTREE = retour", C_DGRAY)

# ===========================================================
#  ÉCRAN RECORDS
# ===========================================================
class ScreenRecords:
    def __init__(self):
        self.scores = load_highscores()
        self.timer  = 0

    def update(self):
        self.timer += 1
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN):
            return "menu"
        return "records"

    def draw(self):
        pyxel.rect(20, 20, W - 40, H - 40, C_BLACK)
        pyxel.rectb(20, 20, W - 40, H - 40, C_RED)
        for cx, cy in [(20,20),(W-23,20),(20,H-23),(W-23,H-23)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW)

        t = self.timer
        pyxel.text(78, 26, "MEILLEURS SCORES", C_YELLOW)
        pyxel.rect(28, 34, W - 56, 1, C_RED)

        medals = ["1.", "2.", "3.", "4.", "5."]
        medal_colors = [C_YELLOW, C_LGRAY, C_BROWN, C_LGRAY, C_LGRAY]

        if not self.scores:
            pyxel.text(70, 100, "Aucun score!", C_DGRAY)
            pyxel.text(50, 114, "Lancez une partie pour jouer", C_DGRAY)
        else:
            y = 42
            for i, hs in enumerate(self.scores[:5]):
                if i >= len(medals):
                    break
                mc = medal_colors[i]
                # Surbrillance 1er
                if i == 0:
                    pyxel.rect(26, y - 1, W - 52, 12, C_NAVY)
                    pyxel.rectb(26, y - 1, W - 52, 12, C_YELLOW)
                pyxel.text(28, y + 2, medals[i], mc)
                # Score
                pyxel.text(48, y + 2, f"{hs['score']:>7}", mc)
                # Vague
                pyxel.text(108, y + 2, f"vague {hs['wave']}", C_LGRAY)
                # Barre de score visuelle
                max_score = max(s['score'] for s in self.scores) if self.scores else 1
                bar_w = int((hs['score'] / max_score) * 70)
                pyxel.rect(155, y + 4, bar_w, 3, mc)
                y += 16

        # Animation torii
        rx = W // 2
        ry = H - 30
        gc = C_YELLOW if (t % 30 < 15) else C_ORANGE
        pyxel.rect(rx - 20, ry,     40, 3, C_RED)
        pyxel.rect(rx - 16, ry + 3, 32, 2, C_RED)
        pyxel.rect(rx - 18, ry + 5,  3, 8, C_RED)
        pyxel.rect(rx + 15, ry + 5,  3, 8, C_RED)
        pyxel.pset(rx, ry - 1, gc)

        pyxel.text(55, H - 16, "ECHAP/ENTREE = retour", C_DGRAY)

# ===========================================================
#  ÉCRAN SELECTION DIFFICULTÉ
# ===========================================================
class ScreenDifficulty:
    DIFFS = [
        {
            "label":    "FACILE",
            "color":    C_LGREEN,
            "desc1":    "HP x1.5  Vitesse x0.75",
            "desc2":    "Pour decouvrir le jeu",
            "mod_hp":   1.5,
            "mod_spd":  0.75,
            "flag":     "easy",
        },
        {
            "label":    "NORMAL",
            "color":    C_YELLOW,
            "desc1":    "Stats de base",
            "desc2":    "L experience complete",
            "mod_hp":   1.0,
            "mod_spd":  1.0,
            "flag":     "normal",
        },
        {
            "label":    "DIFFICILE",
            "color":    C_RED,
            "desc1":    "HP x0.7  Vitesse x1.4",
            "desc2":    "Pour les veterans",
            "mod_hp":   0.7,
            "mod_spd":  1.4,
            "flag":     "hard",
        },
        {
            "label":    "SURVIE ∞",
            "color":    C_PURPLE,
            "desc1":    "Vagues infinies procedurales",
            "desc2":    "Jusqu a votre mort!",
            "mod_hp":   1.0,
            "mod_spd":  1.0,
            "flag":     "survive",
        },
    ]

    def __init__(self):
        self.selected = 1  # Normal par défaut
        self.timer    = 0
        self.confirm_flash = 0

    def update(self):
        self.timer += 1
        if self.confirm_flash > 0:
            self.confirm_flash -= 1
            if self.confirm_flash == 0:
                return ("launch", self.DIFFS[self.selected]["flag"])

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            return "menu"
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.DIFFS)
        if pyxel.btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.DIFFS)
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # Vérifier clic souris sur bouton
            mx, my = pyxel.mouse_x, pyxel.mouse_y
            for i in range(len(self.DIFFS)):
                bx, by, bw, bh = self._btn_rect(i)
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    self.selected = i
                if pyxel.btnp(pyxel.KEY_RETURN):
                    pass
            self.confirm_flash = 20
        return "difficulty"

    def _btn_rect(self, i):
        bw, bh = 200, 34
        bx = (W - bw) // 2
        by = 44 + i * 44
        return bx, by, bw, bh

    def draw(self):
        pyxel.rect(10, 10, W - 20, H - 20, C_BLACK)
        pyxel.rectb(10, 10, W - 20, H - 20, C_RED)
        for cx, cy in [(10,10),(W-13,10),(10,H-13),(W-13,H-13)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW)

        t = self.timer
        pyxel.text(68, 16, "CHOISIR DIFFICULTE", C_YELLOW)
        pyxel.rect(18, 24, W - 36, 1, C_RED)
        pyxel.text(50, 28, "HAUT/BAS + ENTREE", C_DGRAY)

        for i, d in enumerate(self.DIFFS):
            bx, by, bw, bh = self._btn_rect(i)
            sel = (i == self.selected)
            # Fond
            if sel:
                pyxel.rect(bx, by, bw, bh, C_NAVY)
                pyxel.rectb(bx, by, bw, bh, d["color"])
                # Coins dorés
                for cx, cy in [(bx,by),(bx+bw-3,by),(bx,by+bh-3),(bx+bw-3,by+bh-3)]:
                    pyxel.rect(cx, cy, 3, 3, C_YELLOW)
            else:
                pyxel.rect(bx, by, bw, bh, C_BLACK)
                pyxel.rectb(bx, by, bw, bh, C_DGRAY)

            # Label
            lx = bx + (bw - len(d["label"]) * 4) // 2
            pyxel.text(lx, by + 5, d["label"], d["color"] if sel else C_LGRAY)
            # Desc
            dx = bx + (bw - len(d["desc1"]) * 4) // 2
            pyxel.text(dx, by + 14, d["desc1"], C_WHITE if sel else C_DGRAY)
            dx2 = bx + (bw - len(d["desc2"]) * 4) // 2
            pyxel.text(dx2, by + 23, d["desc2"], C_LGRAY if sel else C_DGRAY)

            # Curseur katana
            if sel:
                kx = bx - 14
                ky = by + bh // 2
                blink = (t // 8) % 2
                pyxel.rect(kx, ky - 1, 8, 3, C_LGRAY)
                pyxel.rect(kx + 7, ky - 1, 2, 3, C_YELLOW)
                pyxel.rect(kx + 9, ky, 3, 1, C_BROWN)
                if blink:
                    pyxel.pset(kx, ky, C_WHITE)

        # Flash confirmation
        if self.confirm_flash > 0:
            c = C_YELLOW if (self.confirm_flash % 4 < 2) else C_RED
            pyxel.rectb(10, 10, W - 20, H - 20, c)
            txt = "LANCEMENT!"
            pyxel.text((W - len(txt) * 4) // 2, H // 2 - 4, txt, C_WHITE)

        pyxel.text(55, H - 18, "ECHAP = retour menu", C_DGRAY)

# ===========================================================
#  MENU PRINCIPAL
# ===========================================================
class Menu:
    STATE_MENU        = "menu"
    STATE_INSTRUCTIONS= "instructions"
    STATE_CREDITS     = "credits"
    STATE_RECORDS     = "records"
    STATE_DIFFICULTY  = "difficulty"
    STATE_LAUNCH      = "launch"

    BUTTONS = ["JOUER", "INSTRUCTIONS", "RECORDS", "CREDITS", "QUITTER"]

    def __init__(self):
        pyxel.init(W, H, title="JapanTahan", fps=FPS)
        pyxel.mouse(True)

        # Chargement images
        if os.path.exists("assets/fond_depart_small.jpg"):
            pyxel.images[IMG_BG].load(0, 0, "assets/fond_depart_small.jpg")
        logo_path = "assets/logo_menu.png"
        if os.path.exists(logo_path):
            pyxel.images[IMG_LOGO].load(0, 0, logo_path)
            self.has_logo = True
        else:
            self.has_logo = False

        # Musique
        self.mp3_active = False
        self._init_music()
        self.music_on = True

        # État
        self.state    = self.STATE_MENU
        self.selected = 0
        self.timer    = 0

        # Sous-écrans
        self.screen_instructions = ScreenInstructions()
        self.screen_credits      = ScreenCredits()
        self.screen_records      = ScreenRecords()
        self.screen_difficulty   = ScreenDifficulty()

        # Particules
        self.sakuras    = [Sakura() for _ in range(35)]
        self.sparks     = []
        self.spark_timer= 0
        self.bursts     = []
        self.mists      = [MistCloud() for _ in range(6)]
        self.lanterns   = [
            Lantern(18, 148),
            Lantern(W - 22, 148),
            Lantern(14, 172),
            Lantern(W - 18, 172),
        ]

        # Fond torii
        self.torii_bg = ToriiBackground()

        # Animation logo
        self.logo_y      = -130
        self.logo_target = 2
        self.intro_done  = False
        self.logo_scale  = 0.0

        # Flash JOUER
        self.play_flash  = 0
        self.blink_timer = 0

        # Défilement titre vertical (idle)
        self.idle_timer = 0

        # Étoiles de fond
        self.stars = [
            (random.randint(0, W), random.randint(0, 120),
             random.choice([C_WHITE, C_LGRAY, C_PEACH]))
            for _ in range(18)
        ]
        self.star_timer = 0

        # Onde de lumière (effet au clic)
        self.wave_rings = []  # liste de (x, y, r, life)

        pyxel.run(self.update, self.draw)

    # ── Musique ───────────────────────────────────────────
    def _init_music(self):
        if _PYGAME_OK:
            try:
                pygame.mixer.init()
                mp3 = "assets/Shattered Shogun.mp3"
                if os.path.exists(mp3):
                    pygame.mixer.music.load(mp3)
                    pygame.mixer.music.set_volume(0.45)
                    pygame.mixer.music.play(-1)
                    self.mp3_active = True
                    return
            except Exception:
                pass
        self._setup_pyxel_music()

    def _setup_pyxel_music(self):
        pyxel.sound(0).set(
            "e3 r g3 r a3 r g3 e3 d3 r e3 r g3 r e3 r",
            "t", "55556666 55556666", "nnnnnnnn nnnnnnnn", 20)
        pyxel.sound(1).set(
            "a2 r r r e2 r r r g2 r r r d2 r r r",
            "s", "3333 3333 3333 3333", "nnnn nnnn nnnn nnnn", 20)
        pyxel.sound(2).set(
            "a1 r r a1 r r a1 r a1 r a1 r r a1 r r",
            "n", "7777 7777 7777 7777", "nnnn nnnn nnnn nnnn", 20)
        pyxel.sound(3).set(
            "e4 r r a4 r r g4 r r e4 r r",
            "p", "4444 4444", "nnnn nnnn", 25)
        pyxel.music(0).set([0], [1], [2], [3])
        pyxel.playm(0, loop=True)

    def _toggle_music(self):
        self.music_on = not self.music_on
        if self.mp3_active and _PYGAME_OK:
            if self.music_on:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()
        else:
            if self.music_on:
                pyxel.playm(0, loop=True)
            else:
                pyxel.stop()

    # ── Boutons ───────────────────────────────────────────
    def _button_rect(self, i):
        bw, bh = 150, 20
        bx = (W - bw) // 2
        by = 158 + i * 26
        return bx, by, bw, bh

    def _hovered(self, i):
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        bx, by, bw, bh = self._button_rect(i)
        return bx <= mx <= bx + bw and by <= my <= by + bh

    # ── Update ────────────────────────────────────────────
    def update(self):
        self.timer += 1
        self.idle_timer += 1
        mx, my = pyxel.mouse_x, pyxel.mouse_y

        # ── Sous-écrans ───────────────────────────────────
        if self.state == self.STATE_INSTRUCTIONS:
            r = self.screen_instructions.update()
            if r == "menu":
                self.state = self.STATE_MENU
            return

        if self.state == self.STATE_CREDITS:
            r = self.screen_credits.update()
            if r == "menu":
                self.state = self.STATE_MENU
            return

        if self.state == self.STATE_RECORDS:
            r = self.screen_records.update()
            if r == "menu":
                self.state = self.STATE_MENU
            return

        if self.state == self.STATE_DIFFICULTY:
            r = self.screen_difficulty.update()
            if r == "menu":
                self.state = self.STATE_MENU
                return
            if isinstance(r, tuple) and r[0] == "launch":
                self._launch_game(r[1])
            return

        # ── Animation intro ───────────────────────────────
        if not self.intro_done:
            self.logo_y     = self.logo_y + (self.logo_target - self.logo_y) * 0.1
            self.logo_scale = min(1.0, self.logo_scale + 0.035)
            if abs(self.logo_y - self.logo_target) < 0.5 and self.logo_scale >= 0.99:
                self.intro_done = True

        # ── Sakura ────────────────────────────────────────
        for s in self.sakuras:
            s.update()

        # ── Brume ─────────────────────────────────────────
        for m in self.mists:
            m.update()

        # ── Lanternes ─────────────────────────────────────
        for l in self.lanterns:
            l.update()

        # ── Torii bg ──────────────────────────────────────
        self.torii_bg.update()

        # ── Étoiles (clignotement) ────────────────────────
        self.star_timer += 1

        # ── Étincelles logo ───────────────────────────────
        self.spark_timer += 1
        if self.spark_timer % 3 == 0:
            lx = 73 + 55  # centre logo
            ly = int(self.logo_y) + 55
            self.sparks.append(Spark(lx, ly))
        self.sparks = [sp for sp in self.sparks if sp.alive]
        for sp in self.sparks:
            sp.update()

        # ── Bursts (explosion clic) ───────────────────────
        for b in self.bursts:
            b.update()
        self.bursts = [b for b in self.bursts if b.alive]

        # ── Ondes de lumière ──────────────────────────────
        self.wave_rings = [(x, y, r + 1.5, life - 1)
                           for x, y, r, life in self.wave_rings if life > 0]

        # ── Clignotement ──────────────────────────────────
        self.blink_timer = (self.blink_timer + 1) % 50

        # ── Flash JOUER ───────────────────────────────────
        if self.play_flash > 0:
            self.play_flash -= 1
            # Burst de particules pendant flash
            if self.play_flash % 4 == 0:
                for _ in range(8):
                    self.bursts.append(BurstParticle(
                        random.randint(20, W - 20),
                        random.randint(H // 2 - 20, H // 2 + 20)))
            return

        # ── Navigation clavier ────────────────────────────
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.BUTTONS)
        if pyxel.btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.BUTTONS)
        if pyxel.btnp(pyxel.KEY_RETURN):
            self._choose(self.selected)
        if pyxel.btnp(pyxel.KEY_M):
            self._toggle_music()

        # ── Hover & clic souris ───────────────────────────
        for i in range(len(self.BUTTONS)):
            if self._hovered(i):
                self.selected = i
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # Onde de clic
            self.wave_rings.append((mx, my, 2, 20))
            for i in range(len(self.BUTTONS)):
                if self._hovered(i):
                    self._choose(i)

    def _choose(self, i):
        label = self.BUTTONS[i]
        if label == "JOUER":
            self.state = self.STATE_DIFFICULTY
        elif label == "INSTRUCTIONS":
            self.state = self.STATE_INSTRUCTIONS
        elif label == "RECORDS":
            self.screen_records = ScreenRecords()  # refresh scores
            self.state = self.STATE_RECORDS
        elif label == "CREDITS":
            self.state = self.STATE_CREDITS
        elif label == "QUITTER":
            if _PYGAME_OK and self.mp3_active:
                pygame.mixer.music.stop()
            pyxel.quit()

    def _launch_game(self, mode="normal"):
        if _PYGAME_OK and self.mp3_active:
            pygame.mixer.music.stop()
        else:
            pyxel.stop()

        args = [sys.executable, "jeux.py"]
        if mode == "survive":
            args.append("--survive")
        elif mode == "easy":
            args.append("--easy")
        elif mode == "hard":
            args.append("--hard")
        subprocess.Popen(args)
        pyxel.quit()

    # ── DRAW ──────────────────────────────────────────────
    def draw(self):
        pyxel.cls(C_BLACK)
        t = self.timer

        # Fond
        if os.path.exists("assets/fond_depart_small.jpg"):
            pyxel.blt(0, 0, IMG_BG, 0, 0, W, H)

        # Torii de fond (derrière tout)
        self.torii_bg.draw(t)

        # Overlay dégradé bas
        self._draw_overlay()

        # Brume
        for m in self.mists:
            m.draw()

        # Sakura
        for s in self.sakuras:
            s.draw()

        # Sous-écrans
        if self.state == self.STATE_INSTRUCTIONS:
            self.screen_instructions.draw()
            return
        if self.state == self.STATE_CREDITS:
            self.screen_credits.draw()
            return
        if self.state == self.STATE_RECORDS:
            self.screen_records.draw()
            return
        if self.state == self.STATE_DIFFICULTY:
            self.screen_difficulty.draw()
            return

        # Étoiles (clignotantes)
        for i, (sx, sy, sc) in enumerate(self.stars):
            phase = (t + i * 7) % 40
            if phase < 32:
                pyxel.pset(sx, sy, sc)

        # Ondes de lumière (clic)
        for (rx, ry, rr, _) in self.wave_rings:
            ir = int(rr)
            if ir > 0:
                pyxel.circb(rx, ry, ir, C_YELLOW)

        # Logo animé
        self._draw_logo()

        # Étincelles
        for sp in self.sparks:
            sp.draw()

        # Lanternes
        for l in self.lanterns:
            l.draw()

        # Décoration torii (foreground)
        self._draw_torii_deco()

        # Boutons
        for i, label in enumerate(self.BUTTONS):
            self._draw_button(i, label)

        # Burst particles
        for b in self.bursts:
            b.draw()

        # Footer
        music_txt = f"M:MUS {'ON' if self.music_on else 'OFF'}"
        pyxel.text(3, H - 8, "v2.0", C_DGRAY)
        pyxel.text(W - len(music_txt) * 4 - 3, H - 8,
                   music_txt, C_LGREEN if self.music_on else C_DGRAY)

        # Indicateur highscore
        hs = load_highscores()
        if hs:
            pyxel.text(W//2 - 26, H - 8, f"TOP:{hs[0]['score']}", C_YELLOW)

        # Flash JOUER
        if self.play_flash > 0:
            c = C_YELLOW if (self.play_flash % 6 < 3) else C_RED
            pyxel.rectb(0, 0, W, H, c)
            pyxel.rectb(1, 1, W - 2, H - 2, c)
            txt = "CHARGEMENT..."
            pyxel.text((W - len(txt) * 4) // 2, H // 2, txt, C_WHITE)

    # ── Overlay sombre bas ─────────────────────────────────
    def _draw_overlay(self):
        for y in range(140, H):
            if (y // 2) % 2 == 0:
                pyxel.rect(0, y, W, 1, C_BLACK)
        # Bande complète tout en bas
        pyxel.rect(0, H - 12, W, 12, C_BLACK)

    # ── Logo animé ─────────────────────────────────────────
    def _draw_logo(self):
        if not self.has_logo:
            self._draw_text_logo()
            return

        t     = self.timer
        pulse = int(math.sin(t * 0.07) * 2.5)
        lx    = 73
        ly    = int(self.logo_y)
        lw, lh= 110, 110

        c_border = C_RED if (t % 30 < 15) else C_ORANGE
        c_outer  = C_YELLOW if (t % 20 < 10) else C_BROWN

        # Ombre
        pyxel.rectb(lx + 3, ly + 3, lw, lh, C_BLACK)
        # Fond
        pyxel.rect(lx - 3, ly - 3, lw + 6, lh + 6, C_BLACK)
        # Logo
        pyxel.blt(lx, ly, IMG_LOGO, lx, ly, lw, lh)
        # Cadre intérieur
        pyxel.rectb(lx - 2 - pulse, ly - 2 - pulse,
                    lw + 4 + pulse*2, lh + 4 + pulse*2, c_border)
        # Cadre extérieur
        pyxel.rectb(lx - 5 - pulse, ly - 5 - pulse,
                    lw + 10 + pulse*2, lh + 10 + pulse*2, c_outer)
        # Coins dorés (grands)
        sz = 6
        for cx, cy in [
            (lx - 5, ly - 5),
            (lx + lw - sz + 3, ly - 5),
            (lx - 5, ly + lh - sz + 3),
            (lx + lw - sz + 3, ly + lh - sz + 3),
        ]:
            pyxel.rect(cx, cy, sz, sz, C_YELLOW)
            pyxel.pset(cx + 2, cy + 2, C_WHITE)  # reflet

    def _draw_text_logo(self):
        t    = self.timer
        glow = C_RED if (t % 20 < 10) else C_ORANGE
        ly   = int(self.logo_y)
        for dx, dy, c in [(1, 1, C_BLACK), (0, 0, C_WHITE)]:
            pyxel.text(W//2 - 20 + dx, ly + 30 + dy, "JAPAN", c)
        for dx, dy, c in [(1, 1, C_BLACK), (0, 0, glow)]:
            pyxel.text(W//2 - 20 + dx, ly + 42 + dy, "TAHAN", c)

    # ── Décoration torii foreground ────────────────────────
    def _draw_torii_deco(self):
        t  = self.timer
        y  = 148
        cx = W // 2
        # Barre principale (légère oscillation)
        pyxel.rect(cx - 52, y,     104, 3, C_RED)
        pyxel.rect(cx - 43, y + 4,  86, 2, C_RED)
        # Piliers
        pyxel.rect(cx - 48, y + 6,   3, 10, C_RED)
        pyxel.rect(cx + 45, y + 6,   3, 10, C_RED)
        # Shine clignotant
        if (t % 40) < 20:
            pyxel.pset(cx - 50, y, C_ORANGE)
            pyxel.pset(cx + 50, y, C_ORANGE)

    # ── Bouton avancé ──────────────────────────────────────
    def _draw_button(self, i, label):
        bx, by, bw, bh = self._button_rect(i)
        hovered  = self._hovered(i)
        selected = (i == self.selected)
        t        = self.timer

        # Ombre
        pyxel.rect(bx + 2, by + 2, bw, bh, C_BLACK)

        # Fond animé si sélectionné
        if selected:
            # Dégradé simulé par bandes alternées
            for dy in range(bh):
                c = C_RED if (dy % 4 < 2) else C_NAVY
                pyxel.rect(bx, by + dy, bw, 1, c)
            border_c = C_YELLOW
            text_c   = C_WHITE
        elif hovered:
            pyxel.rect(bx, by, bw, bh, C_DGRAY)
            border_c = C_ORANGE
            text_c   = C_YELLOW
        else:
            pyxel.rect(bx, by, bw, bh, C_BLACK)
            border_c = C_LGRAY
            text_c   = C_LGRAY

        # Bordure
        pyxel.rectb(bx, by, bw, bh, border_c)

        # Coins dorés
        for cx, cy in [(bx, by), (bx + bw - 3, by),
                       (bx, by + bh - 3), (bx + bw - 3, by + bh - 3)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW if selected else border_c)

        # Texte centré
        tx = bx + (bw - len(label) * 4) // 2
        ty = by + (bh - 5) // 2
        # Ombre texte
        pyxel.text(tx + 1, ty + 1, label, C_BLACK)
        pyxel.text(tx, ty, label, text_c)

        # Curseur katana animé
        if selected:
            kx   = bx - 14
            ky   = by + bh // 2
            blink= (t // 8) % 2
            pyxel.rect(kx,     ky - 1, 9, 3, C_LGRAY)
            pyxel.rect(kx + 8, ky - 1, 2, 3, C_YELLOW)
            pyxel.rect(kx + 10, ky,    3, 1, C_BROWN)
            if blink:
                pyxel.pset(kx, ky, C_WHITE)
            # Flèche droite miroir
            pyxel.rect(bx + bw + 5, ky - 1, 9, 3, C_LGRAY)
            pyxel.rect(bx + bw + 4, ky - 1, 2, 3, C_YELLOW)
            pyxel.rect(bx + bw + 2, ky,     3, 1, C_BROWN)
            if blink:
                pyxel.pset(bx + bw + 13, ky, C_WHITE)

# ===========================================================
#  POINT D'ENTRÉE
# ===========================================================
Menu()
