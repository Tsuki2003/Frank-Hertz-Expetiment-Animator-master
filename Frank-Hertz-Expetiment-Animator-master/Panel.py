import pygame
import sys
from functools import partial

from BasicModule import BasicModule, get_screen
from RectModule import LabelModule, ButtonModule, DisplayModule
from ScrollBarModule import ScrollBarModule
from StateModule import State
from Tube import Tube
from PlotModule import PlotModule


class Button:
    def __init__(self, screen, x, y, w, h, text, callback):
        self.screen = screen
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont(None,24)
        self.color_normal = (60,60,180)
        self.color_hover = (100,100,220)
        self.color = self.color_normal

    def draw(self):
        pygame.draw.rect(self.screen, self.color, self.rect)
        surf = self.font.render(self.text, True, (255,255,255))
        self.screen.blit(surf, surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.color = self.color_hover
            else:
                self.color = self.color_normal
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                print(f"点击按钮:{self.text}")
                self.callback()


class VoltageControler(BasicModule):
    def __init__(self, screen, x, y, text, max_value, state):
        super(VoltageControler, self).__init__(screen)

        label = LabelModule(screen, x=x, y=y, text=text)
        scrollbar = ScrollBarModule(screen, x=x+60, y=y, max_value=max_value, set_value=state.set_param(text))
        digit_displayer = DisplayModule(screen, x=x+210, y=y, get_text=lambda:"{:.2f}".format(getattr(state, text)))

        self.add_sub_module('label', label)
        self.add_sub_module('scrollbar', scrollbar)
        self.add_sub_module('digit_displayer', digit_displayer)

    def update(self):
        self.sub_module.label.show_text()
        self.sub_module.scrollbar.update()
        self.sub_module.digit_displayer.update()
        self.sub_module.digit_displayer.show_text()


class CurrentDisplayer(BasicModule):
    def __init__(self, screen, x, y, state):
        super(CurrentDisplayer, self).__init__(screen)

        self.add_sub_module('current_displayer',
                            DisplayModule(screen, x=x+20, y=y+20,
                                          get_text=lambda:"{:.2f}".format(getattr(state, 'Ie'))))
        self.add_sub_module('plot_button', ButtonModule(screen, x=x+180, y=y+20, state=state))
        self.add_sub_module('plot', PlotModule(screen, x=x+20, y=y+80, state=state))

    def update(self):
        self.sub_module.current_displayer.update()
        self.sub_module.current_displayer.show_text()
        self.sub_module.plot_button.update()
        self.sub_module.plot_button.show_button()
        self.sub_module.plot.update()


class Panel(BasicModule):
    def __init__(self, screen, state):
        super(Panel, self).__init__(screen)
        self.screen = screen
        self.state = state

        self.gas_buttons = []
        btn_w = 80
        btn_h = 30
        btn_hg = Button(screen,200,15,btn_w,btn_h,"汞 Hg",partial(self.switch_gas,"Hg"))
        btn_ar = Button(screen,300,15,btn_w,btn_h,"氩 Ar",partial(self.switch_gas,"Ar"))
        btn_ne = Button(screen,400,15,btn_w,btn_h,"氖 Ne",partial(self.switch_gas,"Ne"))
        btn_he = Button(screen,500,15,btn_w,btn_h,"氦 He",partial(self.switch_gas,"He"))

        self.gas_buttons.append(btn_hg)
        self.gas_buttons.append(btn_ar)
        self.gas_buttons.append(btn_ne)
        self.gas_buttons.append(btn_he)

        self.add_sub_module('Uf', VoltageControler(screen, x=10, y=320, text='Uf', max_value=1, state=state))
        self.add_sub_module('Ug', VoltageControler(screen, x=10, y=400, text='Ug', max_value=3, state=state))
        self.add_sub_module('Ua', VoltageControler(screen, x=10, y=480, text='Ua', max_value=80, state=state))
        self.add_sub_module('Ue', VoltageControler(screen, x=10, y=560, text='Ue', max_value=15, state=state))

        self.ua_increment_button = Button(screen, 920, 20, 120, 32, '+0.5V Ua', self.increase_Ua)
        self.ua_scan_button = Button(screen, 920, 60, 120, 32, 'Auto Scan Ua', self.toggle_auto_scan)
        self.state.helper['auto_scan'] = False
        self.auto_scan_timer = 0

        self.add_sub_module('Ie', CurrentDisplayer(screen, x=300, y=300, state=state))
        self.add_sub_module('tube', Tube(screen, state))

    def switch_gas(self, gas_name):
        """切换气体，同时重置管内粒子+清空绘图历史曲线"""
        self.state.gas_type = gas_name
        print(f"切换气体到：{gas_name}")
        if hasattr(self.sub_module["tube"], "reset_particles"):
            self.sub_module["tube"].reset_particles()
        # 清空弗兰克赫兹UI图像历史数据
        plot_obj = self.sub_module["Ie"].sub_module["plot"]
        plot_obj.clear_data()

    def increase_Ua(self):
        self.state.Ua += 0.5
        if self.state.Ua > 80:
            self.state.Ua = 80
        print(f"Ua 已增加到 {self.state.Ua:.2f} V")

    def toggle_auto_scan(self):
        self.state.helper['auto_scan'] = not self.state.helper['auto_scan']
        if self.state.helper['auto_scan']:
            self.state.helper['plot'] = True
            self.state.helper['UI'].clear()
            self.state.Ua = 0.0
            self.auto_scan_timer = 0
            print("开始自动扫描 Ua")
        else:
            print("停止自动扫描 Ua")

    def update(self, event=None):
        for sub_module in self.sub_module.values():
            sub_module.update()
        for btn in self.gas_buttons:
            btn.draw()
        self.ua_increment_button.draw()
        self.ua_scan_button.draw()

        if self.state.helper.get('auto_scan', False):
            self.auto_scan_timer += 1
            if self.auto_scan_timer >= 12:
                self.auto_scan_timer = 0
                self.state.Ua += 0.5
                if self.state.Ua > 80:
                    self.state.Ua = 80
                    self.state.helper['auto_scan'] = False
                    print("自动扫描 Ua 已完成")

        if event is not None:
            for btn in self.gas_buttons:
                btn.handle_event(event)
            self.ua_increment_button.handle_event(event)
            self.ua_scan_button.handle_event(event)
