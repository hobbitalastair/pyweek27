import pygame, pygame.display, pygame.event, pygame.time, pygame.image, math, pygame.mixer, pygame.font
from pygame import Color, Surface, transform, draw
from pygame.mixer import Sound
from random import randint
from parallax import parallax

TICKEVENT = pygame.USEREVENT + 1
FPS = 30
HEIGHTMAP_LEN = 2000
HEIGHTMAP_XRES = 5
STOPS = 3

class Bus:
    def __init__(self):
        self.img = pygame.image.load("bus.png")
        # Wheels - x, y, radii
        self.back_wheel = (78, 75 - 13, 12)
        self.front_wheel = (225, 75 - 13, 12)
        self.wheelbase = self.front_wheel[0] - self.back_wheel[0]

        self.seats = {30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250}

        self.mass = 10000   # Rough mass in kg
        self.speed = 0      # Horizontal speed in pixel/s
        self.angle = 0      # Angle in radians
        self.pos = 0        # Offset from start in pixels
        self.altitude = 0   # Approximate altitude in pixels
        self.people = {}    # Person: offset

        self.current_stop = 0
        self.next_stop = 1


class Stop:
    sign = pygame.image.load("stop_sign.png")
    img = pygame.image.load("stop.png")

    def __init__(self, state, pos, time):
        self.x = pos
        min_x = self.x - (self.img.get_width() // 2)
        max_x = self.x + (self.img.get_width() // 2)
        self.y = min((get_height(x, state) for x in range(min_x, max_x + 1))) - 2 # With margin for parallax
        self.z = 1.05   # Add a slight parallax effect...
        self.time = time            # Target time of arrival, in ms
        self.arrived = False
        self.arrival_time = None    # Actual time of arrival

    def render(self, screen, pos):
        x, y = pos
        screen.blit(self.img, (x - (self.img.get_width() // 2), y - self.img.get_height()))


class Person:
    def __init__(self, state, start, end):
        self.start = start
        self.end = end
        self.x = start
        self.y = get_height(self.x, state)
        self.z = 1.03 # Should be 1 on the bus?
        self.height = 40
        self.delivered = False

    def render(self, screen, pos):
        x, y = pos
        draw.circle(screen, Color(230, 140, 140), (x, y - self.height), 7)


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
        self.brake = 0

        self.engine_noise = Sound("bus_engine.ogg")

        self.heightmap = [0 for i in range(HEIGHTMAP_LEN)]
        current_height = 0.0
        delta = 0.0
        for i in range(len(self.heightmap)):
            self.heightmap[i] = int(current_height)
            delta += (randint(-1, 1) / 10)
            delta *= 0.99 # Ensure that hills smooth out
            current_height += delta

        self.stops = [Stop(self, i * int(HEIGHTMAP_LEN * HEIGHTMAP_XRES / (STOPS - 1)), HEIGHTMAP_LEN * i / (STOPS * 40)) for i in range(STOPS)]

        self.people = set()
        count = randint(5, 10)
        while len(self.people) < count:
            start_stop = randint(0, len(self.stops) - 2)
            end_stop = randint(start_stop, len(self.stops) - 1)
            start = self.stops[start_stop].x + randint(-60, 60) # Random placement to avoid overlapping...
            end = self.stops[end_stop].x
            if start_stop < end_stop:
                self.people.add(Person(self, start, end))


def get_height(x, state):
    i = max(min(int(x) // HEIGHTMAP_XRES, len(state.heightmap) - 1), 0)
    return state.heightmap[i]


def redraw_bg(state, screen):
    width, height = screen.get_size()
    # Draw the background
    for x in range(width):
        h = get_height(x - (width // 2) + int(state.bus.pos), state)
        h -= state.bus.altitude # Keep the bus centred
        draw.line(screen, Color(0, 0, 0), (x, height), (x, (height // 2) - h))


def position_bus(state, screen):
    """ Calculate the bus position; required for keeping the bus centered """
    bus = state.bus

    # Calculate the wheel heights and bus angle
    # FIXME: This is fairly naive... does not account for the wheels moving
    #        inwards/outwards as the bus rotates.
    bus.back_wheel_height = get_height(int(bus.pos) - (bus.img.get_width() // 2) + bus.back_wheel[0], state)
    bus.front_wheel_height = get_height(int(bus.pos) - (bus.img.get_width() // 2) + bus.front_wheel[0], state)
    bus.angle = math.sin((bus.front_wheel_height - bus.back_wheel_height) / bus.wheelbase)
    
    # Update the bus altitude...
    bus.altitude = (bus.back_wheel_height + bus.front_wheel_height) // 2


def redraw_bus(state, screen):
    """ Redraw the bus on the display """
    width, height = screen.get_size()
    bus = state.bus

    # Calculate the change to the wheel y position.
    mid_to_wheel_x = (bus.img.get_width() // 2) - bus.back_wheel[0]
    mid_to_wheel_y = (bus.img.get_height() // 2) - bus.back_wheel[1]
    hyp = math.sqrt(mid_to_wheel_x**2 + mid_to_wheel_y**2)
    adjusted_mid_to_wheel_y = math.asin(math.sin(mid_to_wheel_y / hyp) - bus.angle) * hyp

    bus_img = transform.rotate(bus.img, bus.angle * 180 / 3.14)
    screen.blit(bus_img, ((width - bus_img.get_width()) // 2,
                          (height - bus_img.get_height()) // 2 \
                            + adjusted_mid_to_wheel_y - bus.back_wheel[2] \
                            - bus.back_wheel_height + bus.altitude))


def redraw_instruments(state, screen, font):
    """ Redraw instruments """
    text = "Speed: {}, RPM: {}, Target time: {}".format(round(state.bus.speed), round(state.engine.revs), round(state.stops[state.bus.next_stop].time - (pygame.time.get_ticks() // 1000)))
    img = font.render(text, True, Color(255, 255, 255), Color(0, 0, 0))
    screen.blit(img, [(screen.get_size()[i] - img.get_size()[i]) // (2 - i) for i in range(2)])


def redraw(state, screen, font):
    """ Redraw the current game state """
    screen.fill(Color(100, 190, 255))
    position_bus(state, screen)

    parallax(-state.bus.pos, -state.bus.altitude, screen, state.stops + list(state.people))

    redraw_bg(state, screen)
    redraw_bus(state, screen)

    redraw_instruments(state, screen, font)


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

    engine.revs -= abs(engine_force) / 200
    engine.revs += engine.throttle * 100
    engine.revs *= 0.98                         # Internal friction

    # FIXME: Hacked engine noise to show revs... should probably show throttle?
    # The sound "pitch" normally changes for revs instead?
    engine.revs = max(min(engine.revs, engine.max_revs), 0) # Cap engine revs.
    #state.engine_noise.set_volume(engine.throttle) # 0-1
    state.engine_noise.set_volume(engine.revs / engine.max_revs) # 0-1
    

    # Update the bus model
    accel = -math.asin(bus.angle) * 5           # Gravity
    accel += engine_force / bus.mass            # Engine influence
    accel -= bus.speed * 500 / bus.mass         # Dynamic friction
    accel -= 1000 * state.brake * bus.speed / bus.mass    # Braking force
    bus.speed += accel
    # Static friction (brake + bus)
    if bus.speed != 0:
        static_brake = (0.05 * state.brake + 0.005) / bus.speed
        if abs(static_brake) > abs(bus.speed):
            bus.speed = 0
        else:
            bus.speed -= static_brake
    bus.pos += bus.speed

    # Passengers
    for person, offset in bus.people.items():
        person.x = bus.pos + offset
        person.y = get_height(person.x, state) # FIXME: Doesn't recalculate height properly...

    if bus.speed == 0:
        # Board the bus
        for person in state.people.difference(bus.people.keys()):
            if abs(person.x - bus.pos) < 100 and abs(bus.pos - person.end) > 100:
                offsets = list(bus.seats.difference(bus.people.values()))
                if len(offsets) == 0:
                    offset = 0
                else:
                    offset = offsets[randint(0, len(offsets) - 1)]
                offset -= bus.img.get_width() // 2
                bus.people[person] = offset

        # Leave the bus
        for person in bus.people.copy():
            if abs(person.end - bus.pos) < 100:
                bus.people.pop(person)
                person.delivered = True

        # Update the stop number
        bus.current_stop = 0
        for i, stop in enumerate(state.stops):
            if abs(bus.pos - stop.x) < 200:
                bus.current_stop = i
        
        bus.next_stop = min(bus.current_stop + 1, len(state.stops) - 1)
        if not state.stops[bus.current_stop].arrived:
            state.stops[bus.current_stop].arrived = True
            state.stops[bus.current_stop].arrival_time = pygame.time.get_ticks() // 1000

    # Check for the end of game condition
    if bus.current_stop == len(state.stops) - 1:
        overdue_time = 0
        for stop in state.stops:
            if stop.arrived:
                overdue_time += max(0, stop.arrival_time - stop.time)
        undelivered = 0
        for person in state.people:
            if not person.delivered:
                undelivered += 1

        print("Total time: {}".format(pygame.time.get_ticks() // 1000))
        print("Overdue time: {}".format(round(overdue_time)))
        print("Undelivered: {}".format(undelivered))
        print("Score (small is better): {}".format(undelivered * 5 + round(overdue_time)))
        pygame.event.post(pygame.event.Event(pygame.QUIT))


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
        if ev.key == pygame.K_b:
            state.brake = 1
            state.engine.throttle = 0
            state.engine.clutch = 0
    if ev.type == pygame.KEYUP:
        if ev.key == pygame.K_b:
            state.brake = 0
            state.engine.clutch = 1


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 700))
    pygame.display.flip()
    pygame.time.set_timer(TICKEVENT, 1000 // FPS)

    font = pygame.font.SysFont("Terminus", 18)

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
                redraw(state, screen, font)
                pygame.display.flip()
            else:
                handle_event(event, state)

    finally:
        pygame.quit()

