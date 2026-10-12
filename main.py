import pygame, sys, random
from config import *
from database import save_and_fetch, warm_up
from graphics import *


def new_game():
    sx = (FIELD_W // 2) // BLOCK * BLOCK
    sy = (FIELD_H // 2) // BLOCK * BLOCK
    snake = [(sx, sy)]
    direction = (BLOCK, 0)
    food = random_food(snake)
    return snake, direction, food, 0


def random_food(snake):
    while True:
        f = (random.randint(0, FIELD_W // BLOCK - 1) * BLOCK,
             random.randint(0, FIELD_H // BLOCK - 1) * BLOCK)
        if f not in snake:
            return f


def render_playing(screen, fonts, snake, food, score, ox, oy,
                   state, cursor_timer, win_w, win_h):
    """Общая отрисовка игрового экрана: field, snake, food, HUD."""
    draw_grid(screen, ox, oy, FIELD_W, FIELD_H)
    draw_food(screen, food, ox, oy)
    draw_snake(screen, snake, ox, oy, dead=(state == "input"))
    draw_field_border(screen, ox, oy, FIELD_W, FIELD_H)

    if state == "playing":
        panel = pygame.Surface((win_w, 40), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 130))
        screen.blit(panel, (0, 0))
        screen.blit(fonts['main'].render(f"Счёт: {score}", True, WHITE), (12, 8))
        hint = fonts['small'].render(
            "Стрелки - движение   |   Space - пауза   |   F11 - полный экран",
            True, GRAY)
        screen.blit(hint, (win_w - hint.get_width() - 12, 13))


def render_input_overlay(screen, fonts, player_name, name_error,
                         cursor_on, win_w, win_h):
    cy = win_h // 2
    center_text(screen, "ИГРА ОКОНЧЕНА", fonts['big'], RED, cy - 190)
    center_text(screen, f"Введите имя для сохранения в БД:",
                fonts['main'], WHITE, cy - 100)
    box_w, box_h = 340, 46
    box = pygame.Rect(win_w // 2 - box_w // 2, cy - 60, box_w, box_h)
    draw_input_box(screen, box, player_name, fonts['main'], cursor_on)
    if name_error:
        center_text(screen, "Пожалуйста, введите имя!",
                    fonts['small'], RED, box.y + box.h + 4)


def main():
    warm_up()
    pygame.init()
    screen = init_window(FIELD_W, FIELD_H)
    pygame.display.set_caption("Змейка")
    
    icon = load_icon("icon.png")
    if icon is not None:
        pygame.display.set_icon(icon)
        
    clock = pygame.time.Clock()

    fonts = {
        'small': pygame.font.SysFont("Segoe UI", 16),
        'main':  pygame.font.SysFont("Segoe UI", 22),
        'big':   pygame.font.SysFont("Segoe UI", 44, bold=True),
        'huge':  pygame.font.SysFont("Segoe UI", 100, bold=True),
    }

    snake, direction, food, score = new_game()
    win_w, win_h = FIELD_W, FIELD_H
    is_fullscreen = False
    windowed_size = (win_w, win_h)
    state = "countdown"
    state_before_pause = "countdown"
    pause_started = 0
    player_name = ""
    error_msg = ""
    name_error = False
    cursor_timer = 0
    countdown_start = pygame.time.get_ticks()
    top_scores, player_rank, total_players = [], None, None

    def start_countdown():
        nonlocal snake, direction, food, score, countdown_start
        nonlocal top_scores, player_rank, total_players
        snake, direction, food, score = new_game()
        countdown_start = pygame.time.get_ticks()
        top_scores, player_rank, total_players = [], None, None

    def resize_window(w, h):
        nonlocal screen, win_w, win_h
        win_w, win_h = max(MIN_WIN_W, w), max(MIN_WIN_H, h)
        screen = init_window(win_w, win_h)

    def toggle_fullscreen():
        nonlocal screen, win_w, win_h, is_fullscreen, windowed_size
        if not is_fullscreen:
            windowed_size = (win_w, win_h)
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            is_fullscreen = True
        else:
            screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
            is_fullscreen = False
        if screen is None:
            raise RuntimeError("Не удалось переключить режим экрана")
        win_w, win_h = screen.get_size()

    running = True
    while running:
        dt = clock.tick(FPS)
        cursor_timer += dt
        ox = (win_w - FIELD_W) // 2
        oy = (win_h - FIELD_H) // 2

        # Кнопка отправки
        btn = pygame.Rect(win_w // 2 - 100, win_h // 2 + 25, 200, 46)
        hover = btn.collidepoint(pygame.mouse.get_pos())

        # ----- saving (блокирующая операция) -----
        if state == "saving":
            screen.fill(BG)
            draw_grid(screen, ox, oy, FIELD_W, FIELD_H)
            draw_field_border(screen, ox, oy, FIELD_W, FIELD_H)
            dim_screen(screen, 150)
            center_text(screen, "Сохранение результата...",
                        fonts['main'], YELLOW, win_h // 2 - 15)
            pygame.display.flip()
            pygame.event.pump()
            try:
                top_scores, player_rank, total_players = save_and_fetch(
                    player_name, score)
                state = "saved"
            except Exception as exc:
                print(f"[DB] ERROR: {exc}")
                error_msg = str(exc)
                state = "error"
            continue

        # ----- события -----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.VIDEORESIZE and not is_fullscreen:
                resize_window(event.w, event.h)
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
                continue

            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and state == "input" and btn.collidepoint(event.pos)):
                if player_name.strip():
                    state = "saving"
                else:
                    name_error = True

            if event.type != pygame.KEYDOWN:
                continue

            # --- состояния с клавиатурой ---
            if state in ("countdown", "playing"):
                if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                    state_before_pause = state
                    pause_started = pygame.time.get_ticks()
                    state = "paused"
                elif state == "playing":
                    if event.key == pygame.K_UP and direction != (0, BLOCK):
                        direction = (0, -BLOCK)
                    elif event.key == pygame.K_DOWN and direction != (0, -BLOCK):
                        direction = (0, BLOCK)
                    elif event.key == pygame.K_LEFT and direction != (BLOCK, 0):
                        direction = (-BLOCK, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-BLOCK, 0):
                        direction = (BLOCK, 0)

            elif state == "paused":
                if event.key == pygame.K_SPACE:
                    if state_before_pause == "countdown":
                        countdown_start += pygame.time.get_ticks() - pause_started
                    state = state_before_pause
                elif event.key == pygame.K_ESCAPE:
                    running = False
                    break

            elif state == "input":
                ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
                if event.key == pygame.K_RETURN:
                    if player_name.strip():
                        state = "saving"
                    else:
                        name_error = True
                elif event.key == pygame.K_ESCAPE:
                    running = False
                    break
                elif ctrl and event.key == pygame.K_r:
                    player_name, name_error = "", False
                    start_countdown()
                    state = "countdown"
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                    name_error = False
                else:
                    ch = event.unicode
                    if ch and ch.isprintable() and len(player_name) < MAX_NAME_LEN:
                        player_name += ch
                        name_error = False

            elif state in ("saved", "error"):
                if event.key == pygame.K_r:
                    player_name, error_msg, name_error = "", "", False
                    start_countdown()
                    state = "countdown"
                elif event.key == pygame.K_ESCAPE:
                    running = False
                    break

        if not running:
            break

        # ----- обновление логики -----
        if state == "countdown":
            if pygame.time.get_ticks() - countdown_start >= 3 * COUNTDOWN_MS:
                state = "playing"
        elif state == "playing":
            new_head = (snake[0][0] + direction[0],
                        snake[0][1] + direction[1])
            hit_wall = (new_head[0] < 0 or new_head[0] >= FIELD_W or
                        new_head[1] < 0 or new_head[1] >= FIELD_H)
            if hit_wall or new_head in snake:
                if hit_wall:
                    cx = max(0, min(FIELD_W - BLOCK, new_head[0]))
                    cy = max(0, min(FIELD_H - BLOCK, new_head[1]))
                    if (cx, cy) != snake[0]:
                        snake.insert(0, (cx, cy))
                state = "input"
                player_name, name_error = "", False
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 10
                    food = random_food(snake)
                else:
                    snake.pop()

        # ----- отрисовка -----
        screen.fill(BG)
        render_playing(screen, fonts, snake, food, score, ox, oy,
                       state, cursor_timer, win_w, win_h)

        if state == "countdown":
            num = 3 - (pygame.time.get_ticks() - countdown_start) // COUNTDOWN_MS
            text = str(num) if num > 0 else "СТАРТ"
            color = YELLOW if num > 0 else GREEN
            surf = fonts['huge'].render(text, True, color)
            screen.blit(surf, (win_w // 2 - surf.get_width() // 2,
                               win_h // 2 - surf.get_height() // 2))

        elif state == "paused":
            dim_screen(screen, 180)
            center_text(screen, "ПАУЗА", fonts['big'], YELLOW, win_h // 2 - 60)
            center_text(screen, f"Ваш счёт: {score}", fonts['main'], WHITE, win_h // 2)
            center_text(screen, "Space - продолжить", fonts['main'], WHITE, win_h // 2 + 50)
            center_text(screen, "Esc - закрыть игру", fonts['small'], GRAY, win_h // 2 + 90)

        elif state == "input":
            dim_screen(screen, 180)
            center_text(screen, "ИГРА ОКОНЧЕНА", fonts['big'], RED, win_h // 2 - 190)
            center_text(screen, f"Ваш счёт: {score}", fonts['main'], WHITE, win_h // 2 - 140)
            render_input_overlay(screen, fonts, player_name, name_error,
                                 cursor_timer // 500 % 2 == 0, win_w, win_h)
            draw_button(screen, btn, "Отправить", fonts['main'], hover)
            center_text(screen, "Ctrl+R - новая игра", fonts['small'], GRAY, btn.y + btn.h + 14)
            center_text(screen, "ESC - закрыть игру", fonts['small'], GRAY, btn.y + btn.h + 36)

        elif state == "saved":
            dim_screen(screen, 190)
            cy = win_h // 2
            center_text(screen, "СОХРАНЕНО", fonts['big'], GREEN, cy - 190)
            center_text(screen, f"Игрок: {player_name}    Счёт: {score}",
                        fonts['main'], WHITE, cy - 140)
            if player_rank is not None:
                color = GREEN if player_rank <= TOP_LIMIT else GRAY
                center_text(screen, f"Ваше место: {player_rank} из {total_players}",
                            fonts['small'], color, cy - 110)
            center_text(screen, "ЛУЧШИЕ РЕЗУЛЬТАТЫ", fonts['small'], GRAY, cy - 85)

            left, right = win_w // 2 - 150, win_w // 2 + 150
            hdr = fonts['small']
            screen.blit(hdr.render("#", True, GRAY), (left + 5, cy - 62))
            screen.blit(hdr.render("Имя", True, GRAY), (left + 35, cy - 62))
            sc = hdr.render("Счёт", True, GRAY)
            screen.blit(sc, (right - sc.get_width(), cy - 62))
            pygame.draw.line(screen, DARK_GRAY, (left, cy - 42), (right, cy - 42), 1)

            for i, (name, val) in enumerate(top_scores):
                y = cy - 35 + i * 26
                is_me = (name == player_name and val == score)
                if is_me:
                    pygame.draw.rect(screen, HIGHLIGHT,
                                     (left - 2, y - 3, right - left + 4, 24),
                                     border_radius=4)
                    color = WHITE
                else:
                    color = WHITE if i == 0 else GRAY
                screen.blit(hdr.render(f"{i + 1}.", True, color), (left + 5, y))
                screen.blit(hdr.render(str(name), True, color), (left + 35, y))
                s = hdr.render(str(val), True, color)
                screen.blit(s, (right - s.get_width(), y))

            center_text(screen, "R - новая игра", fonts['small'], YELLOW, win_h - 45)
            center_text(screen, "ESC - закрыть игру", fonts['small'], YELLOW, win_h - 25)

        elif state == "error":
            dim_screen(screen, 200)
            cy = win_h // 2
            center_text(screen, "ОШИБКА СОХРАНЕНИЯ", fonts['big'], RED, cy - 155)
            center_text(screen, "Не удалось сохранить результат в БД.",
                        fonts['main'], WHITE, cy - 90)
            short = (error_msg[:72] + "...") if len(error_msg) > 72 else error_msg
            center_text(screen, short, fonts['small'], GRAY, cy - 55)
            center_text(screen, f"Ваш счёт: {score}", fonts['main'], YELLOW, cy - 15)
            center_text(screen, "R - новая игра", fonts['main'], WHITE, cy + 40)
            center_text(screen, "ESC - закрыть игру", fonts['main'], WHITE, cy + 75)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()