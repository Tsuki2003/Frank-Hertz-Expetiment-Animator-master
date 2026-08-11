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
        self.magnet_direction = 1
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
        return set_value