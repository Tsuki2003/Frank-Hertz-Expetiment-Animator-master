from dotteddict import dotteddict

class State(object):
    def __init__(self):
        self.Uf = 0
        self.Ug = 0
        self.Ua = 0
        self.Ue = 0
        self.Ie = 0
        self.magnet_enabled = False
        self.magnet_strength = 0.0
        # 磁场方向：'transverse' 横向（垂直于管轴），'axial' 轴向（沿管轴）
        self.magnet_orientation = 'transverse'
        self.magnet_direction = 1
        # 新增：独立的轴向和横向磁场开关与强度（单位：mT，档位 0,5,10,15,20,25）
        self.axial_enabled = False
        self.transverse_enabled = False
        self.axial_strength = 0.0
        self.transverse_strength = 0.0
        self.helper = {
            'plot': False,
            'UI': {},
            'plot_temp': False
        }
        self.gas_type = "Ne"   # 默认氖
        self.gas_config = {
            "Hg": {"v0":9.2, "name":"汞 Hg"},
            "Ar": {"v0":13.8, "name":"氩 Ar"},
            "Ne": {"v0":16.7, "name":"氖 Ne"},
            "He": {"v0":24.6, "name":"氦 He"}
        }
        

    def set_param(self, key):
        def set_value(value):
            if key == 'Uf':
                self.Uf = value
            if key == 'Ug':
                self.Ug = value
            if key == 'Ua':
                self.Ua = value
            if key == 'Ue':
                self.Ue = value
            if key == 'Ie':
                self.Ie = value
            if key == 'magnet_strength':
                self.magnet_strength = value
            if key == 'magnet_orientation':
                # 允许通过setter变更方向（接收字符串）
                if value in ('transverse', 'axial'):
                    self.magnet_orientation = value
            if key == 'axial_strength':
                try:
                    self.axial_strength = float(value)
                except Exception:
                    pass
            if key == 'transverse_strength':
                try:
                    self.transverse_strength = float(value)
                except Exception:
                    pass
            if key == 'axial_enabled':
                try:
                    self.axial_enabled = bool(value)
                except Exception:
                    pass
            if key == 'transverse_enabled':
                try:
                    self.transverse_enabled = bool(value)
                except Exception:
                    pass
        return set_value