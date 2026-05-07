import pyxel
import os
import math
import random

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===========================================================
#  CONSTANTES GLOBALES
# ===========================================================
W, H         = 256, 256
FPS          = 30
STARTING_HP  = 20
STARTING_GOLD= 150

# Chemin ennemi (waypoints pixel sur la map 256x256)
PATH = [
    (45,  25),
    (45,  70),
    (127, 70),
    (127, 120),
    (190, 120),
    (190, 195),
    (210, 195),
    (210, 256),
]

# ── Palettes couleurs pyxel (index 0-15) ──────────────────
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
#  DÉFINITIONS DES TOURS
# ===========================================================
TOWER_DEFS = {
    "archer": {
        "label":    "Archer",
        "cost":     [50, 75, 100],   # coût par niveau (0=achat, 1=up lv2, 2=up lv3)
        "range":    [55, 70, 85],
        "cooldown": [28, 22, 16],
        "damage":   [1,  2,  3],
        "bullet_speed": [2.5, 3.0, 3.5],
        "colors":   [C_LGREEN, C_GREEN, C_DGRAY],
        "shape":    "circle",
    },
    "katana": {
        "label":    "Katana",
        "cost":     [80, 100, 130],
        "range":    [35, 45, 55],
        "cooldown": [12, 8,  5],
        "damage":   [2,  3,  5],
        "bullet_speed": [4.0, 5.0, 6.0],
        "colors":   [C_RED, C_ORANGE, C_YELLOW],
        "shape":    "square",
    },
    "tamiko": {
        "label":    "Tamiko",
        "cost":     [120, 150, 180],
        "range":    [80, 95, 110],
        "cooldown": [40, 32, 25],
        "damage":   [3,  5,  8],
        "bullet_speed": [2.0, 2.5, 3.0],
        "colors":   [C_PURPLE, C_PINK, C_WHITE],
        "shape":    "diamond",
    },
}

TOWER_KEYS = list(TOWER_DEFS.keys())  # ordre d'affichage

# ===========================================================
#  DÉFINITIONS DES ENNEMIS PAR TYPE
# ===========================================================
ENEMY_DEFS = {
    "grunt": {
        "label":  "Grunt",
        "hp":     3,
        "speed":  0.6,
        "reward": 10,
        "color":  C_RED,
        "size":   5,
    },
    "fast": {
        "label":  "Rapide",
        "hp":     2,
        "speed":  1.4,
        "reward": 15,
        "color":  C_YELLOW,
        "size":   4,
    },
    "tank": {
        "label":  "Tank",
        "hp":     12,
        "speed":  0.35,
        "reward": 30,
        "color":  C_DGRAY,
        "size":   8,
    },
    "boss": {
        "label":  "BOSS",
        "hp":     50,
        "speed":  0.25,
        "reward": 100,
        "color":  C_PURPLE,
        "size":   11,
    },
}

# ===========================================================
#  DONNÉES DE VAGUES
#  Chaque vague = liste de (type_ennemi, délai_avant_spawn)
# ===========================================================
WAVES = [
    # Wave 1 — introduction
    [("grunt",3),("grunt",60),("grunt",60),("grunt",90),("grunt",60)],
    # Wave 2 — rapides en renfort
    [("grunt",3),("fast",40),("grunt",50),("fast",40),("grunt",60),("fast",40)],
    # Wave 3 — premier tank
    [("grunt",3),("grunt",40),("tank",60),("grunt",40),("grunt",40)],
    # Wave 4 — assaut mixte
    [("fast",3),("fast",30),("tank",50),("grunt",40),("fast",30),("tank",80)],
    # Wave 5 — boss wave 1
    [("grunt",3),("fast",30),("grunt",40),("boss",80),("grunt",40),("fast",30)],
    # Wave 6 — double tanks
    [("tank",3),("fast",30),("tank",80),("fast",30),("grunt",40),("grunt",40),("tank",100)],
    # Wave 7 — enfer rapide
    [("fast",3),("fast",20),("fast",20),("fast",20),("tank",50),("boss",80),("fast",20)],
    # Wave 8 — finale ultime
    [("boss",3),("tank",60),("fast",30),("fast",30),("boss",100),("tank",60),("fast",20),("boss",120)],
]

# ===========================================================
#  PARTICULES
# ===========================================================
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=None):
        self.x     = x
        self.y     = y
        self.color = color
        self.vx    = vx if vx is not None else random.uniform(-1.5, 1.5)
        self.vy    = vy if vy is not None else random.uniform(-2.0, 0.0)
        self.life  = life if life is not None else random.randint(10, 22)
        self.alive = True

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.08   # gravité légère
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive and 0 <= self.x < W and 0 <= self.y < H:
            pyxel.pset(int(self.x), int(self.y), self.color)

# ===========================================================
#  TEXTE FLOTTANT (dégâts / or gagné)
# ===========================================================
class FloatText:
    def __init__(self, x, y, text, color):
        self.x     = x
        self.y     = y
        self.text  = text
        self.color = color
        self.life  = 40
        self.alive = True

    def update(self):
        self.y    -= 0.4
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive:
            alpha = max(0, self.life - 15)   # fade out progressif
            c = self.color if alpha > 0 else C_LGRAY
            pyxel.text(int(self.x), int(self.y), self.text, c)

# ===========================================================
#  BALLE
# ===========================================================
class Bullet:
    def __init__(self, x, y, target, damage, speed, color):
        self.x      = x
        self.y      = y
        self.target = target
        self.damage = damage
        self.speed  = speed
        self.color  = color
        self.alive  = True

    def update(self, particles, float_texts):
        if not self.target.alive:
            self.alive = False
            return

        dx   = self.target.x - self.x
        dy   = self.target.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist < 3:
            self.target.hp -= self.damage
            # Particules d'impact
            for _ in range(4):
                particles.append(Particle(self.x, self.y, self.color))
            # Texte flottant dégâts
            float_texts.append(FloatText(
                self.target.x - 4,
                self.target.y - 10,
                f"-{self.damage}",
                C_WHITE,
            ))
            if self.target.hp <= 0:
                self.target.alive = False
            self.alive = False
        else:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def draw(self):
        pyxel.circ(int(self.x), int(self.y), 2, self.color)

# ===========================================================
#  ENNEMI
# ===========================================================
class Enemy:
    def __init__(self, etype, path):
        d         = ENEMY_DEFS[etype]
        self.path  = path
        self.index = 0
        self.x, self.y = path[0]
        self.type  = etype
        self.hp    = d["hp"]
        self.max_hp= d["hp"]
        self.speed = d["speed"]
        self.reward= d["reward"]
        self.color = d["color"]
        self.size  = d["size"]
        self.alive = True
        self.reached_end = False  # a-t-il atteint la base ?

    def update(self):
        if not self.alive:
            return

        if self.index < len(self.path) - 1:
            tx, ty = self.path[self.index + 1]
            dx = tx - self.x
            dy = ty - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 2:
                self.index += 1
            else:
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
        else:
            # Fin du chemin → dégâts au joueur
            self.alive       = True   # keep alive flag pour le game loop
            self.reached_end = True
            self.alive       = False  # retire de la liste après

    def draw(self):
        if not self.alive:
            return
        s = self.size
        # Corps
        pyxel.circ(int(self.x), int(self.y), s, self.color)
        # Bordure blanche si boss
        if self.type == "boss":
            pyxel.circb(int(self.x), int(self.y), s + 1, C_WHITE)
        # Barre de vie
        bar_w = s * 2
        bx    = int(self.x) - s
        by    = int(self.y) - s - 5
        ratio = max(0, self.hp / self.max_hp)
        pyxel.rect(bx, by, bar_w, 2, C_RED)
        pyxel.rect(bx, by, int(bar_w * ratio), 2, C_LGREEN)

# ===========================================================
#  TOUR
# ===========================================================
class Tower:
    def __init__(self, x, y, ttype):
        self.x      = x
        self.y      = y
        self.type   = ttype
        self.level  = 0          # 0 = niveau 1, 1 = niveau 2, 2 = niveau 3
        d           = TOWER_DEFS[ttype]
        self._sync()
        self.cooldown_timer = 0
        self.selected       = False

    def _sync(self):
        """Synchronise les stats selon le niveau actuel."""
        d = TOWER_DEFS[self.type]
        lv = self.level
        self.range       = d["range"][lv]
        self.cooldown    = d["cooldown"][lv]
        self.damage      = d["damage"][lv]
        self.bullet_spd  = d["bullet_speed"][lv]
        self.color       = d["colors"][lv]

    def upgrade_cost(self):
        """Retourne le coût de l'upgrade suivante, ou None si max."""
        if self.level >= 2:
            return None
        return TOWER_DEFS[self.type]["cost"][self.level + 1]

    def upgrade(self):
        if self.level < 2:
            self.level += 1
            self._sync()

    def sell_value(self):
        d    = TOWER_DEFS[self.type]
        total= sum(d["cost"][:self.level + 1])
        return total // 2

    def update(self, enemies, bullets, particles, float_texts):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if self.cooldown_timer == 0:
            # Cibler l'ennemi le plus avancé dans portée
            best  = None
            best_progress = -1
            for e in enemies:
                if not e.alive:
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
                bullets.append(Bullet(
                    self.x, self.y, best,
                    self.damage, self.bullet_spd, self.color,
                ))
                self.cooldown_timer = self.cooldown

    def draw(self):
        d     = TOWER_DEFS[self.type]
        shape = d["shape"]
        s     = 6
        x, y  = int(self.x), int(self.y)
        c     = self.color

        # Socle
        pyxel.rect(x - s - 1, y - s - 1, (s+1)*2, (s+1)*2, C_BROWN)

        if shape == "circle":
            pyxel.circ(x, y, s, c)
            pyxel.circb(x, y, s, C_WHITE)
        elif shape == "square":
            pyxel.rect(x - s, y - s, s*2, s*2, c)
            pyxel.rectb(x - s, y - s, s*2, s*2, C_WHITE)
        elif shape == "diamond":
            pyxel.tri(x, y - s, x + s, y, x, y + s, c)
            pyxel.tri(x, y - s, x - s, y, x, y + s, c)

        # Numéro de niveau
        lv_str = ["I", "II", "III"][self.level]
        pyxel.text(x - 2, y - 2, lv_str, C_BLACK)

        # Anneau de sélection + portée
        if self.selected:
            pyxel.circb(x, y, self.range, C_LGRAY)
            pyxel.circb(x, y, s + 2, C_YELLOW)

# ===========================================================
#  GESTIONNAIRE DE VAGUES
# ===========================================================
class WaveManager:
    def __init__(self, path):
        self.path       = path
        self.wave_index = 0        # vague courante (0-based)
        self.queue      = []       # liste de (delay, etype) restants
        self.timer      = 0
        self.active     = False    # vague en cours ?
        self.all_done   = False    # toutes les vagues finies
        self.between_delay = 180   # 6 s entre vagues (30fps)
        self.between_timer = 0
        self.waiting    = False    # entre deux vagues

    def start_next_wave(self):
        if self.wave_index >= len(WAVES):
            self.all_done = True
            return
        self.queue  = list(WAVES[self.wave_index])
        self.timer  = 0
        self.active = True
        self.wave_index += 1

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
            # Vague terminée en spawn — attendre que tous les ennemis soient morts
            if not any(e.alive for e in enemies):
                self.active        = False
                self.waiting       = True
                self.between_timer = self.between_delay

    @property
    def current_wave(self):
        return self.wave_index  # après start_next_wave, correspond à la vague jouée

    def time_to_next(self):
        """Secondes avant la prochaine vague (pendant attente)."""
        return max(0, self.between_timer // FPS)

# ===========================================================
#  HUD
# ===========================================================
def draw_hud(hp, max_hp, gold, wave, total_waves, score,
             selected_type, selected_tower, wave_mgr):
    # Bande noire en haut
    pyxel.rect(0, 0, W, 14, C_BLACK)

    # HP
    pyxel.text(3, 3, f"HP:", C_WHITE)
    bar_w = 40
    ratio = max(0, hp / max_hp)
    pyxel.rect(17, 3, bar_w, 6, C_RED)
    pyxel.rect(17, 3, int(bar_w * ratio), 6, C_LGREEN)
    pyxel.text(59, 3, f"{hp}", C_WHITE)

    # Or
    pyxel.text(80, 3, f"Or:{gold}", C_YELLOW)

    # Vague
    wave_txt = f"Vague:{wave}/{total_waves}"
    pyxel.text(140, 3, wave_txt, C_ORANGE)

    # Score
    score_txt = f"Sc:{score}"
    pyxel.text(200, 3, score_txt, C_LBLUE)

    # Bandeau bas : panneau de contrôle
    pyxel.rect(0, H - 26, W, 26, C_BLACK)

    # Touches raccourcis
    labels = [
        ("1:Archer", 2,  C_LGREEN),
        ("2:Katana",  60, C_RED),
        ("3:Tamiko", 118, C_PINK),
        ("U:Upgrade", 174, C_YELLOW),
        ("V:Vendre",  224, C_ORANGE),
    ]
    for txt, x, c in labels:
        pyxel.text(x, H - 22, txt, c)

    # Tour sélectionnée
    if selected_type:
        d    = TOWER_DEFS[selected_type]
        cost = d["cost"][0]
        pyxel.text(2, H - 12, f">> {d['label']} cout:{cost}or", C_WHITE)

    # Info tour cliquée
    if selected_tower:
        t  = selected_tower
        uc = t.upgrade_cost()
        sv = t.sell_value()
        d  = TOWER_DEFS[t.type]
        info = f"{d['label']} Lv{t.level+1} | Up:{uc or 'MAX'} | Vend:{sv}"
        pyxel.text(2, H - 12, info, C_BGRAY)

    # Compte à rebours entre vagues
    if wave_mgr.waiting:
        s   = wave_mgr.time_to_next()
        msg = f"Prochaine vague dans {s}s..."
        pyxel.text(W//2 - len(msg)*2, H//2 - 4, msg, C_WHITE)

    if wave_mgr.all_done and not any_enemies_alive:
        pass  # géré dans draw_victory

# ===========================================================
#  ÉCRANS
# ===========================================================
def draw_game_over(score):
    pyxel.rect(40, 80, 176, 90, C_BLACK)
    pyxel.rectb(40, 80, 176, 90, C_RED)
    pyxel.text(88, 90,  "GAME OVER", C_RED)
    pyxel.text(70, 105, "Le japon est tombe...", C_WHITE)
    pyxel.text(65, 120, f"Score final : {score}", C_YELLOW)
    pyxel.text(70, 140, "ENTER = Rejouer", C_LGRAY)
    pyxel.text(75, 150, "ESC   = Quitter", C_LGRAY)

def draw_victory(score):
    pyxel.rect(30, 75, 196, 100, C_BLACK)
    pyxel.rectb(30, 75, 196, 100, C_YELLOW)
    pyxel.text(85, 85,  "VICTOIRE !", C_YELLOW)
    pyxel.text(60, 100, "Le Japon est protege !", C_LGREEN)
    pyxel.text(65, 115, f"Score final : {score}", C_WHITE)
    if score > 0:
        stars = "★" * min(3, score // 500 + 1)
        pyxel.text(110, 130, stars, C_ORANGE)
    pyxel.text(70, 148, "ENTER = Rejouer", C_LGRAY)
    pyxel.text(75, 158, "ESC   = Quitter", C_LGRAY)

# ===========================================================
#  UTILITAIRES
# ===========================================================
def point_near_path(px, py, path, min_dist=14):
    """Vérifie si un point est trop proche du chemin ennemi."""
    for i in range(len(path) - 1):
        ax, ay = path[i]
        bx, by = path[i+1]
        # Projection sur segment
        dx, dy = bx - ax, by - ay
        seg_len2 = dx*dx + dy*dy
        if seg_len2 == 0:
            t = 0.0
        else:
            t = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / seg_len2))
        cx = ax + t*dx
        cy = ay + t*dy
        dist = math.sqrt((px-cx)**2 + (py-cy)**2)
        if dist < min_dist:
            return True
    return False

# ===========================================================
#  CLASSE PRINCIPALE
# ===========================================================
any_enemies_alive = False  # variable globale pour draw_game_over

class Game:
    # ── États du jeu ──────────────────────────────────────
    STATE_PLAYING   = "playing"
    STATE_GAME_OVER = "game_over"
    STATE_VICTORY   = "victory"
    STATE_PAUSED    = "paused"

    def __init__(self):
        pyxel.init(W, H, title="JapanTahan", fps=FPS)

        # Charger la map dans l'image 0 du gestionnaire pyxel
        pyxel.images[0].load(0, 0, "assets/map_small.png")

        pyxel.mouse(True)
        self.reset()
        pyxel.run(self.update, self.draw)

    # ── Réinitialisation complète ──────────────────────────
    def reset(self):
        self.hp          = STARTING_HP
        self.max_hp      = STARTING_HP
        self.gold        = STARTING_GOLD
        self.score       = 0
        self.state       = self.STATE_PLAYING

        self.enemies     = []
        self.towers      = []
        self.bullets     = []
        self.particles   = []
        self.float_texts = []

        self.wave_mgr    = WaveManager(PATH)
        self.wave_mgr.start_next_wave()

        # Sélection
        self.selected_type  = "archer"   # type de tour à poser
        self.selected_tower = None       # tour cliquée sur la carte
        self.preview_x      = -999
        self.preview_y      = -999

        # Pouvoir spécial Samurai (ultime)
        self.ultimate_ready = True
        self.ultimate_cd    = 0
        self.ultimate_max   = FPS * 30   # 30 secondes
        self.ultimate_fx    = 0          # frames d'effet visuel

    # ── Mise à jour ────────────────────────────────────────
    def update(self):
        global any_enemies_alive

        mx, my = pyxel.mouse_x, pyxel.mouse_y

        # Gestion des états
        if self.state == self.STATE_GAME_OVER or self.state == self.STATE_VICTORY:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                pyxel.quit()
            return

        if self.state == self.STATE_PAUSED:
            if pyxel.btnp(pyxel.KEY_P):
                self.state = self.STATE_PLAYING
            return

        # Pause
        if pyxel.btnp(pyxel.KEY_P):
            self.state = self.STATE_PAUSED
            return

        # ── Sélection du type de tour ─────────────────────
        if pyxel.btnp(pyxel.KEY_1):
            self.selected_type  = "archer"
            self.selected_tower = None
        if pyxel.btnp(pyxel.KEY_2):
            self.selected_type  = "katana"
            self.selected_tower = None
        if pyxel.btnp(pyxel.KEY_3):
            self.selected_type  = "tamiko"
            self.selected_tower = None

        # ── Upgrade tour sélectionnée ─────────────────────
        if pyxel.btnp(pyxel.KEY_U) and self.selected_tower:
            t  = self.selected_tower
            uc = t.upgrade_cost()
            if uc and self.gold >= uc:
                self.gold -= uc
                t.upgrade()
                self.score += 5

        # ── Vendre tour sélectionnée ──────────────────────
        if pyxel.btnp(pyxel.KEY_V) and self.selected_tower:
            t  = self.selected_tower
            sv = t.sell_value()
            self.gold += sv
            self.towers.remove(t)
            self.selected_tower = None

        # ── Pouvoir spécial (ESPACE) ──────────────────────
        if pyxel.btnp(pyxel.KEY_SPACE):
            if self.ultimate_ready:
                self._use_ultimate()

        # Recharge ultime
        if not self.ultimate_ready:
            self.ultimate_cd += 1
            if self.ultimate_cd >= self.ultimate_max:
                self.ultimate_ready = True
                self.ultimate_cd    = 0

        # ── Clic gauche ───────────────────────────────────
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # Vérifier si clic sur une tour existante
            clicked_tower = self._tower_at(mx, my)
            if clicked_tower:
                # Désélectionner si déjà sélectionné
                if self.selected_tower == clicked_tower:
                    clicked_tower.selected = False
                    self.selected_tower    = None
                else:
                    if self.selected_tower:
                        self.selected_tower.selected = False
                    self.selected_tower         = clicked_tower
                    clicked_tower.selected      = True
            else:
                # Zone HUD invalide
                if my < 14 or my > H - 26:
                    pass
                elif point_near_path(mx, my, PATH):
                    # Flash rouge : zone interdite
                    self.particles += [
                        Particle(mx, my, C_RED,
                                 random.uniform(-1, 1),
                                 random.uniform(-1, 1), 12)
                        for _ in range(6)
                    ]
                else:
                    cost = TOWER_DEFS[self.selected_type]["cost"][0]
                    if self.gold >= cost:
                        # Désélectionner ancienne tour
                        if self.selected_tower:
                            self.selected_tower.selected = False
                            self.selected_tower = None
                        self.gold -= cost
                        self.towers.append(Tower(mx, my, self.selected_type))
                    else:
                        # Flash jaune : pas assez d'or
                        self.float_texts.append(
                            FloatText(mx - 10, my - 6, "Pas assez d'or!", C_YELLOW)
                        )

        # ── Clic droit = désélection ──────────────────────
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            if self.selected_tower:
                self.selected_tower.selected = False
                self.selected_tower = None

        # ── Position prévisualisation ─────────────────────
        self.preview_x = mx
        self.preview_y = my

        # ── Mise à jour vague ─────────────────────────────
        self.wave_mgr.update(self.enemies)

        # ── Mise à jour ennemis ───────────────────────────
        enemies_to_remove = []
        for e in self.enemies:
            e.update()
            if e.reached_end and not e.alive:
                # Dégâts au joueur
                dmg = {"grunt":1,"fast":1,"tank":3,"boss":6}[e.type]
                self.hp -= dmg
                self.float_texts.append(
                    FloatText(W//2 - 10, H//2 - 20, f"-{dmg} HP!", C_RED)
                )
                # Particules rouges
                for _ in range(8):
                    self.particles.append(
                        Particle(PATH[-1][0], PATH[-1][1] - 10, C_RED)
                    )
                enemies_to_remove.append(e)
            elif not e.alive:
                # Tué → récompense
                self.gold  += e.reward
                self.score += e.reward * 2
                # Particules or
                for _ in range(5):
                    self.particles.append(
                        Particle(int(e.x), int(e.y), C_YELLOW)
                    )
                self.float_texts.append(
                    FloatText(int(e.x) - 6, int(e.y) - 12,
                              f"+{e.reward}or", C_YELLOW)
                )
                enemies_to_remove.append(e)

        for e in enemies_to_remove:
            if e in self.enemies:
                self.enemies.remove(e)

        any_enemies_alive = any(en.alive for en in self.enemies)

        # ── Check game over ───────────────────────────────
        if self.hp <= 0:
            self.hp    = 0
            self.state = self.STATE_GAME_OVER
            return

        # ── Check victoire ────────────────────────────────
        if self.wave_mgr.all_done and not any_enemies_alive:
            self.state  = self.STATE_VICTORY
            self.score += 500  # bonus victoire
            return

        # ── Mise à jour tours ─────────────────────────────
        for t in self.towers:
            t.update(self.enemies, self.bullets, self.particles, self.float_texts)

        # ── Mise à jour balles ────────────────────────────
        self.bullets     = [b for b in self.bullets     if b.alive]
        for b in list(self.bullets):
            if b.alive:
                b.update(self.particles, self.float_texts)
        self.bullets = [b for b in self.bullets if b.alive]

        # ── Particules & textes flottants ─────────────────
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for ft in self.float_texts:
            ft.update()
        self.float_texts = [ft for ft in self.float_texts if ft.alive]

        # FX ultime
        if self.ultimate_fx > 0:
            self.ultimate_fx -= 1

    # ── Pouvoir spécial ────────────────────────────────────
    def _use_ultimate(self):
        """Samurai Fury : inflige 5 dégâts à tous les ennemis visibles."""
        self.ultimate_ready = False
        self.ultimate_cd    = 0
        self.ultimate_fx    = 20   # frames d'effet flash
        for e in self.enemies:
            if e.alive:
                e.hp -= 5
                if e.hp <= 0:
                    e.alive = False
                    self.gold  += e.reward
                    self.score += e.reward * 2
                # Particules rouges massives
                for _ in range(8):
                    self.particles.append(Particle(int(e.x), int(e.y), C_RED))

    # ── Trouver tour à position ────────────────────────────
    def _tower_at(self, mx, my):
        for t in self.towers:
            if abs(t.x - mx) < 10 and abs(t.y - my) < 10:
                return t
        return None

    # ── Dessin ─────────────────────────────────────────────
    def draw(self):
        pyxel.cls(C_BLACK)

        # ── Carte de fond ─────────────────────────────────
        pyxel.blt(0, 0, 0, 0, 0, W, H)

        # ── Effet ultime (flash rouge) ────────────────────
        if self.ultimate_fx > 0:
            # Dessiner un overlay rouge semi-transparent (approx.)
            c = C_RED if (self.ultimate_fx % 4 < 2) else C_ORANGE
            pyxel.rectb(1, 15, W - 2, H - 42, c)
            pyxel.rectb(2, 16, W - 4, H - 44, c)

        # ── Prévisualisation de pose ───────────────────────
        px, py = self.preview_x, self.preview_y
        if 14 < py < H - 26 and not self._tower_at(px, py):
            cost = TOWER_DEFS[self.selected_type]["cost"][0]
            ok   = self.gold >= cost and not point_near_path(px, py, PATH)
            c    = C_LGREEN if ok else C_RED
            pyxel.circb(px, py, 7, c)

        # ── Tours ─────────────────────────────────────────
        for t in self.towers:
            t.draw()

        # ── Ennemis ───────────────────────────────────────
        for e in self.enemies:
            e.draw()

        # ── Balles ────────────────────────────────────────
        for b in self.bullets:
            b.draw()

        # ── Particules ────────────────────────────────────
        for p in self.particles:
            p.draw()

        # ── Textes flottants ──────────────────────────────
        for ft in self.float_texts:
            ft.draw()

        # ── Indicateur ultime (bas droite du HUD) ─────────
        self._draw_ultimate_bar()

        # ── HUD ───────────────────────────────────────────
        draw_hud(
            self.hp, self.max_hp,
            self.gold,
            self.wave_mgr.current_wave,
            len(WAVES),
            self.score,
            self.selected_type if not self.selected_tower else None,
            self.selected_tower,
            self.wave_mgr,
        )

        # ── Pause ─────────────────────────────────────────
        if self.state == self.STATE_PAUSED:
            pyxel.rect(80, 110, 96, 30, C_BLACK)
            pyxel.rectb(80, 110, 96, 30, C_WHITE)
            pyxel.text(106, 122, "PAUSE (P)", C_WHITE)

        # ── Game Over / Victoire ───────────────────────────
        if self.state == self.STATE_GAME_OVER:
            draw_game_over(self.score)
        elif self.state == self.STATE_VICTORY:
            draw_victory(self.score)

    def _draw_ultimate_bar(self):
        """Barre de rechargement du pouvoir spécial."""
        bw   = 40
        bh   = 5
        bx   = W - bw - 2
        by   = H - 24
        # Fond
        pyxel.rect(bx, by, bw, bh, C_DGRAY)
        if self.ultimate_ready:
            pyxel.rect(bx, by, bw, bh, C_YELLOW)
            pyxel.text(bx - 14, by - 1, "SPC", C_YELLOW)
        else:
            ratio = self.ultimate_cd / self.ultimate_max
            pyxel.rect(bx, by, int(bw * ratio), bh, C_ORANGE)
        pyxel.rectb(bx, by, bw, bh, C_WHITE)
        pyxel.text(bx + 4, by - 8, "FURY", C_ORANGE)

# ===========================================================
#  POINT D'ENTRÉE
# ===========================================================
Game()
