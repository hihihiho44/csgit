# main.py
import pygame
from pygame import Rect
import sys

WIDTH, HEIGHT = 960, 540
TITLE = "Pygame 2D Platformer"
FPS = 60
TILE = 48

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY = (135, 206, 235)
GREEN = (80, 160, 90)
RED = (220, 60, 60)
GOLD = (255, 200, 60)
UI = (30, 30, 30)

# Level layout (TILE-sized grid)
# Legend:
#   '#' = ground/block, 'P' = player spawn, 'E' = enemy, 'C' = coin, 'X' = spike
LEVEL = [
    "................................................................................",
    "................................................................................",
    ".........................C......................................................",
    ".......................#####....................................................",
    "..............................................C..................................",
    "............................................#####................................",
    "...............P................................................................",
    "##############################.................#########################.........",
    ".............................#........................................#.........",
    ".............................#.............C..........................#.........",
    ".............................#...........#####........................#.........",
    ".............................#........................................#.........",
    ".............................#........................................#.........",
    "..............C..............#..................E.....................#.........",
    "............#####............#........................................#.........",
    ".............................##############################...........#.........",
    "............................................................C.........#.........",
    "..........................................................#####.......#.........",
    ".................................E....................................#.........",
    "#######################################################################.........",
]

def grid_to_world(x, y):
    return x * TILE, y * TILE

class Camera:
    def __init__(self, width, height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height

    def follow(self, target_rect):
        self.offset.x = target_rect.centerx - WIDTH // 2
        self.offset.y = target_rect.centery - HEIGHT // 2

    def apply(self, rect):
        return Rect(rect.x - self.offset.x, rect.y - self.offset.y, rect.width, rect.height)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((TILE * 0.7, TILE * 0.9))
        self.image.fill((40, 100, 220))
        self.rect = self.image.get_rect(topleft=pos)

        # Physics
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.speed = 6
        self.jump_speed = -14
        self.gravity = 0.7
        self.on_ground = False
        self.double_jump_available = True
        self.jump_buffer = 0
        self.jump_buffer_time = 0.12

        # Gameplay
        self.alive = True
        self.score = 0

    def handle_input(self, keys):
        self.acc.x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.acc.x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.acc.x = self.speed

    def request_jump(self):
        self.jump_buffer = self.jump_buffer_time

    def do_jump_if_possible(self):
        if self.on_ground:
            self.vel.y = self.jump_speed
            self.on_ground = False
            self.double_jump_available = True
        elif self.double_jump_available:
            self.vel.y = self.jump_speed
            self.double_jump_available = False

    def physics_update(self, dt):
        # Apply gravity
        self.vel.y += self.gravity

        # Horizontal smoothing
        target_vx = self.acc.x
        self.vel.x = target_vx

        # Clamp speeds if needed (optional)
        self.vel.x = max(min(self.vel.x, 10), -10)
        self.vel.y = max(min(self.vel.y, 20), -20)

        # Jump buffer countdown
        if self.jump_buffer > 0:
            self.jump_buffer -= dt
            if self.on_ground:
                self.do_jump_if_possible()
                self.jump_buffer = 0

    def update(self, dt, tiles, hazards, coins, enemies):
        keys = pygame.key.get_pressed()
        self.handle_input(keys)

        # Jump input
        for event in pygame.event.get(pygame.USEREVENT):
            pass  # placeholder (we'll process events in main loop)

        # Manual jump check here instead of event
        if keys[pygame.K_SPACE]:
            # Edge-triggering: buffer jump; main loop will feed dt
            self.request_jump()

        # Physics before collision
        self.physics_update(dt)

        # Separate axis collision
        # Horizontal
        self.rect.x += int(self.vel.x)
        self.resolve_collisions(axis="x", solids=tiles)

        # Vertical
        prev_on_ground = self.on_ground
        self.rect.y += int(self.vel.y)
        self.on_ground = False
        self.resolve_collisions(axis="y", solids=tiles)

        # If landed this frame, clear buffer
        if not prev_on_ground and self.on_ground:
            self.jump_buffer = 0

        # Check hazards
        for h in hazards:
            if self.rect.colliderect(h.rect):
                self.die()

        # Collect coins
        for c in list(coins):
            if self.rect.colliderect(c.rect):
                coins.remove(c)
                self.score += 10

        # Simple enemy interaction (touch = death)
        for e in enemies:
            if self.rect.colliderect(e.rect):
                self.die()

    def resolve_collisions(self, axis, solids):
        for tile in solids:
            if self.rect.colliderect(tile.rect):
                if axis == "x":
                    if self.vel.x > 0:
                        self.rect.right = tile.rect.left
                    elif self.vel.x < 0:
                        self.rect.left = tile.rect.right
                    self.vel.x = 0
                else:  # y
                    if self.vel.y > 0:
                        self.rect.bottom = tile.rect.top
                        self.on_ground = True
                    elif self.vel.y < 0:
                        self.rect.top = tile.rect.bottom
                    self.vel.y = 0

    def die(self):
        self.alive = False

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=pos)

class Hazard(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE))
        self.image.fill(RED)
        # Triangle spike visual
        pygame.draw.polygon(self.image, (255, 160, 160), [(0, TILE), (TILE//2, 0), (TILE, TILE)])
        self.rect = self.image.get_rect(topleft=pos)

class Coin(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((TILE//2, TILE//2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GOLD, (TILE//4, TILE//4), TILE//4)
        self.rect = self.image.get_rect(center=(pos[0] + TILE//2, pos[1] + TILE//2))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, left_bound, right_bound, speed=2.0):
        super().__init__()
        self.image = pygame.Surface((TILE * 0.8, TILE * 0.8))
        self.image.fill((120, 40, 40))
        self.rect = self.image.get_rect(topleft=pos)
        self.left = left_bound
        self.right = right_bound
        self.speed = speed
        self.dir = 1

    def update(self, dt, tiles):
        self.rect.x += int(self.speed * self.dir)
        # Turn around at bounds or when colliding walls
        if self.rect.left <= self.left:
            self.rect.left = self.left
            self.dir = 1
        if self.rect.right >= self.right:
            self.rect.right = self.right
            self.dir = -1
        for t in tiles:
            if self.rect.colliderect(t.rect):
                self.dir *= -1
                break

def build_level(level_rows):
    tiles, hazards, coins, enemies = [], [], [], []
    player_spawn = (TILE, TILE)

    for y, row in enumerate(level_rows):
        for x, ch in enumerate(row):
            wx, wy = grid_to_world(x, y)
            if ch == "#":
                tiles.append(Tile((wx, wy)))
            elif ch == "P":
                player_spawn = (wx, wy)
            elif ch == "X":
                hazards.append(Hazard((wx, wy)))
            elif ch == "C":
                coins.append(Coin((wx, wy)))
            elif ch == "E":
                # Enemy patrol within two tiles left/right by default
                left = wx - TILE * 3
                right = wx + TILE * 3
                enemies.append(Enemy((wx, wy), left, right))
    return tiles, hazards, coins, enemies, player_spawn

def draw_world(screen, camera, tiles, hazards, coins, enemies, player):
    # Sky background
    screen.fill(SKY)

    # Parallax hint: simple horizon
    pygame.draw.rect(screen, (120, 200, 255), Rect(-camera.offset.x, HEIGHT*0.65 - camera.offset.y, WIDTH*2, HEIGHT))

    for t in tiles:
        screen.blit(t.image, camera.apply(t.rect))
    for h in hazards:
        screen.blit(h.image, camera.apply(h.rect))
    for c in coins:
        screen.blit(c.image, camera.apply(c.rect))
    for e in enemies:
        screen.blit(e.image, camera.apply(e.rect))
    screen.blit(player.image, camera.apply(player.rect))

def draw_ui(screen, player, font):
    # Score
    text = font.render(f"Score: {player.score}", True, UI)
    screen.blit(text, (16, 12))
    # Help
    help_text = font.render("Move: A/D or Left/Right | Jump: Space", True, UI)
    screen.blit(help_text, (16, 38))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)

    tiles, hazards, coins, enemies, player_spawn = build_level(LEVEL)
    player = Player(player_spawn)

    camera = Camera(WIDTH, HEIGHT)
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update
        player.update(dt, tiles, hazards, coins, enemies)
        for e in enemies:
            e.update(dt, tiles)
        camera.follow(player.rect)

        # Respawn if dead
        if not player.alive:
            # Simple respawn after short delay
            player = Player(player_spawn)

        # Draw
        draw_world(screen, camera, tiles, hazards, coins, enemies, player)
        draw_ui(screen, player, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
