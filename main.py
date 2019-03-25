import pygame, pygame.display, pygame.event, pygame.time, pygame.image, math
from pygame import Color, Surface, transform, draw
from random import randint

TICKEVENT = pygame.USEREVENT + 1
FPS = 30
HEIGHTMAP_LEN = 2000
HEIGHTMAP_XRES = 5

class Bus:
    def __init__(self):
        self.img = pygame.image.load("bus.png")
        # Wheels - x, y, radii
        self.back_wheel = (78, 75 - 13, 12)
        self.front_wheel = (225, 75 - 13, 12)
        self.wheelbase = self.front_wheel[0] - self.back_wheel[0]

        self.pos = 0
        self.speed = 0
        self.angle = 0
        self.altitude = 0


class State:

    def __init__(self):
        self.bus = Bus()

        self.heightmap = [0 for i in range(HEIGHTMAP_LEN)]
        current_height = 0.0
        delta = 0
        for i in range(len(self.heightmap)):
            self.heightmap[i] = int(current_height)
            delta += (randint(-1, 1) / 10)
            current_height += delta


def get_height(x, state):
    i = max(min(x // HEIGHTMAP_XRES, len(state.heightmap) - 1), 0)
    return state.heightmap[i]


def redraw_bg(state, screen):
    width, height = screen.get_size()
    # Draw the background
    for x in range(width):
        h = get_height(x - (width // 2) + state.bus.pos, state)
        h -= state.bus.altitude # Keep the bus centred
        draw.line(screen, Color(0, 0, 0), (x, height), (x, (height // 2) - h))


def redraw_bus(bus, screen):
    """ Redraw the bus on the display """
    width, height = screen.get_size()

    # Calculate the wheel heights and bus angle
    # FIXME: This is fairly naive... does not account for the wheels moving
    #        inwards/outwards as the bus rotates.
    back_wheel_height = get_height(bus.pos - (bus.img.get_width() // 2) + bus.back_wheel[0], state)
    front_wheel_height = get_height(bus.pos - (bus.img.get_width() // 2) + bus.front_wheel[0], state)
    bus.angle = math.sin((front_wheel_height - back_wheel_height) / bus.wheelbase)
    
    # Update the bus altitude...
    bus.altitude = (back_wheel_height + front_wheel_height) // 2

    # Calculate the change to the wheel y position.
    mid_to_wheel_x = (bus.img.get_width() // 2) - bus.back_wheel[0]
    mid_to_wheel_y = (bus.img.get_height() // 2) - bus.back_wheel[1]
    hyp = math.sqrt(mid_to_wheel_x**2 + mid_to_wheel_y**2)
    adjusted_mid_to_wheel_y = math.asin(math.sin(mid_to_wheel_y / hyp) - bus.angle) * hyp
    
    bus_img = transform.rotate(bus.img, bus.angle * 180 / 3.14)
    screen.blit(bus_img, ((width - bus_img.get_width()) // 2,
                          (height - bus_img.get_height()) // 2 \
                            + adjusted_mid_to_wheel_y - bus.back_wheel[2] \
                            - back_wheel_height + bus.altitude))

def redraw(state, screen):
    """ Redraw the current game state """
    screen.fill(Color(255, 255, 0))
    redraw_bus(state.bus, screen)
    redraw_bg(state, screen)


def tick(state):
    """ Update the game state """
    state.bus.pos += int(state.bus.speed)
    state.bus.speed -= state.bus.angle # Psuedo gravity...


def handle_event(ev, state):
    """ Handle an event """
    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RIGHT:
        state.bus.speed += 1
    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_LEFT:
        state.bus.speed -= 1


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode()
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

