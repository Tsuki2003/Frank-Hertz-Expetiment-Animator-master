import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from StateModule import State
from Tube import Tube
from ParticalModule import Electron
import pygame


def test_magnet_field_changes_electron_velocity_direction():
    pygame.init()
    screen = pygame.display.set_mode((1200, 900))
    state = State()
    state.Ua = 20
    state.Ug = 5
    state.Uf = 0.3
    state.helper['plot'] = False
    tube = Tube(screen, state)

    e = Electron(screen, x=100, y=150, tube=tube)
    e.vx = 1.0
    e.vy = 0.2
    state.magnet_enabled = True
    state.magnet_strength = 0.5
    state.magnet_direction = 1

    vx_before = e.vx
    vy_before = e.vy
    e.update()
    vx_after = e.vx
    vy_after = e.vy

    assert vx_after != vx_before or vy_after != vy_before


def test_field_direction_can_be_reversed_per_axis():
    state = State()

    state.reverse_axial_direction()
    assert state.axial_direction == -1

    state.reverse_transverse_direction()
    assert state.transverse_direction == -1

    state.reverse_axial_direction()
    assert state.axial_direction == 1
