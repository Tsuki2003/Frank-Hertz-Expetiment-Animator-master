import pygame

class PlotModule:
    def __init__(self, screen, x, y, state):
        self.screen = screen
        self.x = x
        self.y = y
        # 放大绘图框尺寸，不改动坐标轴映射逻辑
        self.w = 800
        self.h = 440
        self.state = state
        # X轴 默认 Ua 0‑80V；Y轴默认适配参考图像 0~25.0
        self.x_max = 80
        self.y_max = 25.0
        # BasicModule基类要求
        self.listener = []
        # 字体，SimHei支持中文；如乱码改为'Arial'
        self.font = pygame.font.SysFont('SimHei', 14)

    def clear_data(self):
        """切换气体时清空历史UI采样数据"""
        self.state.helper['UI'].clear()

    def transform(self, u, ie):
        """物理值转画布像素坐标，完全保留原始逻辑不修改"""
        # 限定输入值到绘图范围，避免越界
        u_clamped = max(0.0, min(u, self.x_max))
        ie_clamped = max(0.0, min(ie, self.y_max))
        px = self.x + (u_clamped / self.x_max) * self.w
        py = self.y + self.h - (ie_clamped / self.y_max) * self.h
        # 再次夹紧到像素框内，确保不会画到坐标轴外
        px = max(self.x + 1, min(px, self.x + self.w - 1))
        py = max(self.y + 1, min(py, self.y + self.h - 1))
        return int(px), int(py)

    def update(self):
        # 绘图区白底+外框
        pygame.draw.rect(self.screen, (255, 255, 255), (self.x, self.y, self.w, self.h))
        pygame.draw.rect(self.screen, (0, 0, 0), (self.x, self.y, self.w, self.h), 2)

        # 绘制X、Y坐标轴
        pygame.draw.line(self.screen, (0, 0, 0),
                         (self.x, self.y + self.h),
                         (self.x + self.w, self.y + self.h), 2)
        pygame.draw.line(self.screen, (0, 0, 0),
                         (self.x, self.y),
                         (self.x, self.y + self.h), 2)

        # X轴刻度 0 20 40 60 80V
        for xv in [0, 20, 40, 60, 80]:
            px = self.x + (xv / self.x_max) * self.w
            text_surf = self.font.render(f"{xv}V", True, (0, 0, 0))
            self.screen.blit(text_surf, (px - 8, self.y + self.h + 3))

        # Y轴刻度 0 5 10 15 20 25
        for yv in [0, 5, 10, 15, 20, 25]:
            py = self.y + self.h - (yv / self.y_max) * self.h
            text_surf = self.font.render(f"{yv}", True, (0, 0, 0))
            self.screen.blit(text_surf, (self.x - 22, py - 6))

        ui_dict = self.state.helper['UI']
        if len(ui_dict) < 2:
            return

        # 按电压升序排序采样点
        sorted_points = sorted(ui_dict.items(), key=lambda item: item[0])
        point_list = []
        for u, ie in sorted_points:
            px, py = self.transform(u, ie)
            point_list.append((px, py))
            # 只在绘图区内绘制点
            if self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h:
                pygame.draw.circle(self.screen, (200, 0, 0), (px, py), 2)

        # 平滑曲线插值：使用 Catmull-Rom 样条
        def catmull_rom(p0, p1, p2, p3, t):
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
            # 夹紧样条点到绘图区内，防止插值导致越界
            x = max(self.x + 1, min(x, self.x + self.w - 1))
            y = max(self.y + 1, min(y, self.y + self.h - 1))
            return int(x), int(y)

        smooth_points = []
        n = len(point_list)
        if n == 2:
            smooth_points = point_list
        else:
            for i in range(n - 1):
                p0 = point_list[max(i - 1, 0)]
                p1 = point_list[i]
                p2 = point_list[i + 1]
                p3 = point_list[min(i + 2, n - 1)]
                for step in range(10):
                    t = step / 10
                    smooth_points.append(catmull_rom(p0, p1, p2, p3, t))
            smooth_points.append(point_list[-1])

        # 绘制平滑曲线
        if smooth_points:
            pygame.draw.lines(self.screen, (180, 0, 0), False, smooth_points, 2)
            # 识别波峰（局部极大）与波谷（局部极小）并显示坐标（全部列出）
            values = [ie for (_, ie) in sorted_points]
            us = [u for (u, _) in sorted_points]
            peaks = []
            troughs = []
            n = len(values)
            for i in range(1, n-1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    peaks.append((us[i], values[i]))
                if values[i] < values[i-1] and values[i] < values[i+1]:
                    troughs.append((us[i], values[i]))

            # 在曲线上标注所有峰/谷点并在右上角列出坐标
            info_x = self.x + self.w - 220
            info_y = self.y + 8
            max_show = 12
            count = 0
            for p in peaks[:max_show]:
                px, py = self.transform(p[0], p[1])
                pygame.draw.circle(self.screen, (20, 80, 200), (px, py), 4)
                text = self.font.render(f"峰 Ua={p[0]:.1f}V Ie={p[1]:.2f}", True, (20, 20, 20))
                self.screen.blit(text, (info_x, info_y))
                info_y += 16
                count += 1
            for t in troughs[:max_show]:
                px, py = self.transform(t[0], t[1])
                pygame.draw.circle(self.screen, (20, 180, 20), (px, py), 4)
                text = self.font.render(f"谷 Ua={t[0]:.1f}V Ie={t[1]:.2f}", True, (20, 20, 20))
                self.screen.blit(text, (info_x, info_y))
                info_y += 16
                count += 1
            # 注：峰/谷检测使用简单的局部极值法，容易对噪声敏感；若要严谨分析，建议改为平滑+阈值或二阶导数，这是ai给我的建议，我不会实现，拉倒
