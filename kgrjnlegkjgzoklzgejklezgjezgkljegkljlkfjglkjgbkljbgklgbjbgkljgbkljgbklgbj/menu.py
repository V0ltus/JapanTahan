import pyxel
import os
import subprocess
import sys
from PIL import Image

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =========================
# ASSETS
# =========================
if not os.path.exists("assets/fond_depart_small.jpg"):
    img = Image.open("assets/fond_depart.jpg")
    img = img.resize((256, 256))
    img.save("assets/fond_depart_small.jpg")


class Menu:
    def __init__(self):
        pyxel.init(256, 256, title="JapanTahan")

        # =========================
        # MUSIQUE JAPON ANCIEN
        # =========================
        pyxel.sound(0).set(
            "c3 c3 e3 g3 e3 c3 d3 c3",
            "t",
            "6",
            "n",
            30
        )

        pyxel.sound(1).set(
            "g2 g2 a2 g2 e2 d2 c2",
            "s",
            "4",
            "n",
            35
        )

        pyxel.music(0).set([0, 1], [], [], [])
        pyxel.playm(0, loop=True)

        self.music_on = True

        pyxel.images[1].load(0, 0, "assets/fond_depart_small.jpg")

        self.buttons = ["JOUER", "MUSIQUE ON/OFF"]
        self.selected = 0

        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    # =========================
    # UPDATE
    # =========================
    def update(self):
        mx, my = pyxel.mouse_x, pyxel.mouse_y

        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.buttons)

        if pyxel.btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.buttons)

        if pyxel.btnp(pyxel.KEY_RETURN):
            self.choose(self.selected)

        for i in range(len(self.buttons)):
            bx, by, bw, bh = self.get_button_rect(i)
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.selected = i
                if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                    self.choose(i)

    # =========================
    # ACTIONS
    # =========================
    def choose(self, i):
        if i == 0:
            print("Lancement du jeu...")

            # stop musique
            pyxel.stop()

            # lancer le jeu proprement
            subprocess.Popen([sys.executable, "jeux.py"])

            # fermer menu
            pyxel.quit()

        elif i == 1:
            self.toggle_music()

    def toggle_music(self):
        if self.music_on:
            pyxel.stop()
            self.music_on = False
        else:
            pyxel.playm(0, loop=True)
            self.music_on = True

    # =========================
    # BUTTONS
    # =========================
    def get_button_rect(self, i):
        bw, bh = 140, 20
        bx = (256 - bw) // 2
        by = 160 + i * 30
        return bx, by, bw, bh

    def draw_button(self, i, label):
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        bx, by, bw, bh = self.get_button_rect(i)

        hover = bx <= mx <= bx + bw and by <= my <= by + bh
        selected = (i == self.selected)

        color = 10 if selected else (9 if hover else 7)

        pyxel.rect(bx, by, bw, bh, color)
        pyxel.rectb(bx, by, bw, bh, 0)

        txt = label
        if i == 1:
            txt = "MUSIQUE : ON" if self.music_on else "MUSIQUE : OFF"

        tx = bx + (bw - len(txt) * 4) // 2
        ty = by + 6
        pyxel.text(tx, ty, txt, 0)

    # =========================
    # TITRE
    # =========================
    def draw_title(self):
        title = "JAPAN TAHAN"
        x = (256 - len(title) * 4) // 2

        pyxel.rect(x - 10, 60, len(title) * 4 + 20, 20, 0)
        pyxel.rectb(x - 10, 60, len(title) * 4 + 20, 20, 8)

        pyxel.text(x, 68, title, 7)

    # =========================
    # DRAW
    # =========================
    def draw(self):
        pyxel.cls(0)

        pyxel.blt(0, 0, 1, 0, 0, 256, 256)

        self.draw_title()

        for i, label in enumerate(self.buttons):
            self.draw_button(i, label)


Menu()