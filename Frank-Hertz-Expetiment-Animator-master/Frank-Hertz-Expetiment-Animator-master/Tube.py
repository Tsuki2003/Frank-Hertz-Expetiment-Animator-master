import pygame
import math
import time
from ParticalModule import Atom, Electron
from BasicModule import BasicModule
from pygame.sprite import Group
import random
from math import pi, sin, cos


def collided(e, a):
    dist = ((e.ball_rect.centerx - a.ball_rect.centerx) ** 2 + (e.ball_rect.centery - a.ball_rect.centery) ** 2) ** 0.5
    return dist < 4


class Tube(BasicModule):
    def __init__(self, screen, state):
        super(Tube, self).__init__(screen)
        self.state = state

        # 仅保存线段坐标，不再存储draw.line返回的Rect
        self.p_up_start = (20, 20)
        self.p_up_end = (580, 20)

        self.p_down_start = (20, 280)
        self.p_down_end = (580, 280)

        self.p_collect_start = (560, 20)
        self.p_collect_end = (560, 280)

        self.p_arid_start = (440, 40)
        self.p_arid_end = (440, 260)

        self.p_control_start = (140, 40)
        self.p_control_end = (140, 260)

        self.image = pygame.image.load('images/light.png')
        self.image_rect = self.image.get_rect()
        self.image_rect.centery = 150
        self.image_rect.centerx = 20
        self.mag_font = pygame.font.SysFont('SimHei', 16)

        self.atoms = Group()
        self.electrons = Group()

        self.generate_atoms()
        self.delete_electrons = []
        self.collected_electrons = []

        # 电流滤波与采样计时器，平滑优化参数
        self.smoothed_Ie = 0.0
        # 减小 alpha 让电流变化更缓慢、更平滑
        self.alpha = 0.04
        self.sample_timer = 0
        self.noise_phase = random.random() * 2 * pi
        self.current_window = 1.5  # 采样窗口，秒

    def reset_particles(self):
        self.atoms.empty()
        self.electrons.empty()
        self.delete_electrons.clear()
        self.collected_electrons.clear()
        self.smoothed_Ie = 0.0
        self.sample_timer = 0
        self.generate_atoms()
        print(f"Tube已重置粒子，当前gas_type={self.state.gas_type}")

    def frank_hertz_current(self, ua, apply_magnet=False):
        v0 = self.state.gas_config[self.state.gas_type]["v0"]
        effective_ua = max(0.0, ua - self.state.Ug)
        emission = max(0.3, self.state.Uf)
        suppression = 1.0 + self.state.Ue * 0.08
        # 兼容旧字段：如果使用全局 magnet_enabled/magnet_strength，则以其为基准
        magnet_strength = 0.0
        if apply_magnet:
            if getattr(self.state, 'magnet_enabled', False) and getattr(self.state, 'magnet_strength', 0.0) > 0:
                magnet_strength = self.state.magnet_strength
            # 优先使用独立轴向/横向档位来影响峰位/宽度（作为局部微调）
            # 这里定义一个简单的 shift/width/amplitude 基于横向强度的贡献
            transverse = getattr(self.state, 'transverse_strength', 0.0) if getattr(self.state, 'transverse_enabled', False) else 0.0
            axial = getattr(self.state, 'axial_strength', 0.0) if getattr(self.state, 'axial_enabled', False) else 0.0
            # 将档位 mT 缩放到 0..1 范围（以 25mT 为 max）
            t_norm = transverse / 25.0
            a_norm = axial / 25.0
            # combine for minor spectral shift and width modulation
            shift = 0.12 * magnet_strength + 0.8 * t_norm
            width_factor = 1.0 + 0.5 * t_norm
            amplitude_factor = max(0.2, 1.0 - 0.5 * t_norm)
            base_factor = max(0.35, 1.0 - 0.3 * a_norm)

        if self.state.gas_type == "Hg":
            base = max(0.0, effective_ua - 8.0) * 0.14 * base_factor
            centers = [v0 * n + 1.0 + 0.1 * (n - 1) + shift for n in range(1, 9)]
            amps = [5.5, 9.0, 11.0, 13.0, 14.5, 16.0, 17.0, 18.0]
            widths = [2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8]
            peak_sum = 0.0
            for amp, center, width in zip(amps, centers, widths):
                peak_sum += amp * amplitude_factor * math.exp(-((effective_ua - center) ** 2) / (2 * (width * width_factor) * (width * width_factor)))
            tail = max(0.0, effective_ua - centers[-1]) * 0.10 * base_factor
            current = (base + peak_sum + tail) * emission / suppression * 0.65
        else:
            base = max(0.0, effective_ua - 8.0) * 0.18 * base_factor
            centers = [v0 * n + 1.0 + 0.15 * (n - 1) + shift for n in range(1, 8)]
            amps = [5.5, 9.0, 11.0, 13.5, 15.0, 14.0, 12.0]
            widths = [2.4, 2.8, 3.2, 3.5, 3.9, 4.4, 4.8]
            peak_sum = 0.0
            for amp, center, width in zip(amps, centers, widths):
                peak_sum += amp * amplitude_factor * math.exp(-((effective_ua - center) ** 2) / (2 * (width * width_factor) * (width * width_factor)))
            tail = max(0.0, effective_ua - centers[-1]) * 0.16 * base_factor
            current = (base + peak_sum + tail) * emission / suppression

        if self.state.gas_type == "Ar":
            current *= 0.85
        elif self.state.gas_type == "He":
            current *= 0.45

        # 结合独立轴向/横向档位影响电流：横向降低收集效率，轴向提升（聚焦）
        if apply_magnet:
            # 基于旧字段的全局弱影响
            if getattr(self.state, 'magnet_enabled', False) and getattr(self.state, 'magnet_strength', 0.0) > 0:
                ms = self.state.magnet_strength
                current *= max(0.05, 1.0 - 0.08 * ms)
                if effective_ua < 20:
                    current *= max(0.05, 1.0 - 0.05 * ms)
            # 横向：按横向强度衰减
            t = getattr(self.state, 'transverse_strength', 0.0) if getattr(self.state, 'transverse_enabled', False) else 0.0
            if t > 0:
                # 档位越高，损失越大；25 mT 导致最大衰减
                decay = min(0.95, 0.18 * (t/5.0))
                current *= max(0.02, 1.0 - decay)
            # 轴向：按轴向强度增强（聚焦）
            a = getattr(self.state, 'axial_strength', 0.0) if getattr(self.state, 'axial_enabled', False) else 0.0
            if a > 0:
                boost = 0.10 * (a/5.0)
                current *= (1.0 + boost)
        return max(0.0, min(current, 25.0))

    def compute_current(self, ua):
        ideal = self.frank_hertz_current(ua, apply_magnet=True)
        now = time.time()
        recent_electrons = [t for t in self.collected_electrons if now - t <= self.current_window]
        electron_rate = len(recent_electrons) / max(self.current_window, 0.01)
        shot_noise = random.gauss(0.0, max(0.01, ideal * 0.02))
        wave_noise = math.sin(now * 1.2 + self.noise_phase + ua * 0.06) * 0.06
        pulse = max(0.0, electron_rate - 12.0) * 0.03
        raw_current = ideal + wave_noise + shot_noise + pulse
        self.noise_phase += 0.002
        raw_current = max(0.0, min(raw_current, 25.0))
        self.smoothed_Ie = self.smoothed_Ie * (1.0 - self.alpha) + raw_current * self.alpha
        return max(0.0, min(self.smoothed_Ie, 25.0))

    def draw(self):
        self.screen.blit(self.image, self.image_rect)
        pygame.draw.line(self.screen, (0, 0, 0), self.p_up_start, self.p_up_end)
        pygame.draw.line(self.screen, (0, 0, 0), self.p_down_start, self.p_down_end)
        pygame.draw.line(self.screen, (0, 0, 0), self.p_collect_start, self.p_collect_end)
        pygame.draw.line(self.screen, (100, 100, 100), self.p_arid_start, self.p_arid_end)
        pygame.draw.line(self.screen, (100, 100, 100), self.p_control_start, self.p_control_end)

        magnet_x, magnet_y = 220, 80
        magnet_w, magnet_h = 90, 120
        any_field = getattr(self.state, 'axial_enabled', False) or getattr(self.state, 'transverse_enabled', False) or getattr(self.state, 'magnet_enabled', False)
        body_color = (70, 70, 70) if not any_field else (95, 95, 95)
        pygame.draw.rect(self.screen, body_color, (magnet_x, magnet_y, magnet_w, magnet_h))
        pygame.draw.rect(self.screen, (220, 220, 220), (magnet_x + 8, magnet_y + 8, magnet_w - 16, magnet_h - 16), 2)

        pole_color_left = (255, 0, 0) if any_field else (180, 80, 80)
        pole_color_right = (0, 0, 255) if any_field else (90, 90, 180)
        pygame.draw.rect(self.screen, pole_color_left, (magnet_x + 16, magnet_y + 22, 18, 70))
        pygame.draw.rect(self.screen, pole_color_right, (magnet_x + 56, magnet_y + 22, 18, 70))

        # 标注磁铁示意，你知道照这个贴图有多麻烦吗，气死我了
        label = self.mag_font.render('磁铁', True, (0, 0, 0))
        self.screen.blit(label, (magnet_x + 18, magnet_y - 20))
        # 现在改为纵向/横向各自控制，旧的全局开关已移除
        state_label = self.mag_font.render('', True, (0, 0, 0))
        self.screen.blit(state_label, (magnet_x + 20, magnet_y + magnet_h + 8))

        # 根据不同磁场类型绘制不同的示意：横向用竖直箭头，轴向用聚焦光圈
        if getattr(self.state, 'transverse_enabled', False):
            field_color = (0, 120, 255)
            for i in range(8):
                x = magnet_x + 12 + i * 8
                pygame.draw.line(self.screen, field_color, (x, magnet_y + magnet_h + 10), (x + 6, magnet_y + magnet_h + 34), 2)
                pygame.draw.line(self.screen, field_color, (x + 6, magnet_y + magnet_h + 34), (x + 12, magnet_y + magnet_h + 10), 1)
            # 半透明覆盖表示作用区
            zone_color = (0, 50, 120, 40)
            overlay = pygame.Surface((300, 220), pygame.SRCALPHA)
            overlay.fill(zone_color)
            self.screen.blit(overlay, (140, 40))
            arrow_color = (0, 180, 255)
            for i in range(5):
                x = 160 + i * 55
                pygame.draw.line(self.screen, arrow_color, (x, 60), (x, 230), 1)
                pygame.draw.polygon(self.screen, arrow_color, [(x - 3, 65), (x + 3, 65), (x, 58)])
            b_label = self.mag_font.render('B⊥区', True, arrow_color)
            self.screen.blit(b_label, (320, 45))
        if getattr(self.state, 'axial_enabled', False):
            # 轴向：显示聚焦同心圈，颜色偏绿
            center_x = magnet_x + magnet_w//2
            center_y = magnet_y + magnet_h//2
            overlay = pygame.Surface((300, 220), pygame.SRCALPHA)
            # 更亮的轴向色
            zone_color = (0, 200, 100, 28)
            overlay.fill((0,0,0,0))
            for r in range(20, 120, 20):
                pygame.draw.circle(overlay, (0, 200, 100, 12), (150, 110), r, 2)
            self.screen.blit(overlay, (140, 40))
            a_label = self.mag_font.render('Bₗ区', True, (0, 160, 80))
            self.screen.blit(a_label, (320, 45))

    def generate_atoms(self):
        for _ in range(220):
            self.atoms.add(Atom(self.screen, x=random.random()*500+40, y=random.random()*240+30))

    def generate_electrons(self, ratio):
        for _ in range(2):
            if random.random() < ratio:
                self.electrons.add(Electron(self.screen, x=random.random()*60+20, y=random.random()*60+120, tube=self))

    def update(self):
        self.draw()
        self.atoms.update()
        self.electrons.update()
        for e in self.delete_electrons:
            self.electrons.remove(e)
        self.generate_electrons(ratio=self.state.Uf)

        # 碰撞逻辑：更确定性的非弹性散射以产生可重复的能量损失峰
        collisions = pygame.sprite.groupcollide(self.electrons, self.atoms, False, False, collided=collided)
        for e, atoms in collisions.items():
            v = e.velocity
            v0 = self.state.gas_config[self.state.gas_type]["v0"]

            # 如果电子能量足够达到激发阈值，执行确定性的非弹性碰撞：
            # 电子损失固定能量 v0（以速度平方差），并保持主要向右前进
            if v >= v0:
                v_res_sq = v**2 - v0**2
                if v_res_sq < 0:
                    v_res_sq = 0
                v_res = math.sqrt(v_res_sq)
                # 使电子主要向右（阳极方向），减小垂直分量
                e.vx = max(0.0, v_res)
                e.vy = 0.0
                for a in atoms:
                    a.activate_step = 100
            else:
                # 能量不足时做小角度弹性散射，保留一定的前向动量
                theta = (random.random() - 0.5) * 0.2
                e.vx = v * math.cos(theta)
                e.vy = v * math.sin(theta)

        self.state.Ie = self.compute_current(self.state.Ua)

        if self.state.helper.get('plot', False):
            ua_val = round(self.state.Ua, 1)
            self.state.helper['UI'][ua_val] = self.frank_hertz_current(self.state.Ua, apply_magnet=True)
