import pygame as pg
import sys


def con(*lists):  # stand for connect (list connect)
    res = [[]]
    for i in range(max([len(lst) for lst in lists])):
        res.append([])
        for lst in lists:
            if i < len(lst):
                res[i] += lst[i]

    return res


def draw_text(text, size, color, surface, x, y):
    font = pg.font.SysFont('arial', size)
    obj = font.render(text, 1, color)
    rect = obj.get_rect().move(x, y)
    surface.blit(obj, rect)


def terminate():
    pg.quit()
    sys.exit()
