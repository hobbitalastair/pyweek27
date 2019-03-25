import pygame, pygame.display, pygame.event, pygame.time
from pygame import Color

TICKEVENT = pygame.USEREVENT + 1
FPS = 1

pygame.init()
screen = pygame.display.set_mode()
screen.fill(Color(255, 255, 0))
pygame.display.flip()
pygame.time.set_timer(TICKEVENT, 1000 // FPS)

try:
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            break
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            break
        if event.type == TICKEVENT:
            print("flip")
            pygame.display.flip()

finally:
    pygame.quit()

