import pygame, pygame.display, pygame.event, pygame.time, pygame.image, math, pygame.mixer
from pygame import Color, Surface, transform, draw
from pygame.mixer import Sound
from random import randint

TICKEVENT = pygame.USEREVENT + 1
FPS = 30
HEIGHTMAP_LEN = 2000
HEIGHTMAP_XRES = 5
G_ACCEL = 10

class Bus:
    def __init__(self):
        self.img = pygame.image.load("bus.png")
        # Wheels - x, y, radii
        self.back_wheel = (78, 75 - 13, 12)
        self.front_wheel = (225, 75 - 13, 12)
        self.wheelbase = self.front_wheel[0] - self.back_wheel[0]

        self.mass = 10000   # Rough mass in kg
        self.speed = 0      # Horizontal speed in pixel/s
        self.angle = 0      # Angle in radians
        self.pos = 0        # Offset from start in pixels
        self.altitude = 0   # Approximate altitude in pixels


class Engine:
    def __init__(self):
        self.revs = 0       # 2000 typical??
        self.max_revs = 6000    # ??
        self.throttle = 0   # 0-1
        self.clutch = 1     # 0-1, clutch engagement
        self.gears = {'N': 0.0, 'R': -0.001, '1': 0.001, '2': 0.005, '3': 0.01}
        self.gear = 'N'

    def ratio(self):
        return self.gears[self.gear]


class State:

    def __init__(self):
        self.bus = Bus()
        self.engine = Engine()

        self.engine_noise = Sound("bus_engine.ogg")

        self.heightmap = [0 for i in range(HEIGHTMAP_LEN)]
        current_height = 0.0
        delta = 0.0
        for i in range(len(self.heightmap)):
            self.heightmap[i] = int(current_height)
            delta += (randint(-1, 1) / 10)
            delta *= 0.99 # Ensure that hills smooth out
            current_height += delta


def get_height(x, state):
    i = max(min(x // HEIGHTMAP_XRES, len(state.heightmap) - 1), 0)
    return state.heightmap[i]


def redraw_bg(state, screen):
    width, height = screen.get_size()
    # Draw the background
    for x in range(width):
        h = get_height(x - (width // 2) + int(state.bus.pos), state)
        h -= state.bus.altitude # Keep the bus centred
        draw.line(screen, Color(0, 0, 0), (x, height), (x, (height // 2) - h))


def redraw_bus(bus, screen):
    """ Redraw the bus on the display """
    width, height = screen.get_size()

    # Calculate the wheel heights and bus angle
    # FIXME: This is fairly naive... does not account for the wheels moving
    #        inwards/outwards as the bus rotates.
    back_wheel_height = get_height(int(bus.pos) - (bus.img.get_width() // 2) + bus.back_wheel[0], state)
    front_wheel_height = get_height(int(bus.pos) - (bus.img.get_width() // 2) + bus.front_wheel[0], state)
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
    bus = state.bus
    engine = state.engine

    # FIXME: Lots of random constants! Not terribly physical!

    engine_speed = engine.revs * engine.ratio() * engine.clutch
    speed_delta = engine_speed - bus.speed
    if engine.ratio() != 0:
        torque = abs((1 / engine.ratio()) * engine.clutch * 10)
    else:
        torque = 0

    engine_force = speed_delta * torque

    engine.revs -= engine_force / 200
    engine.revs += engine.throttle * 100

    # FIXME: Hacked engine noise to show revs... should probably show throttle?
    # The sound "pitch" normally changes for revs instead?
    engine.revs = max(min(engine.revs, engine.max_revs), 0) # Cap engine revs.
    #state.engine_noise.set_volume(engine.throttle) # 0-1
    state.engine_noise.set_volume(engine.revs / engine.max_revs) # 0-1
    

    # Update the bus model
    accel = -math.asin(bus.angle) * G_ACCEL     # Gravity
    accel += engine_force / bus.mass            # Engine influence
    accel -= bus.speed * 500 / bus.mass         # Dynamic friction
    bus.speed += accel
    # Static friction
    if bus.speed > 0:
        bus.speed = max(0, bus.speed - 0.5)
    else:
        bus.speed = min(0, bus.speed + 0.5)
    bus.pos += bus.speed


def handle_event(ev, state):
    """ Handle an event """
    if ev.type == pygame.KEYDOWN:
        if ev.key == pygame.K_RIGHT:
            state.engine.throttle = min(state.engine.throttle + 0.1, 1)
        if ev.key == pygame.K_LEFT:
            state.engine.throttle = max(state.engine.throttle - 0.1, 0)
        if ev.key == pygame.K_1:
            state.engine.gear = '1'
        if ev.key == pygame.K_2:
            state.engine.gear = '2'
        if ev.key == pygame.K_3:
            state.engine.gear = '3'
        if ev.key == pygame.K_r:
            state.engine.gear = 'R'
        if ev.key == pygame.K_n:
            state.engine.gear = 'N'


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode()
    pygame.display.flip()
    pygame.time.set_timer(TICKEVENT, 1000 // FPS)

    state = State()
    state.engine_noise.play(loops=-1) # Start the engine running.

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

