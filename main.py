import pygame, sys, time

WIDTH, HEIGHT = 960, 540
TILE = 48
FPS = 60

WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE = (40,100,220)
GREEN = (80,160,90)
RED = (220,60,60)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 48)

scores = [0, 0]
turn = 0

def show_scoreboard():
    screen.fill(WHITE)
    text = font.render(f"{scores[0]} : {scores[1]}", True, BLACK)
    screen.blit(text, (WIDTH//2 - 60, HEIGHT//2 - 30))
    pygame.display.flip()
    time.sleep(1)

def show_winner(player):
    screen.fill(WHITE)
    text = font.render(f"Player {player+1} Wins!", True, BLACK)
    screen.blit(text, (WIDTH//2 - 150, HEIGHT//2 - 30))
    pygame.display.flip()
    time.sleep(3)
    pygame.quit(); sys.exit()

# ------------------ MAIN MENU ------------------
def main_menu():
    while True:
        screen.fill(WHITE)
        title = font.render("Main Menu", True, BLACK)
        start = font.render("Press S to Start", True, BLACK)
        end = font.render("Press Q to Quit", True, BLACK)
        screen.blit(title, (WIDTH//2-100, HEIGHT//3))
        screen.blit(start, (WIDTH//2-150, HEIGHT//2))
        screen.blit(end, (WIDTH//2-150, HEIGHT//2+50))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_s: return "start"
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

def map_editor():
    cols, rows = WIDTH//TILE, HEIGHT//TILE
    grid = [["." for _ in range(cols)] for _ in range(rows)]
    current_tile = "#"

    tile_names = {
        "#": "Block (발판)",
        "P": "Player Start ",
        "G": "Goal ",
        "X": "Trap ",
        "S": "Slow Block",
        "J": "Double Jump Item",
        "A": "Arrow Trap"
    }

    while True:
        screen.fill(WHITE)
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
                pygame.draw.rect(screen, (200,200,200), rect, 1)
                if grid[y][x] == "#": pygame.draw.rect(screen, GREEN, rect)
                elif grid[y][x] == "P": pygame.draw.rect(screen, BLUE, rect)
                elif grid[y][x] == "G": pygame.draw.rect(screen, (0,200,0), rect)
                elif grid[y][x] == "X": pygame.draw.rect(screen, (150,0,0), rect)
                elif grid[y][x] == "S": pygame.draw.rect(screen, (150,150,255), rect)
                elif grid[y][x] == "J": pygame.draw.circle(screen, (255,100,255), rect.center, TILE//3)
                elif grid[y][x] == "A": pygame.draw.rect(screen, (120,60,0), rect)

        info = font.render(f"Tile: {current_tile} - {tile_names[current_tile]} | Enter=Play", True, BLACK)
        screen.blit(info, (10,10))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1: current_tile = "#"
                if e.key == pygame.K_2: current_tile = "P"
                if e.key == pygame.K_3: current_tile = "G"
                if e.key == pygame.K_4: current_tile = "X"
                if e.key == pygame.K_5: current_tile = "S"
                if e.key == pygame.K_6: current_tile = "J"
                if e.key == pygame.K_7: current_tile = "A"
                if e.key == pygame.K_RETURN:
                    # 출발지점과 도착지점 확인
                    has_start = any("P" in row for row in grid)
                    has_goal = any("G" in row for row in grid)
                    if not has_start or not has_goal:
                        print("⚠️ 반드시 출발지점(P)과 도착지점(G)을 지정해야 합니다!")
                    else:
                        return grid
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx,my = pygame.mouse.get_pos()
                gx, gy = mx//TILE, my//TILE

                # 출발지점은 하나만 허용
                if current_tile == "P":
                    # 이미 출발지점이 있으면 추가 불가
                    if any("P" in row for row in grid):
                        print("⚠️ 출발지점은 하나만 지정할 수 있습니다!")
                        continue

                grid[gy][gx] = current_tile     
def play_game(grid):
    global turn, scores
    player = None
    tiles, goal, traps, slows, jump_items, arrow_traps, arrows = [], None, [], [], [], [], []
    for y,row in enumerate(grid):
        for x,ch in enumerate(row):
            rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
            if ch == "#": tiles.append(rect)
            if ch == "P": player = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
            if ch == "G": goal = rect
            if ch == "X": traps.append(rect)
            if ch == "S": slows.append(rect)
            if ch == "J": jump_items.append(rect)
            if ch == "A": arrow_traps.append({"rect": rect, "timer": 0})

    vel = [0,0]
    gravity = 0.7
    jump = -14
    speed = 6
    double_jump = False
    used_double_jump = False

    while True:
        dt = clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        vel[0] = 0
        if keys[pygame.K_LEFT]: vel[0] = -speed
        if keys[pygame.K_RIGHT]: vel[0] = speed
        if keys[pygame.K_SPACE]:
            if vel[1] == 0:  # 땅에서 점프
                vel[1] = jump
                used_double_jump = False
            elif double_jump and not used_double_jump:  # 2단 점프
                vel[1] = jump
                used_double_jump = True

        vel[1] += gravity
        player.x += vel[0]
        player.y += vel[1]

        # --- 일반 블록 충돌 ---
        for t in tiles:
            if player.colliderect(t):
                if vel[1] > 0 and player.bottom > t.top:
                    player.bottom = t.top
                    vel[1] = 0
                    used_double_jump = False

        # --- 슬로우 블록 충돌 (발판 + 디버프) ---
        speed = 6
        jump_power = jump
        for s in slows:
            if player.colliderect(s):
                if vel[1] > 0 and player.bottom > s.top:
                    player.bottom = s.top
                    vel[1] = 0
                    used_double_jump = False
                # 디버프 효과
                speed = 3
                jump_power = -12  # 점프력 소폭 감소

        # 맨 아래 도달 → 게임오버
        if player.top > HEIGHT:
            turn = 1 - turn
            return

        # 함정 충돌
        for tr in traps:
            if player.colliderect(tr):
                turn = 1 - turn
                return

        # Goal 도달
        if goal and player.colliderect(goal):
            scores[turn] += 1
            show_scoreboard()
            if scores[turn] >= 3:
                show_winner(turn)
            turn = 1 - turn
            return

        # 2단 점프 아이템 획득
        for j in jump_items[:]:
            if player.colliderect(j):
                jump_items.remove(j)
                double_jump = True

        # --- 화살 함정 (아래 방향 발사) ---
        for trap in arrow_traps:
            trap["timer"] += dt
            if trap["timer"] > 2:  # 2초마다 발사
                trap["timer"] = 0
                arrows.append(pygame.Rect(trap["rect"].centerx, trap["rect"].bottom, 8, 20))

        # 화살 이동 및 충돌
        for arrow in arrows[:]:
            arrow.y += 8  # 아래로 이동
            if arrow.y > HEIGHT: arrows.remove(arrow)
            if player.colliderect(arrow):
                turn = 1 - turn
                return

        # --- 그리기 ---
        screen.fill((135,206,235))
        for t in tiles: pygame.draw.rect(screen, GREEN, t)
        for tr in traps: pygame.draw.rect(screen, (150,0,0), tr)
        for s in slows: pygame.draw.rect(screen, (150,150,255), s)
        for j in jump_items: pygame.draw.circle(screen, (255,100,255), j.center, TILE//3)
        for trap in arrow_traps: pygame.draw.rect(screen, (120,60,0), trap["rect"])
        for arrow in arrows: pygame.draw.rect(screen, (80,80,80), arrow)
        if goal: pygame.draw.rect(screen, (0,200,0), goal)
        pygame.draw.rect(screen, BLUE, player)
        text = font.render(f"P{turn+1} Turn", True, BLACK)
        screen.blit(text, (10,10))
        pygame.display.flip()
# ------------------ MAIN LOOP ------------------
def main():
    while True:
        choice = main_menu()
        if choice == "start":
            grid = map_editor()
            while True:
                play_game(grid)

if __name__ == "__main__":
    main()