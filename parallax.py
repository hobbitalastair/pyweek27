import pygame, pygame.display, pygame.event, pygame.time
from pygame import Color, draw
from random import randint

SCROLL_SPEED = 10
TICKEVENT = pygame.USEREVENT + 1
FPS = 30
MIN_X = -1000
MAX_X = 1000
MIN_Y = -1000
MAX_Y = 1000
MIN_Z = 1
MAX_Z = 10
MIN_RAD = 5
MAX_RAD = 20
COLOURS = [
    Color(255, 0, 0),
    Color(180, 75, 0),
    Color(120, 120, 0),
    Color(75, 180, 0),
    Color(0, 255, 0),
    Color(0, 180, 75),
    Color(0, 120, 120),
    Color(0, 75, 180),
    Color(0, 0, 255),
    Color(0, 0, 120),
        ]

def parallax(x, y, screen, objects):
    objects.sort(key=lambda c: -c.z)
    x_offset = (screen.get_width() // 2)
    y_offset = (screen.get_height() // 2)
    for obj in objects:
        z = obj.z
        pos = (int(x_offset + ((x + obj.x) / z)), int(y_offset - ((obj.y + y) / z)))
        colour = COLOURS[obj.z - 1]
        draw.circle(screen, colour, pos, obj.rad)


class RandCircle:
    def __init__(self):
        self.x = randint(MIN_X, MAX_X)
        self.y = randint(MIN_Y, MAX_Y)
        self.z = randint(MIN_Z, MAX_Z)
        self.rad = randint(MIN_RAD, MAX_RAD)

class State:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.circles = [RandCircle() for i in range(randint(0, 300))]

def redraw(state, screen):
    screen.fill(Color(255, 255, 255))
    parallax(state.x, state.y, screen, state.circles)

def tick(state):
    if state.left: state.x -= SCROLL_SPEED
    if state.right: state.x += SCROLL_SPEED
    if state.up: state.y += SCROLL_SPEED
    if state.down: state.y -= SCROLL_SPEED

def handle_event(ev, state):
    if ev.type == pygame.KEYDOWN:
        if ev.key == pygame.K_LEFT: state.left = True
        if ev.key == pygame.K_RIGHT: state.right = True
        if ev.key == pygame.K_UP: state.up = True
        if ev.key == pygame.K_DOWN: state.down = True
    if ev.type == pygame.KEYUP:
        if ev.key == pygame.K_LEFT: state.left = False
        if ev.key == pygame.K_RIGHT: state.right = False
        if ev.key == pygame.K_UP: state.up = False
        if ev.key == pygame.K_DOWN: state.down = False


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 700))
    pygame.display.flip()
    pygame.time.set_timer(TICKEVENT, 1000 // FPS)

    state = State()

    try:
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                break
            elif event.type == TICKEVENT:
                tick(state)
                redraw(state, screen)
                pygame.display.flip()
            else:
                handle_event(event, state)

    finally:
        pygame.quit()

