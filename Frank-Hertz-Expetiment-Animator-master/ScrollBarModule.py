import sys
import pygame
from BasicModule import BasicModule, get_screen
from RectModule import DisplayModule
from StateModule import State

class ScrollBarModule(BasicModule):
    def __init__(self, screen, x, y, max_value, set_value, **kwargs):
        super(ScrollBarModule, self).__init__(screen)
        self.x = x
        self.y = y
        self.max_value = max_value
        self.set_value = set_value

        if kwargs.get('is_Ua', False):
            self.state = kwargs['state']

        self.line = pygame.draw.line(screen, (0,0,0), (x, y+10), (x+120, y+10))
        self.rect = pygame.Rect(x-10, y, 20, 20)
        self.activate = False


    def update(self):
        self.screen.fill((0, 0, 0), self.line)
        self.screen.fill((200, 200, 200), self.rect)

    @property
    def listener(self):
        def listerner(event):
            if event.type == pygame.MOUSEBUTTONDOWN and not self.activate:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.rect.collidepoint(mouse_x, mouse_y):
                    self.activate = True
                    self.rect.centerx = min(max(mouse_x, self.x), self.x + 120)
                    if hasattr(self, 'state'):
                        self.state.helper['plot_temp'] = self.state.helper['plot']

            elif event.type == pygame.MOUSEMOTION and self.activate:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.rect.centerx = min(max(mouse_x, self.x), self.x + 120)
                value = (self.rect.centerx - self.x) / 120.0 * self.max_value
                self.set_value(value)
                if hasattr(self, 'state'):
                    self.state.helper['plot'] = False

            elif event.type == pygame.MOUSEBUTTONUP and self.activate:
                self.activate = False
                if hasattr(self, 'state'):
                    self.state.helper['plot'] = self.state.helper['plot_temp']

        return listerner

def test():
    pygame.init()

    screen = get_screen()

    # objects
    state = State()
    def get_text():
        return str(state.Uf)
    digit_displayer = DisplayModule(screen, x=200, y=320, get_text=get_text)
    bar = ScrollBarModule(screen, 50, 320, 10, state.set_param('Uf'))
    listener = bar.listener
    pygame.display.set_caption("test_label_module")

    while True:
        screen.fill((123,234,213))
        digit_displayer.update()
        digit_displayer.show_text()
        bar.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            listener(event)
        pygame.display.flip()


if __name__ == "__main__":
    test()