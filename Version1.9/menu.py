import pyxel
import os
import subprocess
import sys
import math
import random
from PIL import Image

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===========================================================
#  CONSTANTES
# ===========================================================
W, H = 256, 256
FPS  = 30

# Palette pyxel
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

# Image banks pyxel
IMG_BG   = 0   # fond_depart_small.jpg  (256x256)
IMG_LOGO = 1   # logo centré            (256x256)

# ===========================================================
#  PRÉPARATION DES ASSETS (une seule fois)
# ===========================================================
def prepare_assets():
    """Redimensionne et prépare les images si nécessaire."""
    os.makedirs("assets", exist_ok=True)

    # --- Fond de départ ---
    src_bg = "assets/fond_depart.jpg"
    dst_bg = "assets/fond_depart_small.jpg"
    if not os.path.exists(dst_bg) and os.path.exists(src_bg):
        img = Image.open(src_bg).convert("RGB").resize((256, 256), Image.LANCZOS)
        img.save(dst_bg, quality=95)
        print(f"[assets] fond redimensionné → {dst_bg}")

    # --- Logo (110x110 centré dans 256x256) ---
    dst_logo = "assets/logo_menu.png"
    src_logo = "assets/logo.png"
    if not os.path.exists(dst_logo) and os.path.exists(src_logo):
        logo   = Image.open(src_logo).convert("RGB")
        logo   = logo.resize((110, 110), Image.LANCZOS)
        canvas = Image.new("RGB", (256, 256), (0, 0, 0))
        canvas.paste(logo, (73, 0))
        canvas.save(dst_logo)
        print(f"[assets] logo créé → {dst_logo}")

prepare_assets()

# ===========================================================
#  PARTICULE SAKURA
# ===========================================================
class Sakura:
    """Pétale de cerisier animé en arrière-plan."""
    def __init__(self, x=None, y=None):
        self.reset(x, y)

    def reset(self, x=None, y=None):
        self.x     = x if x is not None else random.randint(0, W)
        self.y     = y if y is not None else random.randint(-10, H)
        self.vx    = random.uniform(-0.4, 0.2)
        self.vy    = random.uniform(0.3, 0.9)
        self.angle = random.uniform(0, math.pi * 2)
        self.dangle= random.uniform(-0.05, 0.05)
        self.size  = random.choice([1, 1, 2])
        self.color = random.choice([C_PINK, C_PEACH, C_WHITE, C_PINK])
        self.life  = random.randint(120, 400)

    def update(self):
        self.x     += self.vx + math.sin(self.angle) * 0.3
        self.y     += self.vy
        self.angle += self.dangle
        self.life  -= 1
        if self.life <= 0 or self.y > H + 4:
            self.reset(x=random.randint(0, W), y=-4)

    def draw(self):
        ix, iy = int(self.x), int(self.y)
        if self.size == 1:
            pyxel.pset(ix, iy, self.color)
        else:
            pyxel.circ(ix, iy, 1, self.color)

# ===========================================================
#  PARTICULE D'ÉTINCELLE (sur le logo)
# ===========================================================
class Spark:
    def __init__(self):
        self.reset()

    def reset(self):
        angle    = random.uniform(0, math.pi * 2)
        speed    = random.uniform(0.5, 2.0)
        self.x   = W // 2 + math.cos(angle) * random.randint(30, 55)
        self.y   = 55      + math.sin(angle) * random.randint(20, 55)
        self.vx  = math.cos(angle) * speed * 0.3 + random.uniform(-0.3, 0.3)
        self.vy  = -random.uniform(0.5, 1.5)
        self.life= random.randint(15, 35)
        self.color = random.choice([C_YELLOW, C_ORANGE, C_RED, C_WHITE])
        self.alive = True

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.06
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self):
        if self.alive:
            pyxel.pset(int(self.x), int(self.y), self.color)

# ===========================================================
#  HELPER : dessiner un bouton stylé
# ===========================================================
def draw_fancy_button(bx, by, bw, bh, label, selected, hovered):
    """
    Dessine un bouton avec bordure rouge style japonais.
    selected  → surbrillance principale
    hovered   → surbrillance survol
    """
    # Ombre portée
    pyxel.rect(bx + 2, by + 2, bw, bh, C_BLACK)

    # Fond
    if selected:
        pyxel.rect(bx, by, bw, bh, C_RED)
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

    # Coins dorés (décoration japonaise)
    for cx, cy in [(bx, by), (bx + bw - 3, by),
                   (bx, by + bh - 3), (bx + bw - 3, by + bh - 3)]:
        pyxel.rect(cx, cy, 3, 3, C_YELLOW if selected else border_c)

    # Texte centré
    tx = bx + (bw - len(label) * 4) // 2
    ty = by + (bh - 5) // 2
    pyxel.text(tx, ty, label, text_c)

# ===========================================================
#  ÉCRAN INSTRUCTIONS
# ===========================================================
class ScreenInstructions:
    def __init__(self):
        self.scroll = 0

    def update(self):
        self.scroll += 1
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN) \
                or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return "menu"
        return "instructions"

    def draw(self):
        # Fond noir semi-transparent
        pyxel.rect(10, 8, W - 20, H - 16, C_BLACK)
        pyxel.rectb(10, 8, W - 20, H - 16, C_RED)
        # Coins
        for cx, cy in [(10,8),(W-13,8),(10,H-11),(W-13,H-11)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW)

        pyxel.text(70, 14, "INSTRUCTIONS", C_YELLOW)
        pyxel.rect(20, 22, W - 40, 1, C_RED)

        lines = [
            ("TOURS", C_ORANGE),
            ("1 = Archer   cout:50or  portee:55", C_LGREEN),
            ("  Rapide, longue portee, dommages:1", C_LGRAY),
            ("2 = Katana   cout:80or  portee:35", C_RED),
            ("  Tres rapide, courte portee, dmg:2", C_LGRAY),
            ("3 = Tamiko   cout:120or portee:80", C_PINK),
            ("  Lente, enorme portee, dommages:3", C_LGRAY),
            ("", C_BLACK),
            ("ENNEMIS", C_ORANGE),
            ("Grunt  HP:3  vitesse:norm  recomp:10", C_WHITE),
            ("Rapide HP:2  vitesse:rapide recomp:15", C_YELLOW),
            ("Tank   HP:12 vitesse:lente recomp:30", C_LGRAY),
            ("BOSS   HP:50 vitesse:lente recomp:100", C_PURPLE),
            ("", C_BLACK),
            ("CONTROLES", C_ORANGE),
            ("Clic G  = poser une tour", C_WHITE),
            ("Clic G  = selectionner tour", C_WHITE),
            ("U       = ameliorer tour (+or)", C_YELLOW),
            ("V       = vendre tour (50% valeur)", C_YELLOW),
            ("ESPACE  = Samurai Fury (tous -5HP)", C_RED),
            ("P       = Pause", C_LGRAY),
            ("", C_BLACK),
            ("RETOUR : ECHAP ou ENTREE", C_LGRAY),
        ]

        y = 28
        for txt, c in lines:
            if y > H - 14:
                break
            pyxel.text(16, y, txt, c)
            y += 9

# ===========================================================
#  ÉCRAN CRÉDITS
# ===========================================================
class ScreenCredits:
    def __init__(self):
        self.timer = 0

    def update(self):
        self.timer += 1
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN) \
                or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return "menu"
        return "credits"

    def draw(self):
        pyxel.rect(20, 20, W - 40, H - 40, C_BLACK)
        pyxel.rectb(20, 20, W - 40, H - 40, C_RED)
        for cx, cy in [(20,20),(W-23,20),(20,H-23),(W-23,H-23)]:
            pyxel.rect(cx, cy, 3, 3, C_YELLOW)

        pyxel.text(80, 28, "CREDITS", C_YELLOW)
        pyxel.rect(30, 37, W - 60, 1, C_RED)

        lines = [
            ("JapanTahan", C_ORANGE),
            ("Tower Defense Japonais", C_LGRAY),
            ("", C_BLACK),
            ("Conception & Code", C_WHITE),
            ("Equipe JapanTahan", C_LGREEN),
            ("", C_BLACK),
            ("Graphismes", C_WHITE),
            ("Assets IA + Pixel Art", C_LGREEN),
            ("", C_BLACK),
            ("Moteur", C_WHITE),
            ("Pyxel  v2.x  (Takashi Kitao)", C_LBLUE),
            ("", C_BLACK),
            ("Merci d avoir joue !", C_YELLOW),
            ("Protegez le Japon !", C_RED),
        ]

        y = 46
        for txt, c in lines:
            x = 28 + (W - 56 - len(txt) * 4) // 2
            pyxel.text(x, y, txt, c)
            y += 10

        # Animation torii bas
        t  = self.timer
        rx = W // 2
        ry = H - 32
        pyxel.rect(rx - 18, ry,      36, 3,  C_RED)   # barre haute
        pyxel.rect(rx - 14, ry + 3,  28, 2,  C_RED)   # barre basse
        pyxel.rect(rx - 16, ry + 5,   3, 12, C_RED)   # pilier gauche
        pyxel.rect(rx + 13, ry + 5,   3, 12, C_RED)   # pilier droit

        pyxel.text(60, H - 15, "RETOUR : ECHAP / ENTREE", C_DGRAY)

# ===========================================================
#  MENU PRINCIPAL
# ===========================================================
class Menu:

    # États internes
    STATE_MENU         = "menu"
    STATE_INSTRUCTIONS = "instructions"
    STATE_CREDITS      = "credits"
    STATE_LAUNCH       = "launch"

    BUTTONS = ["JOUER", "INSTRUCTIONS", "CREDITS", "QUITTER"]

    def __init__(self):
        pyxel.init(W, H, title="JapanTahan", fps=FPS)

        # ── Chargement images ─────────────────────────────
        pyxel.images[IMG_BG].load(0, 0, "assets/fond_depart_small.jpg")

        logo_path = "assets/logo_menu.png"
        if os.path.exists(logo_path):
            pyxel.images[IMG_LOGO].load(0, 0, logo_path)
            self.has_logo = True
        else:
            self.has_logo = False

        # ── Musique japonaise ─────────────────────────────
        self._setup_music()
        self.music_on = True

        # ── État ─────────────────────────────────────────
        self.state    = self.STATE_MENU
        self.selected = 0

        # ── Sous-écrans ───────────────────────────────────
        self.screen_instructions = ScreenInstructions()
        self.screen_credits      = ScreenCredits()

        # ── Animations ───────────────────────────────────
        self.timer       = 0
        self.sakuras     = [Sakura() for _ in range(30)]
        self.sparks      = []
        self.spark_timer = 0

        # Animation d'entrée logo
        self.logo_y      = -120     # commence hors écran (haut)
        self.logo_target = 0        # position finale
        self.logo_scale  = 0.0     # zoom-in
        self.intro_done  = False

        # Flash bouton JOUER
        self.play_flash  = 0

        # Clignotement "APPUYEZ SUR ENTREE"
        self.blink_timer = 0

        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    # ── Musique ───────────────────────────────────────────
    def _setup_music(self):
        # Mélodie pentatonique japonaise — canal 0
        pyxel.sound(0).set(
            "e3 r  g3 r  a3 r  g3 e3  "
            "d3 r  e3 r  g3 r  e3 r  ",
            "t",
            "55556666 55556666",
            "nnnnnnnn nnnnnnnn",
            20,
        )
        # Basse douce — canal 1
        pyxel.sound(1).set(
            "a2 r r r  e2 r r r  "
            "g2 r r r  d2 r r r  ",
            "s",
            "3333 3333 3333 3333",
            "nnnn nnnn nnnn nnnn",
            20,
        )
        # Percussions taiko légères — canal 2
        pyxel.sound(2).set(
            "a1 r r a1 r r a1 r  "
            "a1 r a1 r r a1 r r  ",
            "n",
            "7777 7777 7777 7777",
            "nnnn nnnn nnnn nnnn",
            20,
        )
        # Harmonie haute — canal 3
        pyxel.sound(3).set(
            "e4 r r  a4 r r  g4 r r  e4 r r  ",
            "p",
            "4444 4444",
            "nnnn nnnn",
            25,
        )
        pyxel.music(0).set([0], [1], [2], [3])
        pyxel.playm(0, loop=True)

    def _toggle_music(self):
        if self.music_on:
            pyxel.stop()
            self.music_on = False
        else:
            pyxel.playm(0, loop=True)
            self.music_on = True

    # ── Calculs boutons ───────────────────────────────────
    def _button_rect(self, i):
        bw, bh = 140, 18
        bx = (W - bw) // 2
        by = 164 + i * 24
        return bx, by, bw, bh

    def _hovered(self, i):
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        bx, by, bw, bh = self._button_rect(i)
        return bx <= mx <= bx + bw and by <= my <= by + bh

    # ── Update ────────────────────────────────────────────
    def update(self):
        self.timer += 1

        # ── Sous-écrans ───────────────────────────────────
        if self.state == self.STATE_INSTRUCTIONS:
            result = self.screen_instructions.update()
            if result == "menu":
                self.state = self.STATE_MENU
            return

        if self.state == self.STATE_CREDITS:
            result = self.screen_credits.update()
            if result == "menu":
                self.state = self.STATE_MENU
            return

        # ── Animation intro logo ──────────────────────────
        if not self.intro_done:
            self.logo_y     = int(self.logo_y + (self.logo_target - self.logo_y) * 0.12)
            self.logo_scale = min(1.0, self.logo_scale + 0.04)
            if abs(self.logo_y - self.logo_target) < 1 and self.logo_scale >= 0.99:
                self.intro_done = True

        # ── Pétales sakura ────────────────────────────────
        for s in self.sakuras:
            s.update()

        # ── Étincelles sur logo ───────────────────────────
        self.spark_timer += 1
        if self.spark_timer % 4 == 0:
            self.sparks.append(Spark())
        self.sparks = [sp for sp in self.sparks if sp.alive]
        for sp in self.sparks:
            sp.update()

        # ── Clignotement ──────────────────────────────────
        self.blink_timer = (self.blink_timer + 1) % 40

        # ── Flash bouton play ─────────────────────────────
        if self.play_flash > 0:
            self.play_flash -= 1
            if self.play_flash == 0:
                self._launch_game()
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
                    self._choose(i)

    # ── Actions ───────────────────────────────────────────
    def _choose(self, i):
        label = self.BUTTONS[i]
        if label == "JOUER":
            self.play_flash = 25   # flash d'animation avant lancement
        elif label == "INSTRUCTIONS":
            self.state = self.STATE_INSTRUCTIONS
        elif label == "CREDITS":
            self.state = self.STATE_CREDITS
        elif label == "QUITTER":
            pyxel.quit()

    def _launch_game(self):
        pyxel.stop()
        subprocess.Popen([sys.executable, "jeux.py"])
        pyxel.quit()

    # ── Draw ──────────────────────────────────────────────
    def draw(self):
        pyxel.cls(C_BLACK)

        # ── Fond ──────────────────────────────────────────
        pyxel.blt(0, 0, IMG_BG, 0, 0, W, H)

        # ── Overlay sombre pour lisibilité ────────────────
        self._draw_overlay()

        # ── Pétales sakura ────────────────────────────────
        for s in self.sakuras:
            s.draw()

        if self.state == self.STATE_INSTRUCTIONS:
            self.screen_instructions.draw()
            return

        if self.state == self.STATE_CREDITS:
            self.screen_credits.draw()
            return

        # ── Logo ──────────────────────────────────────────
        self._draw_logo()

        # ── Étincelles ────────────────────────────────────
        for sp in self.sparks:
            sp.draw()

        # ── Ligne décorative torii ────────────────────────
        self._draw_torii_deco()

        # ── Boutons ───────────────────────────────────────
        for i, label in enumerate(self.BUTTONS):
            self._draw_button(i, label)

        # ── Option musique (touche M) ─────────────────────
        music_txt = f"M: MUSIQUE {'ON ' if self.music_on else 'OFF'}"
        pyxel.text(W - len(music_txt) * 4 - 3, H - 8, music_txt,
                   C_LGREEN if self.music_on else C_DGRAY)

        # ── Version ───────────────────────────────────────
        pyxel.text(3, H - 8, "v1.0", C_DGRAY)

        # ── Flash JOUER ───────────────────────────────────
        if self.play_flash > 0:
            c = C_YELLOW if (self.play_flash % 6 < 3) else C_RED
            pyxel.rectb(0, 0, W, H, c)
            pyxel.rectb(1, 1, W - 2, H - 2, c)
            txt = "CHARGEMENT..."
            pyxel.text(W//2 - len(txt)*2, H//2, txt, C_WHITE)

    # ── Overlay dégradé sombre ────────────────────────────
    def _draw_overlay(self):
        # Bande sombre en bas pour les boutons
        for y in range(150, H):
            alpha = min(15, (y - 150) // 5)
            if (y // 2) % 2 == 0:
                pyxel.rect(0, y, W, 1, C_BLACK)

    # ── Logo animé ────────────────────────────────────────
    def _draw_logo(self):
        if not self.has_logo:
            # Fallback texte stylé
            self._draw_text_logo()
            return

        # Pulsation scale simulée via bordure
        t    = self.timer
        pulse= int(math.sin(t * 0.08) * 2)

        # Cadre lumineux autour du logo
        lx, ly = 73, self.logo_y
        lw, lh = 110, 110
        c_border = C_RED if (t % 30 < 15) else C_ORANGE

        # Ombre portée
        pyxel.rectb(lx + 2, ly + 2, lw, lh, C_BLACK)

        # Fond noir derrière le logo
        pyxel.rect(lx - 2, ly - 2, lw + 4, lh + 4, C_BLACK)

        # Logo
        pyxel.blt(lx, ly, IMG_LOGO, lx, ly, lw, lh)

        # Cadre décoratif
        pyxel.rectb(lx - 2 - pulse, ly - 2 - pulse,
                    lw + 4 + pulse*2, lh + 4 + pulse*2, c_border)
        pyxel.rectb(lx - 4 - pulse, ly - 4 - pulse,
                    lw + 8 + pulse*2, lh + 8 + pulse*2,
                    C_YELLOW if (t % 20 < 10) else C_BROWN)

        # Coins dorés
        sz = 5
        for cx, cy in [
            (lx - 4, ly - 4),
            (lx + lw - sz + 2, ly - 4),
            (lx - 4,            ly + lh - sz + 2),
            (lx + lw - sz + 2, ly + lh - sz + 2),
        ]:
            pyxel.rect(cx, cy, sz, sz, C_YELLOW)

    def _draw_text_logo(self):
        """Fallback si pas de logo PNG."""
        t   = self.timer
        glow= C_RED if (t % 20 < 10) else C_ORANGE

        title1 = "JAPAN"
        title2 = "TAHAN"
        x1 = W//2 - len(title1) * 4
        x2 = W//2 - len(title2) * 4 + 1

        pyxel.text(x1 + 1, 31, title1, C_BLACK)
        pyxel.text(x1,     30, title1, C_WHITE)
        pyxel.text(x2 + 1, 41, title2, C_BLACK)
        pyxel.text(x2,     40, title2, glow)

    # ── Décoration torii ──────────────────────────────────
    def _draw_torii_deco(self):
        """Mini-torii dessiné pixelart entre logo et boutons."""
        # Ligne rouge séparatrice style torii
        y  = 152
        cx = W // 2

        # Barre principale
        pyxel.rect(cx - 50, y,     100, 3, C_RED)
        # Barre secondaire
        pyxel.rect(cx - 40, y + 4,  80, 2, C_RED)
        # Piliers
        pyxel.rect(cx - 46, y + 6,   3, 8, C_RED)
        pyxel.rect(cx + 43, y + 6,   3, 8, C_RED)

        # Lanterns latérales (pixels)
        for lx in [cx - 56, cx + 52]:
            pyxel.rect(lx,     y - 2,  4, 6, C_ORANGE)
            pyxel.rect(lx + 1, y - 3,  2, 1, C_YELLOW)
            pyxel.rect(lx + 1, y + 4,  2, 2, C_RED)

    # ── Bouton stylé ──────────────────────────────────────
    def _draw_button(self, i, label):
        bx, by, bw, bh = self._button_rect(i)
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        hovered  = self._hovered(i)
        selected = (i == self.selected)

        # Label adapté musique
        display_label = label

        draw_fancy_button(bx, by, bw, bh, display_label, selected, hovered)

        # Curseur katana à gauche du bouton sélectionné
        if selected:
            t    = self.timer
            blink= (t // 8) % 2
            kx   = bx - 12
            ky   = by + bh // 2
            # Katana pixelart minimaliste
            pyxel.rect(kx,      ky - 1, 8, 3, C_LGRAY)   # lame
            pyxel.rect(kx + 7,  ky - 1, 2, 3, C_YELLOW)  # garde
            pyxel.rect(kx + 9,  ky,     3, 1, C_BROWN)   # poignée
            if blink:
                pyxel.pset(kx, ky, C_WHITE)               # reflet


# ===========================================================
#  POINT D'ENTRÉE
# ===========================================================
Menu()
