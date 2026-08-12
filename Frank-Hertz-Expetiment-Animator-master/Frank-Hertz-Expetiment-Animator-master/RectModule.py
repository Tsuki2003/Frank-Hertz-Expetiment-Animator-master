import sys
import pygame

from BasicModule import BasicModule, get_screen
from StateModule import State

class LabelModule(BasicModule):
    def __init__(self, screen, x, y, text, **kwargs):
        super(LabelModule, self).__init__(screen)
        self.x = x
        self.y = y

        self.text = text
        self.text_color = kwargs.get('text_color', (0,0,0))
        self.font = pygame.font.SysFont(None, kwargs.get('fontsize', 32))
        self.bg_color = kwargs.get('bg_color', None)
        self.rect = pygame.Rect(x, y, 40, 20)

        self.prepare_text()

    def prepare_text(self):
        self.text_image = self.font.render(self.text, True, self.text_color, self.bg_color)
        self.text_rect = self.text_image.get_rect()
        self.text_rect.center = self.rect.center

    def show_text(self):
        self.screen.blit(self.text_image, self.text_rect)

    def update(self):
        pass

class DisplayModule(LabelModule):
    def __init__(self, screen, x, y, get_text, **kwargs):
        super(DisplayModule, self).__init__(screen, x, y, '', **kwargs)
        self.get_text = get_text
        self.text_color = kwargs.get('text_color', (0,255,0))
        self.bg_color = kwargs.get('bg_color', (0,0,0))

    def update(self):
        self.text = self.get_text()
        self.prepare_text()

class ButtonModule(DisplayModule):
    def __init__(self, screen, x, y, state, **kwargs):
        self.state = state
        def get_text():
            return "Plot mode: " + ('on' if self.state.helper['plot'] else 'off')
        self.get_text = get_text()

        self.rect = pygame.Rect(x-40, y, 120, 60)

        super(ButtonModule, self).__init__(screen, x, y, get_text, **kwargs)
        self.text_color = kwargs.get('text_color', (0,0,200))
        self.bg_color = kwargs.get('bg_color', (200,200,0))

    def prepare_text(self):
        self.text_image = self.font.render(self.text, True, self.text_color, self.bg_color)
        self.text_rect = self.text_image.get_rect()
        self.text_rect.center = self.rect.center

    def show_button(self):
        self.screen.fill(self.bg_color, self.rect)
        self.screen.blit(self.text_image, self.text_rect)

    @property
    def listener(self):
        def listener(event):
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.rect.collidepoint(mouse_x, mouse_y):
                    self.state.helper['plot'] = not self.state.helper['plot']
        return listener




def test():
    pygame.init()

    screen = get_screen()

    # objects
    label = LabelModule(screen, x=10, y=310, text='Uf')
    import random
    def get_text():
        return str("%.2f"%(random.random()))
    digit_displayer = DisplayModule(screen, x=180, y=310, get_text=get_text)

    button = ButtonModule(screen, x=450, y=320, state=State())
    listener = button.listener
    pygame.display.set_caption("test_label_module")

    while True:
        screen.fill((123,234,213))
        label.show_text()
        digit_displayer.update()
        digit_displayer.show_text()
        button.update()
        button.show_button()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            listener(event)
        pygame.display.flip()


if __name__ == "__main__":
    test()