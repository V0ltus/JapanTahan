import pyxel

MENU = 0
GAME = 1

class JapanTahan:

    def __init__(self):

        pyxel.init(320, 240, title="JapanTahan")

        # Charge les ressources
        pyxel.load("theme.pyxres")

        self.scene = MENU

        # Bouton Play
        self.button_x = 110
        self.button_y = 180
        self.button_w = 100
        self.button_h = 30

        pyxel.run(self.update, self.draw)

    def update(self):

        # MENU
        if self.scene == MENU:

            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):

                mx = pyxel.mouse_x
                my = pyxel.mouse_y

                # Vérifie clic bouton
                if (
                    self.button_x <= mx <= self.button_x + self.button_w
                    and
                    self.button_y <= my <= self.button_y + self.button_h
                ):
                    self.scene = GAME

    def draw(self):

        pyxel.cls(0)

        # ===== MENU =====
        if self.scene == MENU:

            # Logo
            pyxel.blt(85, 30, 0, 0, 0, 150, 120)

            # Nom du jeu
            pyxel.text(120, 155, "JAPANTAHAN", 7)

            # Bouton PLAY
            pyxel.rect(
                self.button_x,
                self.button_y,
                self.button_w,
                self.button_h,
                11
            )

            pyxel.text(145, 192, "PLAY", 0)

        # ===== GAME =====
        elif self.scene == GAME:

            pyxel.text(120, 120, "GAME STARTED", 7)

JapanTahan()
