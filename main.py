import pygame as pg
import os
import sys
from random import randint, choice, sample

import util


pg.init()
SIZE = WIDTH, HEIGHT = 1280, 720
SCALED_SIZE = S_WIDTH, S_HEIGHT = [i // 4 for i in SIZE]
screen = pg.display.set_mode(SIZE)
display = pg.Surface(SCALED_SIZE)

FPS = 60
clock = pg.time.Clock()

all_sprites = pg.sprite.Group()
player_group = pg.sprite.Group()
tiles_group = pg.sprite.Group()
walls_group = pg.sprite.Group()
enemy_group = pg.sprite.Group()
weapon_group = pg.sprite.Group()
exit_group = pg.sprite.Group()

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
                break

    map = [[j for j in util.list_connect(*[rooms[i][randint(0, len(rooms[i]) - 1)] for i in line]) if j] for line in room_types]
    return util.list_connect([['1'] for _ in range(size * 8)], [j for sub in map for j in sub], [['1'] for _ in range(size * 8)])


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
            if map[y][x] in ['0', '@', 'e', 'x']:
                Tile('empty', x, y)
            if map[y][x] == '1':
                Tile('wall', x, y)

    return x, y


# initializing all sprite images
tile_images = {
    'empty': load_image('empty.png'),
    'wall': load_image('wall.png'),
    'exit': load_image('exit.png')
}
enemy_images = {
    'slime': load_image('slime.png')
}

player_sheets = {
    'idle': (load_image('player_idle4x1.png'), (4, 1)),
    'run': (load_image('player_run4x1.png'), (4, 1)),
    'death': (load_image('player_death8x1.png'), (8, 1))
}

slash_image = load_image('slash.png')
tile_size = 16


class Tile(pg.sprite.Sprite):
    def __init__(self, tile_id, x, y):
        if tile_id == 'empty':
            super().__init__(tiles_group, all_sprites)
        elif tile_id == 'exit':
            super().__init__(tiles_group, all_sprites, exit_group)
        else:
            super().__init__(tiles_group, all_sprites, walls_group)

        self.image = tile_images[tile_id]
        self.rect = self.image.get_rect().move(tile_size * x, tile_size * y)


class Entity(pg.sprite.Sprite):
    def __init__(self, x, y, groups, hp, sheets):
        super().__init__(*groups)

        self.x = x
        self.y = y

        self.flipped = False
        if type(sheets) == dict:
            self.animated = True

            self.sheets = sheets

            self.anim_timer = 8  # frames per animation frame change
            self.cur_anim_timer = self.anim_timer

            self.frames = []
            self.action = 'idle'
            self.cut_sheet(sheets[self.action], *self.sheets[self.action][1])
            self.cur_frame = 0
            
            self.image = self.frames[self.cur_frame]
        else:
            self.animated = False
            self.image = sheets
        
        self.dead = False
        self.rect = self.image.get_rect().move(tile_size * x, tile_size * y)
        self.hp = hp
        self.max_hp = self.hp
        self.max_invincible_frames = 60
        self.invincible_frames = 0

    def cut_sheet(self, sheet, cols, rows):
        self.frames = []
        self.anim_rect = pg.Rect(0, 0, sheet[0].get_width() // cols, sheet[0].get_height() // rows)

        for i in range(rows):
            for j in range(cols):
                frame_loc = self.anim_rect.w * j, self.anim_rect.h * i
                self.frames.append(sheet[0].subsurface(pg.Rect(frame_loc, self.anim_rect.size)))

    def change_action(self, action, frame, new_value):
        if action != new_value:
            self.action = new_value
            self.cut_sheet(self.sheets[self.action], *self.sheets[self.action][1])
            frame = 0
        
        return self.action, frame

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

    def get_hit(self, attacker):
        if not self.invincible_frames:
            self.hp -= attacker.damage
            self.invincible_frames = self.max_invincible_frames

    def die(self):
        if self.dead:
            return
        else:
            self.dead = True

        if self.animated:
            if 'death' in self.sheets.keys():
                self.change_action(self.action, self.cur_frame, 'death')
        else:
            self.kill()

    def update(self):
        if self.hp != self.max_hp:
            pg.draw.rect(display, (200, 0, 0), (self.rect.x, self.rect.y - 5, self.rect.width, 2))
            pg.draw.rect(display, (50, 255, 50), (self.rect.x, self.rect.y - 5, self.rect.width * self.hp // self.max_hp, 2))

        if self.hp <= 0:
            self.die()

        if self.animated:
            if not self.cur_anim_timer:
                self.cur_frame = (self.cur_frame + 1) % len(self.frames)
                self.image = pg.transform.flip(self.frames[self.cur_frame], self.flipped, False)
                self.cur_anim_timer = self.anim_timer
            else:
                self.cur_anim_timer -= 1

            if self.dead and self.cur_frame == self.sheets['death'][1][0] - 1:
                self.kill()
        else:
            self.image = pg.transform.flip(self.image, self.flipped, False)

        if self.invincible_frames != 0:
            mask = pg.mask.from_surface(self.image).to_surface()
            mask.set_colorkey((0, 0, 0))
            mask.set_alpha(255 * (self.invincible_frames / self.max_invincible_frames))
            display.blit(mask, (self.rect.x - 1, self.rect.y))
            display.blit(mask, (self.rect.x + 1, self.rect.y))
            display.blit(mask, (self.rect.x, self.rect.y - 1))
            display.blit(mask, (self.rect.x, self.rect.y + 1))

            self.invincible_frames -= 1


class Weapon(Entity):
    def __init__(self, master, timer):
        image = pg.transform.flip(slash_image, master.flipped, False)
        super().__init__(master.rect.center[0] // 16, master.rect.y // 16, (all_sprites, weapon_group), 1, image)
        self.damage = 1

        self.master = master
        self.timer = timer

        if master.flipped:
            self.rect = self.rect.move(-self.rect.width - 8, 0)
        else:
            self.rect = self.rect.move(8, 0)

    def set_timer(self, timer):
        self.timer = timer

    def update(self):
        super().update()

        self.image.set_alpha(255 * (self.timer / 10))
        for sprite in pg.sprite.spritecollide(self, enemy_group, False):
            sprite.get_hit(self)


class Player(Entity):
    def __init__(self, x, y, score):
        super().__init__(x, y, (player_group, all_sprites), 5, player_sheets) 
        self.y_momentum = 0
        self.speed = 2
        self.attack_timer = 0
        self.slashes = []
        self.score = score

    def attack(self):
        self.attack_timer = 10

        if self.attack_timer != 0:
            weapon = Weapon(self, self.attack_timer)
            self.slashes.append(weapon)

    def add_score(self, score):
        self.score += score

    def update(self):
        super().update()

        if self.attack_timer != 0:
            self.attack_timer -= 1
            [sprite.set_timer(self.attack_timer) for sprite in self.slashes]
        else:
            [sprite.kill() for sprite in self.slashes]

        if self.dead and self.cur_frame == self.sheets['death'][1][0] - 1:
            for sprite in all_sprites:
                sprite.kill()

            lose_screen(self.score)
        
        if pg.sprite.spritecollide(self, exit_group, False):
            win_screen(self.score)


class Enemy(Entity):
    def __init__(self, x, y, image, hp, damage, price):
        super().__init__(x, y, (all_sprites, enemy_group), hp, image)
        self.prive = price
        self.damage = damage
        self.last_attacker = None

    def get_hit(self, attacker):
        super().get_hit(attacker)
        self.last_attacker = attacker

    def die(self):
        super().die()
        self.last_attacker.master.add_score(self.price)


class Slime(Enemy):
    def __init__(self, x, y):
        self.price = 10

        super().__init__(x, y, enemy_images['slime'], 3, 1, self.price)
        self.movement = [1, 0]
        self.max_invincible_frames = 30
        
    def update(self):
        super().update()

        collisions = self.move(self.movement)

        if collisions['right'] or collisions['left']:
            self.movement[0] = -self.movement[0]

        next_step_rect = self.rect.move(self.rect.width * self.movement[0], 4)
        if next_step_rect.collidelist(list(walls_group)) == -1:
            self.movement[0] = -self.movement[0]

        if pg.sprite.spritecollide(self, player_group, False):
            self.hit()

    def hit(self):
        player = pg.sprite.spritecollide(self, player_group, False)[0]
        player.get_hit(self)


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


def start_screen():
    click = False

    while True:
        display.fill((24, 20, 37))
        m_pos = [i // 4 for i in pg.mouse.get_pos()]
        
        util.draw_text(':DDD', 14, (255, 255, 255), display, 10, 10)

        play_b = pg.Rect(10, 50, 120, 35)

        if play_b.collidepoint(m_pos):
            if click:
                main(0)

        pg.draw.rect(display, (255, 255, 255), play_b)
        util.draw_text('start', 30, (24, 20, 37), display, play_b.x + 10, play_b[1])

        click = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                util.terminate()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    util.terminate()
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        screen.blit(pg.transform.scale(display, SIZE), (0, 0))
        pg.display.flip()
        clock.tick(FPS)


def lose_screen(final_score):
    click = False

    while True:
        display.fill((24, 20, 37))
        m_pos = [i // 4 for i in pg.mouse.get_pos()]

        util.draw_text('u dead :(', 14, (255, 255, 255), display, 10, 10)
        util.draw_text(f'final score: {final_score}', 14, (255, 255, 255), display, 150, 10)

        restart_b = pg.Rect(10, 50, 120, 35)
        end_b = pg.Rect(10, 100, 120, 35)

        if restart_b.collidepoint(m_pos):
            if click:
                for sprite in all_sprites:
                    sprite.kill()

                main(0)
        if end_b.collidepoint(m_pos):
            if click:
                util.terminate()

        pg.draw.rect(display, (255, 255, 255), restart_b)
        util.draw_text('restart', 30, (24, 20, 37), display, restart_b.x + 10, restart_b[1])
        pg.draw.rect(display, (255, 255, 255), end_b)
        util.draw_text('quit', 30, (24, 20, 37), display, end_b.x + 10, end_b[1])

        click = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                util.terminate()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    util.terminate()
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        screen.blit(pg.transform.scale(display, SIZE), (0, 0))
        pg.display.flip()
        clock.tick(FPS)


def win_screen(final_score):
    click = False

    while True:
        display.fill((24, 20, 37))
        m_pos = [i // 4 for i in pg.mouse.get_pos()]

        util.draw_text('u won :D', 14, (255, 255, 255), display, 10, 10)
        util.draw_text(f'final score: {final_score}', 14, (255, 255, 255), display, 150, 10)

        restart_b = pg.Rect(10, 50, 120, 35)
        end_b = pg.Rect(10, 100, 120, 35)

        if restart_b.collidepoint(m_pos):
            if click:
                for sprite in all_sprites:
                    sprite.kill()

                main(0)
        if end_b.collidepoint(m_pos):
            if click:
                util.terminate()

        pg.draw.rect(display, (255, 255, 255), restart_b)
        util.draw_text('restart', 30, (24, 20, 37), display, restart_b.x + 10, restart_b[1])
        pg.draw.rect(display, (255, 255, 255), end_b)
        util.draw_text('quit', 30, (24, 20, 37), display, end_b.x + 10, end_b[1])

        click = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                util.terminate()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    util.terminate()
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        screen.blit(pg.transform.scale(display, SIZE), (0, 0))
        pg.display.flip()
        clock.tick(FPS)


def main(score):
    size = 6
    level = generate_level(size)
    camera = Camera()

    level_x, level_y = load_level(level)
    moving_right = moving_left = False
    air_timer = 0
    enemies = [Slime]

    spawns = []  # player spawns
    for line in enumerate(level[:8]):
        possibles = [i for i in enumerate(line[1]) if i[1] == '@']
        spawns += [(i[0], line[0]) for i in possibles]

    spawn_x, spawn_y = choice(spawns)
    player = Player(spawn_x, spawn_y, 0)

    spawns = []  # enemy spawns
    for line in enumerate(level):
        possibles = [i for i in enumerate(line[1]) if i[1] == 'e']
        spawns += [(i[0], line[0]) for i in possibles]
    
    for _ in sample(spawns, len(spawns) // 2):
        choice(enemies)(*choice(spawns))

    spawns = []  # exit spawns
    for line in enumerate(level[-9:-1]):
        possibles = [i for i in enumerate(line[1]) if i[1] == 'x']
        spawns += [(i[0], line[0] + 8 * (size - 1)) for i in possibles]

    spawn_x, spawn_y = spawns.pop(randint(0, len(spawns) - 1))
    Tile('exit', spawn_x, spawn_y)

    run = True
    while run:
        display.fill((24, 20, 37))

        if not player.dead:
            player_movement = [0, 0]
            if moving_right:
                player_movement[0] += player.speed
            if moving_left:
                player_movement[0] -= player.speed

            player_movement[1] += player.y_momentum
            player.y_momentum += 0.4
            if player.y_momentum > 5:
                player.y_momentum = 5

            if player_movement[0] == 0:
                player.action, player.cur_frame = player.change_action(player.action, player.cur_frame, 'idle')
            if player_movement[0] > 0:
                player.flipped = False
                player.action, player.cur_frame = player.change_action(player.action, player.cur_frame, 'run')
            if player_movement[0] < 0:
                player.flipped = True
                player.action, player.cur_frame = player.change_action(player.action, player.cur_frame, 'run')

            collisions = player.move(player_movement)

            if collisions['bottom']:
                air_timer = 0
                player.y_momentum = 0
            else:
                air_timer += 1

        camera.update(player)
        for sprite in all_sprites:
            camera.apply(sprite)

        for s in all_sprites.sprites():  # drawing in fov
            if -s.rect.width < s.rect.x < S_WIDTH and -s.rect.height < s.rect.y < S_HEIGHT:
                display.blit(s.image, (s.rect.x, s.rect.y))
                
        for s in all_sprites.sprites():  # updating in fov + some more space
            if (-s.rect.width * 2 < s.rect.x < S_WIDTH + s.rect.width * 2 and 
                -s.rect.height * 2 < s.rect.y < S_HEIGHT + s.rect.height * 2):
                s.update()

        player_group.draw(display)
        weapon_group.draw(display)

        util.draw_text(f'score: {player.score}', 8, (255, 255, 255), display, 5, 5)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
                util.terminate()
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
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if not player.attack_timer:
                    player.attack()

        screen.blit(pg.transform.scale(display, SIZE), (0, 0))
        pg.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    start_screen()
