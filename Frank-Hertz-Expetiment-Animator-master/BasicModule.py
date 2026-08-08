from dotteddict import dotteddict
import pygame
from inspect import isfunction

class BasicModule(object):
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.sub_module = dotteddict(dict())

    def add_sub_module(self, name, module):
        self.sub_module[name] = module

    def update(self):
        pass

    @property
    def listener(self):
        listeners = []
        for sub_module in self.sub_module.values():
            listener = sub_module.listener
            if isfunction(listener):
                listeners.append(sub_module.listener)
            elif isinstance(listener, list):
                listeners.extend(listener)
        return listeners if listeners else None


def get_screen():
    screen = pygame.display.set_mode((1200, 900))
    return screen