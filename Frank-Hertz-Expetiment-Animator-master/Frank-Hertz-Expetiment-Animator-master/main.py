import sys
import pygame

from Panel import Panel
from StateModule import State
from BasicModule import get_screen

# 程序入口
# 说明：
#  这个程序改造自网上的开源代码，改动过程中夹杂着大量折腾和妥协，
#  有些注释里写着我的牢骚——如果读起来情绪化，请理解那是调试时的心声。
#  能跑起来就是胜利，若你发现奇怪的注释或看不懂的实现，先别急着怀疑自己，
#  多半是我在临时修补处留下的痕迹

def main():
    pygame.init()

    screen = get_screen()

    state = State()
    panel = Panel(screen, state)
    listeners = panel.listener
    pygame.display.set_caption("陆家圆弗兰克赫兹实验仿真作业")

    while True:
        screen.fill((100,170,220))
        panel.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            panel.update(event)
            for listener in listeners:
                listener(event)
        pygame.display.flip()

if __name__ == "__main__":
    main()
