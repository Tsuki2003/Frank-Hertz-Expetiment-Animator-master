import pygame
from BasicModule import BasicModule
from math import sin, cos, pi
import random
import time

class ParticalModule(pygame.sprite.Sprite):
    def __init__(self, screen, x, y):
        super(ParticalModule, self).__init__()

        self.screen = screen

        self.ball =pygame.draw.ellipse(self.screen, self.color, [x, y, self.radius, self.radius])
        #self.ball_rect = self.ball.get_rect()
        self.ball_rect = self.ball
        self.x = x
        self.y = y
        self.ball_rect.centerx = x
        self.ball_rect.centery = y
        self.vx = self.v * cos(2*pi*random.random())
        self.vy = self.v * sin(2*pi*random.random())

        self.activate_step = 0

    def update(self):
        pygame.draw.ellipse(self.screen, self.color1 if self.activate_step>0 else self.color,
                            [self.ball.left, self.ball.top, self.radius, self.radius])
        #self.screen.fill(self.color1 if self.activate_step>0 else self.color, self.ball)
        self.x = self.x + self.vx
        self.y = self.y + self.vy
        self.ball_rect.centerx = self.x
        self.ball_rect.centery = self.y



class Atom(ParticalModule):
    color = [89, 59, 9]
    radius = 5
    v = 0.2
    color1 = [199, 100, 53]

    def update(self):
        super(Atom, self).update()
        if self.ball_rect.top <= 20 or self.ball_rect.bottom >= 280:
            self.vy = -self.vy
        if self.ball_rect.left <= 20 or self.ball_rect.right >= 560:
            self.vx = -self.vx
        self.activate_step = max(self.activate_step-1, 0)



class Electron(ParticalModule):
    color = [247, 176, 11]
    radius = 2
    v = 0.3
    color1 = [199, 100, 53]

    def __init__(self, screen, x, y, tube):
        super(Electron, self).__init__(screen, x, y)
        self.tube = tube
        self.rect = self.ball_rect

    def update(self):
        super(Electron, self).update()
        if self.ball_rect.top <= 20 or self.ball_rect.left <= 20 or self.ball_rect.bottom >= 280:
            self.tube.delete_electrons.append(self)
        if (abs(self.ball_rect.centerx - 140) < 2 or abs(self.ball_rect.centerx - 440) < 2) and random.random() < 0.1:
            self.tube.delete_electrons.append(self)
        if self.ball_rect.right >= 560:
            self.tube.delete_electrons.append(self)
            self.tube.collected_electrons.append(time.time())
            self.tube.collected_electrons = self.tube.collected_electrons[-100:]

        # accelerate
        if self.ball_rect.centerx < 140:
            self.vx += self.tube.state.Ug / 50
        elif self.ball_rect.centerx < 440:
            self.vx += (self.tube.state.Ua - self.tube.state.Ug) / 50
        elif self.ball_rect.centerx > 440:
            self.vx -= (self.tube.state.Ue) / 50

    @property
    def velocity(self):
        return (self.vx**2 + self.vy**2) ** 0.5


