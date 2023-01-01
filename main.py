import pygame as pg
import os
import sys
from random import randint, choice

from util import list_connect


pg.init()
SIZE = WIDTH, HEIGHT = 200, 200
screen = pg.display.set_mode(SIZE)

FPS = 60
clock = pg.time.Clock()

all_sprites = pg.sprite.Group()
player_group = pg.sprite.Group()
tiles_group = pg.sprite.Group()
walls_group = pg.sprite.Group()


templates = []
for file in os.listdir(os.path.join('data', 'levels')):
    with open(os.path.join('data', 'levels', file), 'r') as f:
        templates.append([line.rstrip('\n') for line in list(f)])


def generate_level(size):
    room_types = [[0] * size for _ in range(size)]
    x, y = randint(0, size - 1), 0
    room_types[y][x] = 1

    dir = randint(0, 4)  # direction: (0, 1) = left; (2, 3) = right; (4) = down
    while True:
        if dir in (0, 1):  # going left
            if x > 0:
                if not room_types[y][x - 1]:
                    x, y = x - 1, y
                    room_types[y][x] = 1
                else:
                    dir = randint(0, 4)
            else:
                dir = randint(2, 4)
        elif dir in [2, 3]:  # going right
            if x < size - 1:
                if not room_types[y][x + 1]:
                    x, y = x + 1, y
                    room_types[y][x] = 1
                    dir = randint(0, 4)
                else:
                    dir = randint(0, 4)
            else:
                dir = choice(seq=[0, 1, 4])
        elif dir == 4:  # going down
            if y < size - 1:
                x, y = x, y + 1
                room_types[y - 1][x] = 4 if room_types[y - 2][x] in [2, 4] and y - 2 >= 0 else 2
                room_types[y][x] = 3
                dir = randint(0, 4)
            else:
                break

    map = [[j for j in list_connect(*[templates[i] for i in line]) if j] for line in room_types]
    return [j for sub in map for j in sub]


def load_image(name, colorkey=None):
    fullname = os.path.join('data', 'images', name)
    image = pg.image.load(fullname)

    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()

    return image


def load_level(map):
    player, x, y = None, None, None
    for y in range(len(map)):
        for x in range(len(map[y])):
            if map[y][x] == '0':
                Tile('empty', x, y)
            if map[y][x] == '1':
                Tile('wall', x, y)

    return player, x, y  # player is None for now :P


# initializing all sprite images
tile_images = {
    'empty': load_image('grass.png'),
    'wall': load_image('box.png')
}

tile_width = tile_height = 50


class Tile(pg.sprite.Sprite):
    def __init__(self, tile_id, x, y):
        if tile_id == 'empty':
            super().__init__(tiles_group, all_sprites)
        else:
            super().__init__(tiles_group, all_sprites, walls_group)

        self.image = tile_images[tile_id]
        self.rect = self.image.get_rect().move(tile_width  * x, tile_height * y)


class Player():
    def __init__(self, x, y):
        super().__init__(player_group, all_sprites)

        self.x = x
        self.y = y

    def move(self):
        pass


def main():
    player, level_x, level_y = load_level(generate_level(4))

    run = True
    while run:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
            if event.type == pg.KEYDOWN:
                key = pg.key.get_pressed()
                if key[pg.K_a]:
                    pass

        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        player_group.draw(screen)

        pg.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
    pg.quit()
