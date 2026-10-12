import pygame
from config import (
    GRID, SNAKE_HEAD, SNAKE_BODY, SNAKE_DEAD, FOOD, RED, BLOCK,
    WHITE, GRAY, DARK_GRAY, BLUE, BLUE_HOVER,
)


def draw_grid(screen, ox, oy, fw, fh):
    for x in range(0, fw + 1, BLOCK):
        pygame.draw.line(screen, GRID, (ox + x, oy), (ox + x, oy + fh))
    for y in range(0, fh + 1, BLOCK):
        pygame.draw.line(screen, GRID, (ox, oy + y), (ox + fw, oy + y))


def draw_snake(screen, snake, ox, oy, dead=False):
    for i, seg in enumerate(snake):
        color = SNAKE_DEAD if dead and i == 0 else (
            SNAKE_HEAD if i == 0 else SNAKE_BODY)
        pygame.draw.rect(screen, color,
                         (seg[0] + ox, seg[1] + oy, BLOCK, BLOCK),
                         border_radius=4)


def draw_food(screen, food, ox, oy):
    pygame.draw.rect(screen, FOOD,
                     (food[0] + ox, food[1] + oy, BLOCK, BLOCK),
                     border_radius=6)


def draw_field_border(screen, ox, oy, fw, fh):
    t = 4
    pygame.draw.rect(screen, RED,
                     (ox - t, oy - t, fw + 2 * t, fh + 2 * t), t)


def dim_screen(screen, alpha=170):
    w, h = screen.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, (0, 0))


def center_text(screen, text, font, color, y):
    surf = font.render(text, True, color)
    screen.blit(surf, (screen.get_width() // 2 - surf.get_width() // 2, y))
    return surf


def draw_button(screen, rect, text, font, hover=False):
    color = BLUE_HOVER if hover else BLUE
    pygame.draw.rect(screen, color, rect, border_radius=8)
    surf = font.render(text, True, WHITE)
    screen.blit(surf, (rect.x + rect.w // 2 - surf.get_width() // 2,
                       rect.y + rect.h // 2 - surf.get_height() // 2))


def draw_input_box(screen, rect, text, font, cursor_on=False):
    pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=8)
    pygame.draw.rect(screen, GRAY, rect, width=2, border_radius=8)
    text_surf = font.render(text, True, WHITE)
    screen.blit(text_surf, (rect.x + 14, rect.y + 11))
    if cursor_on:
        cx = rect.x + 14 + text_surf.get_width() + 2
        pygame.draw.line(screen, WHITE,
                         (cx, rect.y + 12), (cx, rect.y + rect.h - 12), 2)


def init_window(w, h):
    s = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    if s is None:
        raise RuntimeError("Не удалось создать окно")
    return s

def load_icon(path: str = "icon.png"):
    """Загружает иконку окна. Если файла нет — возвращает None."""
    try:
        return pygame.image.load(path)
    except Exception as exc:
        print(f"[ICON] Не удалось загрузить иконку: {exc}")
        return None