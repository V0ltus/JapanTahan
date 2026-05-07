import pyxel
import os
import math

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# =========================
# ENNEMI (SPRITE)
# =========================
class Enemy:
    def __init__(self, path):
        self.path = path
        self.index = 0
        self.x, self.y = path[0]
        self.speed = 0.6
        self.hp = 3
        self.alive = True

    def update(self):
        if not self.alive:
            return

        if self.index < len(self.path) - 1:
            tx, ty = self.path[self.index + 1]

            dx = tx - self.x
            dy = ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 2:
                self.index += 1
            else:
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
        else:
            self.alive = False

    def draw(self):
        if self.alive:
            # sprite dans theme.pyxres
            pyxel.blt(self.x - 8, self.y - 8, 0, 0, 0, 16, 16)


# =========================
# TOUR
# =========================
class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 50
        self.cooldown = 0

    def update(self, enemies, bullets):
        if self.cooldown > 0:
            self.cooldown -= 1

        if self.cooldown == 0:
            for e in enemies:
                if e.alive:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < self.range:
                        bullets.append(Bullet(self.x, self.y, e))
                        self.cooldown = 25
                        break

    def draw(self):
        pyxel.rect(self.x - 4, self.y - 4, 8, 8, 9)


# =========================
# BALLE
# =========================
class Bullet:
    def __init__(self, x, y, target):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 2
        self.alive = True

    def update(self):
        if not self.target.alive:
            self.alive = False
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 2:
            self.target.hp -= 1
            if self.target.hp <= 0:
                self.target.alive = False
            self.alive = False
        else:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def draw(self):
        pyxel.circ(self.x, self.y, 2, 7)


# =========================
# GAME
# =========================
class Game:
    def __init__(self):
        pyxel.init(256, 256, title="JapanTahan")

        # =========================
        # MAP PNG (IMPORTANT)
        # =========================
        pyxel.images[0].load(0, 0, "assets/map_small.png")

        # =========================
        # SPRITES
        # =========================
        pyxel.load("assets/theme.pyxres")

        # =========================
        # CHEMIN
        # =========================
        self.path = [
            (45, 25),
            (45, 70),
            (127, 70),
            (127, 120),
            (190, 120),
            (190, 195),
            (210, 195),
            (210, 256)
        ]

        self.enemies = [Enemy(self.path)]
        self.towers = []
        self.bullets = []

        self.spawn_timer = 0

        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    # =========================
    # UPDATE
    # =========================
    def update(self):
        self.spawn_timer += 1

        if self.spawn_timer > 120:
            self.enemies.append(Enemy(self.path))
            self.spawn_timer = 0

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.towers.append(Tower(pyxel.mouse_x, pyxel.mouse_y))

        for e in self.enemies:
            e.update()

        for t in self.towers:
            t.update(self.enemies, self.bullets)

        for b in self.bullets:
            b.update()

        self.enemies = [e for e in self.enemies if e.alive]
        self.bullets = [b for b in self.bullets if b.alive]

    # =========================
    # DRAW
    # =========================
    def draw(self):
        pyxel.cls(0)

        # =========================
        # MAP (FIX FINAL QUI MARCHE)
        # =========================
        pyxel.blt(0, 0, 0, 0, 0, 256, 256)

        for e in self.enemies:
            e.draw()

        for t in self.towers:
            t.draw()

        for b in self.bullets:
            b.draw()


Game()