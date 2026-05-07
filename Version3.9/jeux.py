import pyxel
import os
import math
import random
import json

# ── Musique MP3 via pygame.mixer (optionnel) ──────────────
try:
    import pygame
    _PYGAME_OK = True
except ImportError:
    _PYGAME_OK = False

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===========================================================
#  CONSTANTES GLOBALES
# ===========================================================
W, H          = 256, 256
FPS           = 30
STARTING_HP   = 25
STARTING_GOLD = 175
HIGHSCORE_FILE = "highscores.json"

# Chemin ennemi principal (waypoints pixel)
PATH_MAIN = [
    (45,  25),
    (45,  70),
    (127, 70),
    (127, 120),
    (190, 120),
    (190, 195),
    (210, 195),
    (210, 256),
]

# ── Palettes couleurs pyxel ───────────────────────────────
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

# ===========================================================
#  HIGHSCORES
# ===========================================================
def load_highscores():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_highscore(score, wave):
    scores = load_highscores()
    scores.append({"score": score, "wave": wave})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:5]
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump(scores, f)
    except Exception:
        pass
    return scores

# ===========================================================
#  SUCCÈS (ACHIEVEMENTS)
# ===========================================================
ACHIEVEMENTS = {
    "first_blood":   {"label": "Premier Sang",    "desc": "Tuer 1 ennemi",           "icon": "★", "unlocked": False},
    "centurion":     {"label": "Centurion",        "desc": "Tuer 100 ennemis",         "icon": "⚔", "unlocked": False},
    "gold_hoarder":  {"label": "Avare",            "desc": "Avoir 500 or simultané",   "icon": "◆", "unlocked": False},
    "max_tower":     {"label": "Maître Bâtisseur", "desc": "Upg. une tour niveau 3",   "icon": "▲", "unlocked": False},
    "no_damage":     {"label": "Fantôme",          "desc": "Terminer une vague sans perdre HP", "icon": "◎", "unlocked": False},
    "boss_slayer":   {"label": "Tueur de Boss",    "desc": "Tuer un Boss",             "icon": "☠", "unlocked": False},
    "fury_master":   {"label": "Fureur Samouraï",  "desc": "Utiliser Fury 5 fois",     "icon": "✦", "unlocked": False},
    "survivor_10":   {"label": "Survivant",        "desc": "Atteindre la vague 10",    "icon": "⬟", "unlocked": False},
    "speedrun":      {"label": "Éclair",           "desc": "Finir vague 1 en <30s",    "icon": "⚡", "unlocked": False},
}

# ===========================================================
#  DÉFINITIONS DES TOURS (5 tours)
# ===========================================================
TOWER_DEFS = {
    "archer": {
        "label":        "Archer",
        "cost":         [50, 75, 100],
        "range":        [55, 70, 90],
        "cooldown":     [26, 20, 14],
        "damage":       [1,  2,  3],
        "bullet_speed": [2.5, 3.0, 3.8],
        "colors":       [C_LGREEN, C_GREEN, C_DGRAY],
        "shape":        "circle",
        "special":      None,
        "desc":         "Polyvalent, longue portee",
    },
    "katana": {
        "label":        "Katana",
        "cost":         [80, 110, 150],
        "range":        [32, 44, 58],
        "cooldown":     [10, 7,  4],
        "damage":       [2,  4,  7],
        "bullet_speed": [4.5, 5.5, 7.0],
        "colors":       [C_RED, C_ORANGE, C_YELLOW],
        "shape":        "square",
        "special":      "burn",   # applique feu
        "desc":         "Rapide, courte portee, brule",
    },
    "tamiko": {
        "label":        "Tamiko",
        "cost":         [120, 160, 200],
        "range":        [80, 95, 115],
        "cooldown":     [38, 30, 22],
        "damage":       [3,  6,  10],
        "bullet_speed": [2.0, 2.5, 3.0],
        "colors":       [C_PURPLE, C_PINK, C_WHITE],
        "shape":        "diamond",
        "special":      "slow",   # applique ralentissement
        "desc":         "Grande portee, ralentit",
    },
    "ninja": {
        "label":        "Ninja",
        "cost":         [100, 140, 180],
        "range":        [50, 65, 80],
        "cooldown":     [18, 13, 9],
        "damage":       [2,  3,  5],
        "bullet_speed": [3.5, 4.5, 5.5],
        "colors":       [C_NAVY, C_DGRAY, C_LGRAY],
        "shape":        "tri",
        "special":      "aoe",    # explose à l'impact (rayon 20)
        "desc":         "AoE splash, empoisonne",
    },
    "oni": {
        "label":        "Oni Canon",
        "cost":         [200, 260, 320],
        "range":        [95, 110, 130],
        "cooldown":     [55, 42, 30],
        "damage":       [8,  14, 22],
        "bullet_speed": [1.8, 2.2, 2.8],
        "colors":       [C_BGRAY, C_LGRAY, C_WHITE],
        "shape":        "hex",
        "special":      "pierce", # traverse plusieurs ennemis
        "desc":         "Lourd, traverse les ennemis",
    },
}

TOWER_KEYS = list(TOWER_DEFS.keys())

# ===========================================================
#  DÉFINITIONS DES ENNEMIS (6 types)
# ===========================================================
ENEMY_DEFS = {
    "grunt": {
        "label":  "Grunt",
        "hp":     4,
        "speed":  0.65,
        "reward": 10,
        "color":  C_RED,
        "size":   5,
        "dmg_to_base": 1,
        "immune": [],
    },
    "fast": {
        "label":  "Rapide",
        "hp":     3,
        "speed":  1.6,
        "reward": 15,
        "color":  C_YELLOW,
        "size":   4,
        "dmg_to_base": 1,
        "immune": [],
    },
    "tank": {
        "label":  "Tank",
        "hp":     18,
        "speed":  0.35,
        "reward": 35,
        "color":  C_DGRAY,
        "size":   9,
        "dmg_to_base": 3,
        "immune": ["slow"],
    },
    "boss": {
        "label":  "BOSS",
        "hp":     70,
        "speed":  0.28,
        "reward": 120,
        "color":  C_PURPLE,
        "size":   12,
        "dmg_to_base": 8,
        "immune": [],
    },
    "kamikaze": {
        "label":  "Kamikaze",
        "hp":     5,
        "speed":  1.1,
        "reward": 20,
        "color":  C_ORANGE,
        "size":   5,
        "dmg_to_base": 2,
        "immune": [],
        "explode_on_death": True,
    },
    "aerial": {
        "label":  "Aérien",
        "hp":     6,
        "speed":  1.2,
        "reward": 25,
        "color":  C_LBLUE,
        "size":   5,
        "dmg_to_base": 2,
        "immune": ["slow", "burn"],
        "flying": True,
    },
}

# ===========================================================
#  VAGUES (10 vagues normales + mode survie)
# ===========================================================
WAVES = [
    # Wave 1
    [("grunt",3),("grunt",55),("grunt",55),("grunt",70),("grunt",55)],
    # Wave 2
    [("grunt",3),("fast",40),("grunt",50),("fast",40),("grunt",60),("fast",40)],
    # Wave 3
    [("grunt",3),("grunt",40),("tank",50),("grunt",40),("grunt",40),("aerial",60)],
    # Wave 4
    [("fast",3),("fast",30),("tank",50),("kamikaze",35),("fast",30),("tank",80)],
    # Wave 5 — boss 1
    [("grunt",3),("fast",30),("grunt",40),("boss",70),("grunt",40),("fast",30),("kamikaze",25)],
    # Wave 6
    [("tank",3),("aerial",30),("fast",28),("tank",80),("aerial",25),("grunt",40),("grunt",40),("tank",100)],
    # Wave 7
    [("fast",3),("fast",20),("fast",20),("aerial",25),("tank",45),("boss",75),("kamikaze",20),("fast",20),("aerial",20)],
    # Wave 8
    [("tank",3),("kamikaze",30),("kamikaze",25),("fast",25),("boss",90),("aerial",25),("tank",50),("kamikaze",20)],
    # Wave 9
    [("boss",3),("tank",55),("aerial",20),("aerial",20),("fast",25),("fast",25),("boss",100),("tank",55),("kamikaze",20),("fast",20)],
    # Wave 10 — finale
    [("boss",3),("tank",40),("boss",80),("aerial",20),("kamikaze",15),("kamikaze",15),("boss",100),("tank",40),("fast",20),("fast",20),("boss",130),("aerial",25)],
]

# ===========================================================
#  SHOP (articles disponibles entre vagues)
# ===========================================================
SHOP_ITEMS = [
    {"id": "hp_potion",   "label": "+5 HP",          "cost": 60,  "color": C_LGREEN, "icon": "♥"},
    {"id": "gold_mine",   "label": "+80 Or",          "cost": 0,   "color": C_YELLOW, "icon": "◆"},  # gratuit bonus
    {"id": "fury_reset",  "label": "Fury rechargée",  "cost": 80,  "color": C_RED,    "icon": "✦"},
    {"id": "slow_all",    "label": "Gel zone",        "cost": 100, "color": C_LBLUE,  "icon": "❄"},
    {"id": "double_gold", "label": "Or x2 (vague)",   "cost": 120, "color": C_ORANGE, "icon": "★"},
    {"id": "max_upgrade", "label": "Upgrade gratuit", "cost": 150, "color": C_PURPLE, "icon": "▲"},
]

# ===========================================================
#  PARTICULES
# ===========================================================
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=None, size=1):
        self.x     = x
        self.y     = y
        self.color = color
        self.vx    = vx if vx is not None else random.uniform(-1.8, 1.8)
        self.vy    = vy if vy is not None else random.uniform(-2.2, 0.2)
        self.life  = life if life is not None else random.randint(10, 24)
        self.size  = size
        self.alive = True

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.09
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive and 0 <= self.x < W and 0 <= self.y < H:
            if self.size <= 1:
                pyxel.pset(int(self.x), int(self.y), self.color)
            else:
                pyxel.circ(int(self.x), int(self.y), self.size - 1, self.color)

# ===========================================================
#  PÉTALE SAKURA (ambiance permanente)
# ===========================================================
class Sakura:
    def __init__(self, x=None, y=None):
        self.reset(x, y)

    def reset(self, x=None, y=None):
        self.x     = x if x is not None else random.randint(0, W)
        self.y     = y if y is not None else random.randint(-10, H)
        self.vx    = random.uniform(-0.5, 0.2)
        self.vy    = random.uniform(0.25, 0.7)
        self.angle = random.uniform(0, math.pi * 2)
        self.dangle= random.uniform(-0.06, 0.06)
        self.color = random.choice([C_PINK, C_PEACH, C_WHITE, C_PINK])
        self.life  = random.randint(200, 500)

    def update(self):
        self.x     += self.vx + math.sin(self.angle) * 0.25
        self.y     += self.vy
        self.angle += self.dangle
        self.life  -= 1
        if self.life <= 0 or self.y > H + 4:
            self.reset(x=random.randint(0, W), y=-4)

    def draw(self):
        pyxel.pset(int(self.x), int(self.y), self.color)

# ===========================================================
#  TEXTE FLOTTANT
# ===========================================================
class FloatText:
    def __init__(self, x, y, text, color, big=False):
        self.x     = x
        self.y     = y
        self.text  = text
        self.color = color
        self.life  = 50 if big else 38
        self.max_life = self.life
        self.vy    = -0.5 if big else -0.35
        self.alive = True
        self.big   = big

    def update(self):
        self.y    += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive:
            pyxel.text(int(self.x), int(self.y), self.text, self.color)

# ===========================================================
#  NOTIFICATION ACHIEVEMENT
# ===========================================================
class AchievToast:
    def __init__(self, label, icon):
        self.label = label
        self.icon  = icon
        self.life  = 120
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if not self.alive:
            return
        alpha = min(self.life, 20)
        bx = W - 110
        by = 16
        pyxel.rect(bx, by, 108, 18, C_BLACK)
        pyxel.rectb(bx, by, 108, 18, C_YELLOW)
        pyxel.text(bx + 3, by + 3, f"{self.icon} SUCCES: {self.label}", C_YELLOW)

# ===========================================================
#  BALLE
# ===========================================================
class Bullet:
    def __init__(self, x, y, target, damage, speed, color, special=None, aoe_radius=0):
        self.x          = x
        self.y          = y
        self.target     = target
        self.damage     = damage
        self.speed      = speed
        self.color      = color
        self.special    = special
        self.aoe_radius = aoe_radius
        self.alive      = True
        self.trail      = []  # historique positions pour traînée

    def update(self, particles, float_texts, enemies):
        if not self.target.alive:
            self.alive = False
            return

        # Traînée
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 4:
            self.trail.pop(0)

        dx   = self.target.x - self.x
        dy   = self.target.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist < 4:
            self._on_hit(particles, float_texts, enemies)
        else:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def _on_hit(self, particles, float_texts, enemies):
        # Effet spécial AoE
        if self.special == "aoe":
            for e in enemies:
                if not e.alive:
                    continue
                dx = e.x - self.x
                dy = e.y - self.y
                if math.sqrt(dx*dx + dy*dy) < self.aoe_radius:
                    e.hp -= self.damage
                    e.apply_status("poison", 120)
                    if e.hp <= 0:
                        e.alive = False
            # Explosion visuelle
            for _ in range(12):
                particles.append(Particle(self.x, self.y, C_LGREEN,
                                          random.uniform(-2.5, 2.5),
                                          random.uniform(-2.5, 2.5), 18, 2))
            self.alive = False
            return

        # Dégâts sur la cible principale
        self.target.hp -= self.damage

        # Appliquer statut
        if self.special == "burn" and "burn" not in self.target.immune:
            self.target.apply_status("burn", 90)
        elif self.special == "slow" and "slow" not in self.target.immune:
            self.target.apply_status("slow", 120)

        # Texte flottant
        float_texts.append(FloatText(
            self.target.x - 4, self.target.y - 10,
            f"-{self.damage}", C_WHITE
        ))

        # Particules impact
        for _ in range(5):
            particles.append(Particle(self.x, self.y, self.color))

        if self.target.hp <= 0:
            self.target.alive = False

        # Pierce : ne pas mourir
        if self.special == "pierce":
            self.alive = False  # simplifié — un seul impact dans cette version
        else:
            self.alive = False

    def draw(self):
        # Traînée
        for i, (tx, ty) in enumerate(self.trail):
            c = C_DGRAY if i < 2 else self.color
            pyxel.pset(tx, ty, c)
        # Corps
        pyxel.circ(int(self.x), int(self.y), 2, self.color)

# ===========================================================
#  ENNEMI
# ===========================================================
class Enemy:
    def __init__(self, etype, path):
        d          = ENEMY_DEFS[etype]
        self.path  = path
        self.index = 0
        self.x, self.y = path[0]
        self.type  = etype
        self.hp    = d["hp"]
        self.max_hp= d["hp"]
        self.base_speed = d["speed"]
        self.speed = d["speed"]
        self.reward= d["reward"]
        self.color = d["color"]
        self.size  = d["size"]
        self.dmg_to_base = d["dmg_to_base"]
        self.immune = d.get("immune", [])
        self.flying = d.get("flying", False)
        self.explode_on_death = d.get("explode_on_death", False)
        self.alive = True
        self.reached_end = False

        # Statuts actifs : {nom: frames_restantes}
        self.statuses = {}
        # Effets visuels
        self.flash_timer = 0

    def apply_status(self, name, duration):
        if name not in self.immune:
            self.statuses[name] = duration

    def update(self):
        if not self.alive:
            return

        # Mise à jour statuts
        for s in list(self.statuses.keys()):
            self.statuses[s] -= 1
            if self.statuses[s] <= 0:
                del self.statuses[s]

        # Calcul vitesse modifiée
        spd = self.base_speed
        if "slow" in self.statuses:
            spd *= 0.4
        if "freeze" in self.statuses:
            spd = 0.0

        # Dégâts poison
        if "poison" in self.statuses:
            if self.statuses["poison"] % 20 == 0:
                self.hp -= 1
                self.flash_timer = 3
                if self.hp <= 0:
                    self.alive = False
                    return

        # Dégâts brûlure
        if "burn" in self.statuses:
            if self.statuses["burn"] % 15 == 0:
                self.hp -= 1
                self.flash_timer = 3
                if self.hp <= 0:
                    self.alive = False
                    return

        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Déplacement
        if self.index < len(self.path) - 1:
            tx, ty = self.path[self.index + 1]
            dx = tx - self.x
            dy = ty - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 2:
                self.index += 1
            else:
                self.x += dx / dist * spd
                self.y += dy / dist * spd
        else:
            self.reached_end = True
            self.alive = False

    def draw(self):
        if not self.alive:
            return
        s = self.size
        ix, iy = int(self.x), int(self.y)

        # Couleur avec flash
        c = C_WHITE if self.flash_timer > 0 else self.color

        # Corps
        pyxel.circ(ix, iy, s, c)

        # Marqueur flying
        if self.flying:
            pyxel.circb(ix, iy, s + 2, C_LBLUE)

        # Bordure boss
        if self.type == "boss":
            pyxel.circb(ix, iy, s + 1, C_WHITE)

        # Marqueur kamikaze (croix)
        if self.type == "kamikaze":
            pyxel.pset(ix, iy, C_BLACK)
            pyxel.pset(ix - 1, iy, C_BLACK)
            pyxel.pset(ix + 1, iy, C_BLACK)

        # Indicateur statut
        if "burn" in self.statuses:
            pyxel.pset(ix, iy - s - 1, C_ORANGE)
        if "slow" in self.statuses:
            pyxel.pset(ix + 1, iy - s - 1, C_LBLUE)
        if "poison" in self.statuses:
            pyxel.pset(ix - 1, iy - s - 1, C_LGREEN)

        # Barre de vie
        bar_w = s * 2
        bx = ix - s
        by = iy - s - 5
        ratio = max(0, self.hp / self.max_hp)
        pyxel.rect(bx, by, bar_w, 2, C_RED)
        pyxel.rect(bx, by, int(bar_w * ratio), 2, C_LGREEN)

# ===========================================================
#  TOUR
# ===========================================================
class Tower:
    def __init__(self, x, y, ttype):
        self.x     = x
        self.y     = y
        self.type  = ttype
        self.level = 0
        self._sync()
        self.cooldown_timer = 0
        self.selected       = False
        self.shoot_anim     = 0   # frames d'animation de tir

    def _sync(self):
        d  = TOWER_DEFS[self.type]
        lv = self.level
        self.range      = d["range"][lv]
        self.cooldown   = d["cooldown"][lv]
        self.damage     = d["damage"][lv]
        self.bullet_spd = d["bullet_speed"][lv]
        self.color      = d["colors"][lv]
        self.special    = d["special"]

    def upgrade_cost(self):
        if self.level >= 2:
            return None
        return TOWER_DEFS[self.type]["cost"][self.level + 1]

    def upgrade(self):
        if self.level < 2:
            self.level += 1
            self._sync()

    def sell_value(self):
        d     = TOWER_DEFS[self.type]
        total = sum(d["cost"][:self.level + 1])
        return total // 2

    def update(self, enemies, bullets, particles, float_texts, double_gold_active=False):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
        if self.shoot_anim > 0:
            self.shoot_anim -= 1

        if self.cooldown_timer == 0:
            best = None
            best_progress = -1
            for e in enemies:
                if not e.alive:
                    continue
                # Archers et Ninja ne touchent pas les aériens (sauf Tamiko et Oni)
                if e.flying and self.type in ("archer", "katana"):
                    continue
                dx   = e.x - self.x
                dy   = e.y - self.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < self.range:
                    progress = e.index + (e.speed / 10.0)
                    if progress > best_progress:
                        best_progress = progress
                        best = e
            if best:
                aoe_r = 20 if self.special == "aoe" else 0
                bullets.append(Bullet(
                    self.x, self.y, best,
                    self.damage, self.bullet_spd, self.color,
                    self.special, aoe_r,
                ))
                self.cooldown_timer = self.cooldown
                self.shoot_anim     = 5

    def draw(self):
        d     = TOWER_DEFS[self.type]
        shape = d["shape"]
        s     = 6
        x, y  = int(self.x), int(self.y)
        c     = self.color

        # Pulsation si en train de tirer
        pulse = 1 if self.shoot_anim > 0 else 0

        # Socle
        pyxel.rect(x - s - 1, y - s - 1, (s + 1)*2, (s + 1)*2, C_BROWN)

        if shape == "circle":
            pyxel.circ(x, y, s + pulse, c)
            pyxel.circb(x, y, s + pulse, C_WHITE)
        elif shape == "square":
            pyxel.rect(x - s, y - s, s * 2, s * 2, c)
            pyxel.rectb(x - s, y - s, s * 2, s * 2, C_WHITE)
        elif shape == "diamond":
            pyxel.tri(x, y - s - pulse, x + s + pulse, y, x, y + s + pulse, c)
            pyxel.tri(x, y - s - pulse, x - s - pulse, y, x, y + s + pulse, c)
        elif shape == "tri":
            pyxel.tri(x - s, y + s, x + s, y + s, x, y - s, c)
        elif shape == "hex":
            pyxel.rect(x - s, y - s//2, s * 2, s, c)
            pyxel.rectb(x - s, y - s//2, s * 2, s, C_WHITE)
            pyxel.circ(x, y, s//2, c)

        # Niveau
        lv_str = ["I", "II", "III"][self.level]
        pyxel.text(x - 2, y - 2, lv_str, C_BLACK)

        # Sélection + portée
        if self.selected:
            pyxel.circb(x, y, self.range, C_LGRAY)
            pyxel.circb(x, y, s + 2, C_YELLOW)

# ===========================================================
#  GESTIONNAIRE DE VAGUES
# ===========================================================
class WaveManager:
    def __init__(self, path, survive_mode=False):
        self.path          = path
        self.wave_index    = 0
        self.queue         = []
        self.timer         = 0
        self.active        = False
        self.all_done      = False
        self.between_delay = 200  # ~6.6s entre vagues
        self.between_timer = 0
        self.waiting       = False
        self.survive_mode  = survive_mode
        self.survive_wave  = 0   # compteur infini

    def start_next_wave(self):
        if not self.survive_mode and self.wave_index >= len(WAVES):
            self.all_done = True
            return

        if self.survive_mode:
            self.survive_wave += 1
            wave = self._gen_survive_wave(self.survive_wave)
        else:
            wave = list(WAVES[self.wave_index])
            self.wave_index += 1

        self.queue  = wave
        self.timer  = 0
        self.active = True

    def _gen_survive_wave(self, n):
        """Génère une vague procédurale croissante en difficulté."""
        types = ["grunt", "fast", "tank", "boss", "kamikaze", "aerial"]
        pool = []
        count = 5 + n * 2
        for i in range(count):
            idx = min(i * len(types) // count, len(types) - 1)
            if n > 5:
                idx = min(idx + 1, len(types) - 1)
            t = types[idx]
            delay = max(15, 50 - n * 2)
            pool.append((t, delay if i > 0 else 3))
        return pool

    def update(self, enemies):
        if self.all_done:
            return

        if self.waiting:
            self.between_timer -= 1
            if self.between_timer <= 0:
                self.waiting = False
                self.start_next_wave()
            return

        if not self.active:
            return

        if self.queue:
            etype, delay = self.queue[0]
            self.timer += 1
            if self.timer >= delay:
                enemies.append(Enemy(etype, self.path))
                self.queue.pop(0)
                self.timer = 0
        else:
            if not any(e.alive for e in enemies):
                self.active        = False
                self.waiting       = True
                self.between_timer = self.between_delay

    @property
    def current_wave(self):
        return self.wave_index if not self.survive_mode else self.survive_wave

    def time_to_next(self):
        return max(0, self.between_timer // FPS)

# ===========================================================
#  SCREEN SHAKE
# ===========================================================
class ScreenShake:
    def __init__(self):
        self.shake = 0
        self.ox    = 0
        self.oy    = 0

    def trigger(self, intensity=3):
        self.shake = max(self.shake, intensity)

    def update(self):
        if self.shake > 0:
            self.ox = random.randint(-self.shake, self.shake)
            self.oy = random.randint(-self.shake, self.shake)
            self.shake -= 1
        else:
            self.ox = 0
            self.oy = 0

# ===========================================================
#  HUD
# ===========================================================
def draw_hud(hp, max_hp, gold, wave, total_waves, score,
             selected_type, selected_tower, wave_mgr,
             ultimate_bars, combo, double_gold_timer,
             survive_mode, shake):
    ox, oy = shake.ox, shake.oy

    # Bande noire haut
    pyxel.rect(0 + ox, 0 + oy, W, 14, C_BLACK)

    # HP bar
    pyxel.text(3 + ox, 3 + oy, "HP:", C_WHITE)
    bar_w = 38
    ratio = max(0, hp / max_hp)
    pyxel.rect(17 + ox, 3 + oy, bar_w, 6, C_RED)
    pyxel.rect(17 + ox, 3 + oy, int(bar_w * ratio), 6, C_LGREEN)
    pyxel.text(57 + ox, 3 + oy, f"{hp}", C_WHITE)

    # Or
    pyxel.text(78 + ox, 3 + oy, f"Or:{gold}", C_YELLOW)

    # Vague
    wlabel = "∞" if survive_mode else str(total_waves)
    pyxel.text(138 + ox, 3 + oy, f"Vg:{wave}/{wlabel}", C_ORANGE)

    # Score
    pyxel.text(196 + ox, 3 + oy, f"Sc:{score}", C_LBLUE)

    # Combo
    if combo > 1:
        pyxel.text(196 + ox, 14 + oy, f"x{combo}COMBO!", C_YELLOW)

    # Double gold timer
    if double_gold_timer > 0:
        pyxel.text(3 + ox, 14 + oy, f"Or x2: {double_gold_timer//FPS+1}s", C_YELLOW)

    # Bandeau bas
    pyxel.rect(0, H - 28, W, 28, C_BLACK)

    # Touches tours
    labels = [
        ("1:Arch", 2,   C_LGREEN),
        ("2:Kat",  40,  C_RED),
        ("3:Tam",  76,  C_PINK),
        ("4:Nin",  112, C_NAVY),
        ("5:Oni",  148, C_BGRAY),
    ]
    for txt, x, c in labels:
        pyxel.text(x, H - 26, txt, c)

    # Ultime bars
    ult_names = ["Q:Fury", "W:Gel", "E:Pluie"]
    ult_colors = [C_RED, C_LBLUE, C_LGREEN]
    for i, (ub, un, uc) in enumerate(zip(ultimate_bars, ult_names, ult_colors)):
        bw  = 40
        bh  = 4
        bx  = 3 + i * 44
        by  = H - 13
        pyxel.rect(bx, by, bw, bh, C_DGRAY)
        if ub["ready"]:
            pyxel.rect(bx, by, bw, bh, uc)
        else:
            r = ub["cd"] / ub["max"]
            pyxel.rect(bx, by, int(bw * r), bh, uc)
        pyxel.rectb(bx, by, bw, bh, C_LGRAY)
        pyxel.text(bx, by - 6, un, uc if ub["ready"] else C_DGRAY)

    # Tour sélectionnée ou info tour
    if selected_tower:
        t  = selected_tower
        uc = t.upgrade_cost()
        sv = t.sell_value()
        d  = TOWER_DEFS[t.type]
        info = f"{d['label']} Lv{t.level+1} Up:{uc or 'MAX'} V:{sv}"
        pyxel.text(140, H - 26, info, C_BGRAY)
    elif selected_type:
        d    = TOWER_DEFS[selected_type]
        cost = d["cost"][0]
        pyxel.text(140, H - 26, f">>{d['label']} {cost}g", C_WHITE)

    # Compte à rebours
    if wave_mgr.waiting:
        s   = wave_mgr.time_to_next()
        msg = f"Prochain: {s}s"
        pyxel.text(W//2 - len(msg)*2, H//2 - 4, msg, C_WHITE)

# ===========================================================
#  ÉCRAN SHOP
# ===========================================================
def draw_shop(items, selected_idx, gold, free_upgrade_available):
    pyxel.rect(15, 20, 226, 210, C_BLACK)
    pyxel.rectb(15, 20, 226, 210, C_RED)

    # Coins dorés
    for cx, cy in [(15, 20), (238, 20), (15, 227), (238, 227)]:
        pyxel.rect(cx, cy, 3, 3, C_YELLOW)

    pyxel.text(85, 26, "SHOP INTER-VAGUE", C_YELLOW)
    pyxel.rect(25, 34, 206, 1, C_RED)

    for i, item in enumerate(items):
        by = 40 + i * 28
        # fond sélection
        if i == selected_idx:
            pyxel.rect(20, by, 216, 26, C_NAVY)
        pyxel.rectb(20, by, 216, 26, item["color"])

        cost = 0 if item["id"] == "gold_mine" else item["cost"]
        can_afford = gold >= cost or item["id"] == "gold_mine"

        tc = item["color"] if can_afford else C_DGRAY
        pyxel.text(26, by + 4, f"{item['icon']} {item['label']}", tc)
        if item["id"] == "gold_mine":
            pyxel.text(180, by + 4, "GRATUIT", C_YELLOW)
        else:
            pyxel.text(180, by + 4, f"{item['cost']}or", tc)
        pyxel.text(26, by + 13, _shop_desc(item["id"]), C_LGRAY)

    pyxel.text(30, 215, "HAUT/BAS=naviguer  ENTREE=acheter  ESC=fermer", C_LGRAY)

def _shop_desc(item_id):
    descs = {
        "hp_potion":   "Restaure 5 points de vie",
        "gold_mine":   "+80 or offert par les villageois",
        "fury_reset":  "Recharge immédiate de Fury",
        "slow_all":    "Gèle tous les ennemis 5s",
        "double_gold": "Doublé l'or toute la prochaine vague",
        "max_upgrade": "Améliore une tour gratuitement",
    }
    return descs.get(item_id, "")

# ===========================================================
#  ÉCRANS GAME OVER / VICTOIRE
# ===========================================================
def draw_game_over(score, highscores, wave):
    pyxel.rect(30, 60, 196, 130, C_BLACK)
    pyxel.rectb(30, 60, 196, 130, C_RED)
    pyxel.text(88, 70, "GAME OVER", C_RED)
    pyxel.text(60, 83, "Le Japon est tombe...", C_WHITE)
    pyxel.text(65, 96, f"Score: {score}  Vague: {wave}", C_YELLOW)
    # Top 3
    pyxel.text(60, 110, "MEILLEURS SCORES:", C_ORANGE)
    for i, hs in enumerate(highscores[:3]):
        pyxel.text(65, 120 + i * 10,
                   f"{i+1}. {hs['score']:>6}  vg{hs['wave']}", C_LGRAY)
    pyxel.text(60, 155, "ENTREE=Rejouer  ESC=Quitter", C_LGRAY)

def draw_victory(score, highscores):
    pyxel.rect(20, 55, 216, 140, C_BLACK)
    pyxel.rectb(20, 55, 216, 140, C_YELLOW)
    pyxel.text(85, 65, "VICTOIRE !", C_YELLOW)
    pyxel.text(50, 78, "Le Japon est protege !", C_LGREEN)
    pyxel.text(55, 91, f"Score final: {score}", C_WHITE)
    stars = min(3, score // 1000 + 1)
    pyxel.text(100, 104, "★" * stars + "☆" * (3 - stars), C_ORANGE)
    pyxel.text(50, 118, "MEILLEURS SCORES:", C_ORANGE)
    for i, hs in enumerate(highscores[:3]):
        pyxel.text(55, 128 + i * 10,
                   f"{i+1}. {hs['score']:>6}  vg{hs['wave']}", C_LGRAY)
    pyxel.text(55, 162, "ENTREE=Rejouer  ESC=Quitter", C_LGRAY)

# ===========================================================
#  UTILITAIRES
# ===========================================================
def point_near_path(px, py, path, min_dist=15):
    for i in range(len(path) - 1):
        ax, ay = path[i]
        bx, by = path[i + 1]
        dx, dy = bx - ax, by - ay
        seg_len2 = dx*dx + dy*dy
        if seg_len2 == 0:
            t = 0.0
        else:
            t = max(0.0, min(1.0, ((px - ax)*dx + (py - ay)*dy) / seg_len2))
        cx2 = ax + t * dx
        cy2 = ay + t * dy
        dist = math.sqrt((px - cx2)**2 + (py - cy2)**2)
        if dist < min_dist:
            return True
    return False

# ===========================================================
#  CLASSE PRINCIPALE
# ===========================================================
class Game:
    STATE_PLAYING   = "playing"
    STATE_GAME_OVER = "game_over"
    STATE_VICTORY   = "victory"
    STATE_PAUSED    = "paused"
    STATE_SHOP      = "shop"

    def __init__(self, survive_mode=False):
        pyxel.init(W, H, title="JapanTahan — Défense du Japon", fps=FPS)
        pyxel.images[0].load(0, 0, "assets/map_small.png")
        pyxel.mouse(True)

        self.survive_mode = survive_mode
        self._init_music()

        # Achievements persistants
        self.achievements = {k: dict(v) for k, v in ACHIEVEMENTS.items()}
        self.achiev_toasts = []

        self.reset()
        pyxel.run(self.update, self.draw)

    # ── Musique MP3 ────────────────────────────────────────
    def _init_music(self):
        self.mp3_active = False
        if _PYGAME_OK:
            try:
                pygame.mixer.init()
                mp3 = "assets/Shattered Shogun.mp3"
                if os.path.exists(mp3):
                    pygame.mixer.music.load(mp3)
                    pygame.mixer.music.set_volume(0.55)
                    pygame.mixer.music.play(-1)
                    self.mp3_active = True
            except Exception:
                pass
        if not self.mp3_active:
            self._setup_pyxel_music()

    def _setup_pyxel_music(self):
        """Musique de fallback pyxel si MP3 indispo."""
        pyxel.sound(0).set(
            "e3 r g3 r a3 r g3 e3 d3 r e3 r g3 r e3 r",
            "t", "55556666 55556666", "nnnnnnnn nnnnnnnn", 20)
        pyxel.sound(1).set(
            "a2 r r r e2 r r r g2 r r r d2 r r r",
            "s", "3333 3333 3333 3333", "nnnn nnnn nnnn nnnn", 20)
        pyxel.sound(2).set(
            "a1 r r a1 r r a1 r a1 r a1 r r a1 r r",
            "n", "7777 7777 7777 7777", "nnnn nnnn nnnn nnnn", 20)
        pyxel.music(0).set([0], [1], [2], [])
        pyxel.playm(0, loop=True)

    # ── Réinitialisation ────────────────────────────────────
    def reset(self):
        self.hp          = STARTING_HP
        self.max_hp      = STARTING_HP
        self.gold        = STARTING_GOLD
        self.score       = 0
        self.state       = self.STATE_PLAYING
        self.kill_count  = 0
        self.hp_at_wave_start = STARTING_HP

        self.enemies     = []
        self.towers      = []
        self.bullets     = []
        self.particles   = []
        self.float_texts = []
        self.sakuras     = [Sakura() for _ in range(22)]

        self.wave_mgr    = WaveManager(PATH_MAIN, survive_mode=self.survive_mode)
        self.wave_mgr.start_next_wave()

        # Sélection
        self.selected_type  = "archer"
        self.selected_tower = None
        self.preview_x      = -999
        self.preview_y      = -999

        # Combo
        self.combo          = 1
        self.combo_timer    = 0

        # Double gold (durée en frames)
        self.double_gold_timer = 0

        # Free upgrade (acheté au shop)
        self.free_upgrade_pending = False

        # Highscores
        self.highscores = load_highscores()

        # Shop
        self.shop_items    = list(SHOP_ITEMS)
        random.shuffle(self.shop_items)
        self.shop_items    = self.shop_items[:4]  # 4 items aléatoires
        self.shop_idx      = 0
        self.shop_shown    = False

        # Screen shake
        self.shake = ScreenShake()

        # 3 ultimes : Fury, Gel de zone, Pluie de flèches
        self.ults = [
            {"ready": True, "cd": 0, "max": FPS * 30},   # Q Fury
            {"ready": True, "cd": 0, "max": FPS * 40},   # W Gel
            {"ready": True, "cd": 0, "max": FPS * 35},   # E Pluie
        ]
        self.ultimate_fx   = 0
        self.fury_count    = 0

        # Timer vague (pour succès speedrun)
        self.wave_timer    = 0

        # Pause
        self.paused        = False

    # ── Update principal ────────────────────────────────────
    def update(self):
        mx, my = pyxel.mouse_x, pyxel.mouse_y

        # Toasts achievements
        for t in self.achiev_toasts:
            t.update()
        self.achiev_toasts = [t for t in self.achiev_toasts if t.alive]

        # Game over / Victoire
        if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                if _PYGAME_OK and self.mp3_active:
                    pygame.mixer.music.stop()
                pyxel.quit()
            return

        # Shop
        if self.state == self.STATE_SHOP:
            self._update_shop()
            return

        # Pause
        if self.state == self.STATE_PAUSED:
            if pyxel.btnp(pyxel.KEY_P) or pyxel.btnp(pyxel.KEY_ESCAPE):
                self.state = self.STATE_PLAYING
            return

        if pyxel.btnp(pyxel.KEY_P):
            self.state = self.STATE_PAUSED
            return

        # Sakura
        for s in self.sakuras:
            s.update()

        # Screen shake
        self.shake.update()

        # Timer vague
        self.wave_timer += 1

        # ── Sélection type tour ───────────────────────────
        key_map = {
            pyxel.KEY_1: "archer",
            pyxel.KEY_2: "katana",
            pyxel.KEY_3: "tamiko",
            pyxel.KEY_4: "ninja",
            pyxel.KEY_5: "oni",
        }
        for key, ttype in key_map.items():
            if pyxel.btnp(key):
                self.selected_type  = ttype
                self.selected_tower = None

        # ── Upgrade ───────────────────────────────────────
        if pyxel.btnp(pyxel.KEY_U) and self.selected_tower:
            t  = self.selected_tower
            uc = t.upgrade_cost()
            if self.free_upgrade_pending and uc:
                t.upgrade()
                self.free_upgrade_pending = False
                self._check_achiev("max_tower", t.level == 2)
                self.float_texts.append(FloatText(t.x - 10, t.y - 14, "UPGRADE FREE!", C_YELLOW))
            elif uc and self.gold >= uc:
                self.gold -= uc
                t.upgrade()
                self.score += 10
                self._check_achiev("max_tower", t.level == 2)

        # ── Vendre ────────────────────────────────────────
        if pyxel.btnp(pyxel.KEY_V) and self.selected_tower:
            sv = self.selected_tower.sell_value()
            self.gold += sv
            self.towers.remove(self.selected_tower)
            self.selected_tower = None

        # ── Ultimes ───────────────────────────────────────
        if pyxel.btnp(pyxel.KEY_Q):
            self._use_ult(0)
        if pyxel.btnp(pyxel.KEY_W):
            self._use_ult(1)
        if pyxel.btnp(pyxel.KEY_E):
            self._use_ult(2)

        # Recharge ults
        for ub in self.ults:
            if not ub["ready"]:
                ub["cd"] += 1
                if ub["cd"] >= ub["max"]:
                    ub["ready"] = True
                    ub["cd"]    = 0

        # Double gold timer
        if self.double_gold_timer > 0:
            self.double_gold_timer -= 1

        # Combo timer
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 1

        # FX
        if self.ultimate_fx > 0:
            self.ultimate_fx -= 1

        # ── Clic gauche ───────────────────────────────────
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            clicked = self._tower_at(mx, my)
            if clicked:
                if self.selected_tower == clicked:
                    clicked.selected       = False
                    self.selected_tower    = None
                else:
                    if self.selected_tower:
                        self.selected_tower.selected = False
                    self.selected_tower    = clicked
                    clicked.selected       = True
            else:
                if my >= 14 and my <= H - 28:
                    if point_near_path(mx, my, PATH_MAIN):
                        for _ in range(6):
                            self.particles.append(
                                Particle(mx, my, C_RED,
                                         random.uniform(-1, 1),
                                         random.uniform(-1, 1), 12))
                    else:
                        cost = TOWER_DEFS[self.selected_type]["cost"][0]
                        if self.gold >= cost:
                            if self.selected_tower:
                                self.selected_tower.selected = False
                                self.selected_tower = None
                            self.gold -= cost
                            self.towers.append(Tower(mx, my, self.selected_type))
                        else:
                            self.float_texts.append(
                                FloatText(mx - 14, my - 8, "Or insuffisant!", C_YELLOW))

        # Clic droit = désélection
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            if self.selected_tower:
                self.selected_tower.selected = False
                self.selected_tower = None

        self.preview_x = mx
        self.preview_y = my

        # ── Vague ─────────────────────────────────────────
        prev_waiting = self.wave_mgr.waiting
        self.wave_mgr.update(self.enemies)

        # Déclencher le shop quand une vague se termine
        if not prev_waiting and self.wave_mgr.waiting and not self.shop_shown:
            self.shop_shown = True
            if self.wave_mgr.current_wave < len(WAVES) or self.survive_mode:
                self._open_shop()

        # ── Ennemis ───────────────────────────────────────
        to_remove = []
        for e in self.enemies:
            e.update()
            if e.reached_end and not e.alive:
                dmg = e.dmg_to_base
                self.hp -= dmg
                self.shake.trigger(4 if dmg >= 3 else 2)
                self.float_texts.append(
                    FloatText(W//2 - 12, H//2 - 22, f"-{dmg} HP!", C_RED, big=True))
                for _ in range(10):
                    self.particles.append(
                        Particle(PATH_MAIN[-1][0], PATH_MAIN[-1][1] - 10, C_RED))
                to_remove.append(e)
            elif not e.alive:
                # Mort en combat
                reward = e.reward * (2 if self.double_gold_timer > 0 else 1)
                self.gold  += reward
                self.score += reward * 2 * self.combo
                self.kill_count += 1

                # Combo
                self.combo = min(8, self.combo + 1) if self.combo_timer > 0 else 1
                self.combo_timer = 45

                # Kamikaze explosion
                if e.explode_on_death:
                    for _ in range(16):
                        self.particles.append(
                            Particle(int(e.x), int(e.y), C_ORANGE,
                                     random.uniform(-3, 3),
                                     random.uniform(-3, 3), 22, 2))
                    self.shake.trigger(3)
                    # Dégâts aux tours proches
                    for t in self.towers:
                        dx = t.x - e.x
                        dy = t.y - e.y
                        # pas de dégâts directs sur tours dans cette version simplifiée

                # Particules or
                for _ in range(6):
                    self.particles.append(
                        Particle(int(e.x), int(e.y), C_YELLOW))
                txt = f"+{reward}g"
                if self.combo > 1:
                    txt += f" x{self.combo}"
                self.float_texts.append(
                    FloatText(int(e.x) - 6, int(e.y) - 14, txt, C_YELLOW))

                # Boss mort
                if e.type == "boss":
                    self.shake.trigger(6)
                    self._unlock_achiev("boss_slayer")
                    for _ in range(20):
                        self.particles.append(
                            Particle(int(e.x), int(e.y), C_PURPLE,
                                     random.uniform(-3, 3),
                                     random.uniform(-3, 3), 28, 2))

                to_remove.append(e)

                # Achievements kill count
                self._check_achiev("first_blood", self.kill_count >= 1)
                self._check_achiev("centurion",   self.kill_count >= 100)

        for e in to_remove:
            if e in self.enemies:
                self.enemies.remove(e)

        # Gold hoarding
        self._check_achiev("gold_hoarder", self.gold >= 500)

        # Wave survivor
        if self.wave_mgr.waiting and self.hp == self.hp_at_wave_start:
            self._unlock_achiev("no_damage")
        if self.wave_mgr.current_wave >= 10:
            self._unlock_achiev("survivor_10")

        # Speedrun vague 1
        if self.wave_mgr.current_wave == 1 and self.wave_mgr.waiting:
            if self.wave_timer <= FPS * 30:
                self._unlock_achiev("speedrun")

        # Reset HP au départ de vague
        if not self.wave_mgr.waiting and self.wave_mgr.active and not self.enemies:
            self.hp_at_wave_start = self.hp

        # ── Check game over ───────────────────────────────
        if self.hp <= 0:
            self.hp    = 0
            self.state = self.STATE_GAME_OVER
            self.highscores = save_highscore(self.score, self.wave_mgr.current_wave)
            return

        # ── Check victoire ────────────────────────────────
        any_alive = any(e.alive for e in self.enemies)
        if self.wave_mgr.all_done and not any_alive:
            self.state      = self.STATE_VICTORY
            self.score     += 1000
            self.highscores = save_highscore(self.score, self.wave_mgr.current_wave)
            return

        # ── Tours ─────────────────────────────────────────
        for t in self.towers:
            t.update(self.enemies, self.bullets, self.particles, self.float_texts,
                     self.double_gold_timer > 0)

        # ── Balles ────────────────────────────────────────
        for b in list(self.bullets):
            if b.alive:
                b.update(self.particles, self.float_texts, self.enemies)
        self.bullets = [b for b in self.bullets if b.alive]

        # ── Particules & textes ───────────────────────────
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]
        for ft in self.float_texts:
            ft.update()
        self.float_texts = [ft for ft in self.float_texts if ft.alive]

    # ── Shop ───────────────────────────────────────────────
    def _open_shop(self):
        self.shop_items = random.sample(SHOP_ITEMS, min(4, len(SHOP_ITEMS)))
        self.shop_idx   = 0
        self.state      = self.STATE_SHOP

    def _update_shop(self):
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.shop_idx = (self.shop_idx + 1) % len(self.shop_items)
        if pyxel.btnp(pyxel.KEY_UP):
            self.shop_idx = (self.shop_idx - 1) % len(self.shop_items)
        if pyxel.btnp(pyxel.KEY_RETURN):
            self._buy_shop_item(self.shop_items[self.shop_idx])
            self.state = self.STATE_PLAYING
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.state = self.STATE_PLAYING
            # Bonus or même si on ferme
            self.gold += 30

    def _buy_shop_item(self, item):
        cost = 0 if item["id"] == "gold_mine" else item["cost"]
        if self.gold < cost and item["id"] != "gold_mine":
            self.float_texts.append(FloatText(80, 120, "Or insuffisant!", C_RED))
            return
        self.gold -= cost

        if item["id"] == "hp_potion":
            self.hp = min(self.max_hp, self.hp + 5)
            self.float_texts.append(FloatText(100, 100, "+5 HP!", C_LGREEN))
        elif item["id"] == "gold_mine":
            self.gold += 80
            self.float_texts.append(FloatText(100, 100, "+80 Or!", C_YELLOW))
        elif item["id"] == "fury_reset":
            self.ults[0]["ready"] = True
            self.ults[0]["cd"]    = 0
        elif item["id"] == "slow_all":
            for e in self.enemies:
                if e.alive:
                    e.apply_status("slow", FPS * 5)
        elif item["id"] == "double_gold":
            self.double_gold_timer = FPS * 60
        elif item["id"] == "max_upgrade":
            self.free_upgrade_pending = True
            self.float_texts.append(FloatText(80, 110, "Upgrade gratuit! (U)", C_PURPLE))

    # ── Ultimes ────────────────────────────────────────────
    def _use_ult(self, idx):
        ub = self.ults[idx]
        if not ub["ready"]:
            return
        ub["ready"] = False
        ub["cd"]    = 0

        if idx == 0:  # Fury — dégâts massifs
            self.ultimate_fx = 22
            self.shake.trigger(5)
            self.fury_count += 1
            self._check_achiev("fury_master", self.fury_count >= 5)
            for e in self.enemies:
                if e.alive:
                    e.hp -= 8
                    if e.hp <= 0:
                        e.alive = False
                        self.gold  += e.reward
                        self.score += e.reward * 2
                    for _ in range(8):
                        self.particles.append(
                            Particle(int(e.x), int(e.y), C_RED))
            self.float_texts.append(
                FloatText(W//2 - 22, H//2 - 30, "SAMURAI FURY!", C_RED, big=True))

        elif idx == 1:  # Gel de zone
            self.shake.trigger(2)
            for e in self.enemies:
                if e.alive:
                    e.apply_status("slow", FPS * 6)
                    for _ in range(5):
                        self.particles.append(
                            Particle(int(e.x), int(e.y), C_LBLUE,
                                     random.uniform(-1, 1), random.uniform(-1, 1), 15))
            self.float_texts.append(
                FloatText(W//2 - 22, H//2 - 30, "BLIZZARD!", C_LBLUE, big=True))

        elif idx == 2:  # Pluie de flèches
            self.shake.trigger(2)
            # Bombarde aléatoirement des ennemis
            targets = [e for e in self.enemies if e.alive]
            hits = 0
            for _ in range(min(12, len(targets) * 3 + 5)):
                if targets:
                    t = random.choice(targets)
                    dmg = random.randint(2, 5)
                    t.hp -= dmg
                    self.particles.append(
                        Particle(int(t.x), int(t.y) - 20, C_LGREEN,
                                 0, random.uniform(2, 4), 12))
                    if t.hp <= 0:
                        t.alive = False
                        hits += 1
            self.float_texts.append(
                FloatText(W//2 - 24, H//2 - 30, "PLUIE DE FLECHES!", C_LGREEN, big=True))

    # ── Achievements ────────────────────────────────────────
    def _check_achiev(self, key, condition):
        if condition:
            self._unlock_achiev(key)

    def _unlock_achiev(self, key):
        if key in self.achievements and not self.achievements[key]["unlocked"]:
            self.achievements[key]["unlocked"] = True
            a = self.achievements[key]
            self.achiev_toasts.append(AchievToast(a["label"], a["icon"]))
            self.score += 50

    # ── Trouver tour ────────────────────────────────────────
    def _tower_at(self, mx, my):
        for t in self.towers:
            if abs(t.x - mx) < 10 and abs(t.y - my) < 10:
                return t
        return None

    # ── DRAW ────────────────────────────────────────────────
    def draw(self):
        pyxel.cls(C_BLACK)
        ox, oy = self.shake.ox, self.shake.oy

        # Carte
        pyxel.blt(0 + ox, 0 + oy, 0, 0, 0, W, H)

        # Sakura
        for s in self.sakuras:
            s.draw()

        # Shop overlay
        if self.state == self.STATE_SHOP:
            draw_shop(self.shop_items, self.shop_idx, self.gold, self.free_upgrade_pending)
            return

        # FX ultime (flash)
        if self.ultimate_fx > 0:
            c = C_RED if (self.ultimate_fx % 4 < 2) else C_ORANGE
            pyxel.rectb(1 + ox, 15 + oy, W - 2, H - 44, c)
            pyxel.rectb(2 + ox, 16 + oy, W - 4, H - 46, c)

        # Prévisualisation
        px, py = self.preview_x, self.preview_y
        if 14 < py < H - 28 and not self._tower_at(px, py):
            cost = TOWER_DEFS[self.selected_type]["cost"][0]
            ok   = self.gold >= cost and not point_near_path(px, py, PATH_MAIN)
            c    = C_LGREEN if ok else C_RED
            pyxel.circb(px, py, 7, c)

        # Tours
        for t in self.towers:
            t.draw()

        # Ennemis
        for e in self.enemies:
            e.draw()

        # Balles
        for b in self.bullets:
            b.draw()

        # Particules
        for p in self.particles:
            p.draw()

        # Textes flottants
        for ft in self.float_texts:
            ft.draw()

        # HUD
        draw_hud(
            self.hp, self.max_hp,
            self.gold,
            self.wave_mgr.current_wave,
            len(WAVES),
            self.score,
            self.selected_type if not self.selected_tower else None,
            self.selected_tower,
            self.wave_mgr,
            self.ults,
            self.combo,
            self.double_gold_timer,
            self.survive_mode,
            self.shake,
        )

        # Toasts achievements
        for i, t in enumerate(self.achiev_toasts):
            t.draw()

        # Pause
        if self.state == self.STATE_PAUSED:
            pyxel.rect(78, 108, 100, 36, C_BLACK)
            pyxel.rectb(78, 108, 100, 36, C_WHITE)
            pyxel.text(104, 118, "PAUSE (P)", C_WHITE)
            pyxel.text(88, 130, "SHOP: Debut vague", C_LGRAY)

        # Game Over / Victoire
        if self.state == self.STATE_GAME_OVER:
            draw_game_over(self.score, self.highscores, self.wave_mgr.current_wave)
        elif self.state == self.STATE_VICTORY:
            draw_victory(self.score, self.highscores)

# ===========================================================
#  POINT D'ENTRÉE
# ===========================================================
Game()
