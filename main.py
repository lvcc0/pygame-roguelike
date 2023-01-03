import pygame as pg
import os
import sys
from random import randint, choice

from util import list_connect


pg.init()
SIZE = WIDTH, HEIGHT = 1280, 720
SCALED_SIZE = S_WIDTH, S_HEIGHT = [i // 1 for i in SIZE]
screen = pg.display.set_mode(SIZE)
display = pg.Surface(SCALED_SIZE)

FPS = 60
clock = pg.time.Clock()

all_sprites = pg.sprite.Group()
player_group = pg.sprite.Group()
tiles_group = pg.sprite.Group()
walls_group = pg.sprite.Group()

rooms = [[], [], [], [], []]  # index as a room type
for file in os.listdir(os.path.join('data', 'levels')):
    with open(os.path.join('data', 'levels', file), 'r') as f:
        rooms[int(file[0])].append([line.rstrip('\n') for line in list(f)])


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
                last_room = x, y
                break

    map = [[j for j in list_connect(*[rooms[i][randint(0, len(rooms[i]) - 1)] for i in line]) if j] for line in room_types]
    return list_connect([['1'] for _ in range(size * 8)], [j for sub in map for j in sub], [['1'] for _ in range(size * 8)])


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
    x, y = None, None
    for y in range(len(map)):
        for x in range(len(map[y])):
            if map[y][x] in ['0', '@']:
                Tile('empty', x, y)
            if map[y][x] == '1':
                Tile('wall', x, y)

    return x, y


# initializing all sprite images
tile_images = {
    'empty': load_image('empty.png'),
    'wall': load_image('wall.png')
}
player_image = load_image('player.png')
tile_size = 16


class Tile(pg.sprite.Sprite):
    def __init__(self, tile_id, x, y):
        if tile_id == 'empty':
            super().__init__(tiles_group, all_sprites)
        else:
            super().__init__(tiles_group, all_sprites, walls_group)

        self.image = tile_images[tile_id]
        self.rect = self.image.get_rect().move(tile_size * x, tile_size * y)


class Player(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(player_group, all_sprites)

        self.x = x
        self.y = y
        self.image = player_image
        self.rect = self.image.get_rect().move(tile_size * x, tile_size * y)

        self.speed = 2
        self.y_momentum = 0

    def move(self, movement):
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self.rect.x += movement[0]

        hit_list = [tile for tile in walls_group if self.rect.colliderect(tile)]
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.rect.left
                collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = tile.rect.right
                collision_types['left'] = True

        self.rect.y += movement[1]
        hit_list = [tile for tile in walls_group if self.rect.colliderect(tile)]
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.rect.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = tile.rect.bottom
                collision_types['top'] = True

        return collision_types


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - S_WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - S_HEIGHT // 2)


def main():
    level = generate_level(5)

    level_x, level_y = load_level(level)
    moving_right = moving_left = False
    air_timer = 0

    spawns = []
    for line in enumerate(level[:8]):
        possibles = [i for i in enumerate(line[1]) if i[1] == '@']
        spawns += [(i[0], line[0]) for i in possibles]

    spawn_x, spawn_y = choice(spawns)
    player = Player(spawn_x, spawn_y)
    camera = Camera()

    run = True
    while run:
        display.fill((0, 0, 0))

        player_movement = [0, 0]
        if moving_right:
            player_movement[0] += player.speed
        if moving_left:
            player_movement[0] -= player.speed

        player_movement[1] += player.y_momentum
        player.y_momentum += 0.4
        if player.y_momentum > 4:
            player.y_momentum = 6

        collisions = player.move(player_movement)

        if collisions['bottom']:
            air_timer = 0
            player.y_momentum = 0
        else:
            air_timer += 1

        camera.update(player)
        for sprite in all_sprites:
            camera.apply(sprite)

        all_sprites.draw(display)
        player_group.draw(display)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
                sys.exit()
            if event.type == pg.KEYDOWN:
                key = pg.key.get_pressed()
                moving_left = key[pg.K_a] or key[pg.K_LEFT]
                moving_right = key[pg.K_d] or key[pg.K_RIGHT]
                if key[pg.K_w] or key[pg.K_UP] or key[pg.K_SPACE]:
                    if air_timer < 5:
                        player.y_momentum = -5
            if event.type == pg.KEYUP:
                key = pg.key.get_pressed()
                moving_left = key[pg.K_a] or key[pg.K_LEFT]
                moving_right = key[pg.K_d] or key[pg.K_RIGHT]

        screen.blit(pg.transform.scale(display, SIZE), (0, 0))
        pg.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
    pg.quit()
