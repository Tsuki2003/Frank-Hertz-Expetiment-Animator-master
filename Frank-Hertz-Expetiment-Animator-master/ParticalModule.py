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

        # 支持独立的纵向/横向磁场：分别使用 state.axial_enabled/transverse_enabled
        # 下面的处理比较近似——并不是精确解，更多是为了视觉上表现“偏转/聚焦”的效果。
        # 注：这里的系数和算法是我调出来的经验值，可能存在物理上的瑕疵，若你是物理学家，别急着投诉我。
        axial_on = getattr(self.tube.state, 'axial_enabled', False)
        trans_on = getattr(self.tube.state, 'transverse_enabled', False)
        axial_dir = getattr(self.tube.state, 'axial_direction', 1)
        sign = getattr(self.tube.state, 'transverse_direction', getattr(self.tube.state, 'magnet_direction', 1))
        if trans_on or axial_on:
            b_strength_trans = getattr(self.tube.state, 'transverse_strength', 0.0) if trans_on else 0.0
            b_strength_axial = getattr(self.tube.state, 'axial_strength', 0.0) if axial_on else 0.0
            # 先处理横向 B⊥ 导致的侧向偏转（旋转速度方向）
            if b_strength_trans > 0 and 140 <= self.ball_rect.centerx <= 520:
                angle = sign * 0.06 * (b_strength_trans/5.0) * (1.0 + abs(self.vx) * 0.2)
                old_vx = self.vx
                old_vy = self.vy
                self.vx = old_vx * cos(angle) - old_vy * sin(angle)
                self.vy = old_vx * sin(angle) + old_vy * cos(angle)
            # 再处理轴向 Bₗ 导致的磁聚焦（抑制横向发散并施加回复力）
            if b_strength_axial > 0:
                center_y = 150
                # 强度按档位比例缩放，使 25 mT 有明显效果
                self.vy *= max(0.02, 1.0 - 0.12 * (b_strength_axial/5.0))
                dy = self.ball_rect.centery - center_y
                self.vy += -0.004 * (b_strength_axial/5.0) * axial_dir * dy

        speed = self.velocity
        max_speed = 5.2
        if speed > max_speed:
            scale = max_speed / speed
            self.vx *= scale
            self.vy *= scale

    @property
    def velocity(self):
        return (self.vx**2 + self.vy**2) ** 0.5


