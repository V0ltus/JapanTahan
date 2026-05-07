import pyxel
import os
import math

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# =========================
# ENNEMI
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
            pyxel.circ(self.x, self.y, 5, 8)


# =========================
# TOUR (grille simple)
# =========================
class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 60
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
# GAME PRINCIPAL
# =========================
class App:
    def __init__(self):
        pyxel.init(256, 256, title="JapanTahan")

        # MAP
        pyxel.images[0].load(0, 0, "assets/map_small.png")

        # MUSIQUE MENU
        pyxel.sound(0).set("c3 e3 g3 e3 c3", "t", "6", "n", 30)
        pyxel.sound(1).set("g2 a2 g2 e2", "s", "4", "n", 40)
        pyxel.music(0).set([0, 1], [], [], [])

        self.state = "menu"
        self.music_on = True

        # GAME DATA
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

        self.enemies = []
        self.towers = []
        self.bullets = []

        self.spawn_timer = 0

        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    # =========================
    # UPDATE
    # =========================
    def update(self):
        if self.state == "menu":
            self.update_menu()
        else:
            self.update_game()

    # =========================
    # MENU
    # =========================
    def update_menu(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.start_game()

    def start_game(self):
        self.state = "game"
        pyxel.playm(0, loop=True)

    # =========================
    # GAME
    # =========================
    def update_game(self):
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

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()

    def draw_menu(self):
        pyxel.text(90, 120, "CLICK TO PLAY", 7)

    def draw_game(self):
        pyxel.blt(0, 0, 0, 0, 0, 256, 256)

        for e in self.enemies:
            e.draw()

        for t in self.towers:
            t.draw()

        for b in self.bullets:
            b.draw()


App()