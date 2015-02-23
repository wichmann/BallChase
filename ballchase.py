#! /usr/bin/env python

from __future__ import division, print_function, unicode_literals

import math
import random

from cocos.director import director, glPushMatrix, glPopMatrix
from cocos.layer import Layer, MultiplexLayer
from cocos.scene import Scene
from cocos.scenes.transitions import FlipAngular3DTransition
from cocos.actions import MoveBy, MoveTo, RotateBy, Repeat, Action, FadeIn
from cocos.sprite import Sprite
from cocos.menu import Menu, MultipleMenuItem, MenuItem, ToggleMenuItem
from cocos.menu import CENTER, shake, shake_back
from cocos.text import Label

import pyglet
from pyglet import clock
from pyglet.window import key
from pyglet.event import EventDispatcher
import soundex


APP_NAME = 'BallChase'
NUMBER_OF_ENEMIES = 2
ENEMY_SPEED = 50
PLAYER_SPEED = 200   # speed of players ball in pixel per second

LEVEL_DATA = (
    # number_of_enemies, enemy_speed, time, level
    (2, 50, 20, 1),
    (3, 60, 25, 2),
    #(3, 70, 30, 3),
    #(4, 80, 35, 4),
    #(4, 90, 40, 5),
    #(5, 100, 45, 6),
    #(5, 110, 50, 7),
    #(6, 120, 55, 8)
)


class Chase(Action):
    """Defining an action for a sprite to move constantly towards some other
    object. Second constructor 'init2()' is a workaround because deepcopy can't
    handle a bound method nor a cocosnode.

    Source: cocos source file test/test_action_non_interval.py
    """
    def init(self, fastness):
        self.fastness = fastness

    def init2(self, chasee, on_bullet_hit):
        self.chasee = chasee
        self.on_bullet_hit = on_bullet_hit

    def step(self, dt):
        if self.chasee is None:
            return
        x0, y0 = self.target.position
        x1, y1 = self.chasee.position
        dx , dy = x1-x0, y1-y0
        mod = math.hypot(dx, dy)
        x = self.fastness * dt * (x1-x0) / mod+x0
        y = self.fastness * dt * (y1-y0) / mod+y0
        self.target.position = (x, y)
        if math.hypot(x1-x, y1-y) < 5:
            self._done = True

    def stop(self):
        self.chasee.do(RotateBy(360, 1.0))
        self.on_bullet_hit(self.target)


class GameLayer(Layer, EventDispatcher):
    # layer receives director.window events
    is_event_handler = True

    def __init__(self, number_of_enemies, enemy_speed, time, level):
        super(GameLayer, self ).__init__()

        self.game_over = False
        self.remaining_seconds = time

        # add sprite for ball
        self.player_ball = Sprite('ball.png')
        width, height = director.get_window_size()
        self.player_ball.position = (width//2, height//2)
        self.add(self.player_ball)

        # add labels for level number and time
        level_number = Label('Level {}'.format(level), (20, 10),
                             font_name='Edit Undo Line BRK',
                             font_size=26,
                             anchor_x='left', anchor_y='bottom')
        self.add(level_number)
        self.remaining_time = Label('{} seconds left'.format(self.remaining_seconds),
                                    (width - 20, 10),
                                    font_name='Edit Undo Line BRK', font_size=26,
                                    anchor_x='right', anchor_y='bottom')
        self.add(self.remaining_time)
        # setup timer for remaining game time
        clock.schedule_interval(self.on_timer_second, 1)

        # add bot balls in random spots on screen
        for i in range(number_of_enemies):
            botball = Sprite('ball2.png')
            botball.position = (random.randint(0, width),
                                random.randint(0, height))
            chase_action = botball.do(Chase(enemy_speed))
            chase_action.init2(self.player_ball, self.on_player_lose)
            self.add(botball, z=1)

    def on_enter(self):
        super(GameLayer,self).on_enter()
        soundex.set_music('tetris.mp3')
        soundex.play_music()

    def on_exit(self):
        super(GameLayer,self).on_exit()
        soundex.stop_music()

    def on_timer_second(self, time):
        if self.remaining_seconds:
            self.remaining_seconds -= 1
            print(self.remaining_seconds)
            self.remaining_time.text = '{} seconds left'.format(self.remaining_seconds)
            self.remove(self.remaining_time)
            self.add(self.remaining_time)
        else:
            self.on_player_win()

    def stop_game(self):
        # stop timer for remaining game time
        clock.unschedule(self.on_timer_second)
        # stop all other bot balls
        for node in self.get_children():
            node.stop()

    def on_player_lose(self, e):
        if not self.game_over:
            self.stop_game()
            # show game over screen over game board
            self.game_over = True
            self.overlay_layer = Layer()
            width, height = director.get_window_size()
            gameover_text = Label('Game Over!', (width//2, height//4*3),
                                  font_name='Edit Undo Line BRK',
                                  font_size=46,
                                  anchor_x='center', anchor_y='center')
            self.overlay_layer.add(gameover_text)
            self.parent.add(self.overlay_layer, z=2)
            gameover_text.do(FadeIn(3.0))
            # play lose sound effect
            soundex.play('no.mp3')
            # emit event to inform other game components
            self.dispatch_event('on_level_lost', self)

    def on_player_win(self):
        self.stop_game()
        # TODO show kill screen!
        self.dispatch_event('on_level_won', self)
        
    def on_key_press(self, symbol, modifiers):
        if self.game_over:
            return
        self.key_still_pressed = True
        if symbol == key.LEFT:
            self.check_bounds()
            self.repeat = Repeat(MoveBy((-PLAYER_SPEED//10, 0), 0.1))
            self.player_ball.do(self.repeat)
        elif symbol == key.RIGHT:
            self.check_bounds()
            self.repeat = Repeat(MoveBy((PLAYER_SPEED//10, 0), 0.1))
            self.player_ball.do(self.repeat)
        elif symbol == key.UP:
            self.check_bounds()
            self.repeat = Repeat(MoveBy((0, PLAYER_SPEED//10), 0.1))
            self.player_ball.do(self.repeat)
        elif symbol == key.DOWN:
            self.check_bounds()
            self.repeat = Repeat(MoveBy((0, -PLAYER_SPEED//10), 0.1))
            self.player_ball.do(self.repeat)
        elif symbol == key.ENTER:
            pass

    def check_bounds(self):
        x, y = self.player_ball.position
        width, height = director.get_window_size()
        if x < 0:
            self.player_ball.position = (width, y)
        if x > width:
            self.player_ball.position = (0, y)
        if y < 0:
            self.player_ball.position = (x, height)
        if y > height:
            self.player_ball.position = (x, 0)

    def on_key_release (self, symbol, modifiers):
        self.key_still_pressed = False
        # stop all actions on sprite
        self.player_ball.stop()

    def on_mouse_motion (self, x, y, dx, dy):
        pass

    def on_mouse_drag (self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_press (self, x, y, buttons, modifiers):
        if self.game_over:
            return
        # calculate necessary speed for player ball
        old_x, old_y = self.player_ball.position
        dx = old_x - x
        dy = old_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        # move ball to new position
        move_to_mouse = MoveTo((x, y), distance/PLAYER_SPEED)
        self.player_ball.do(move_to_mouse)

# register events that GameLayer instances can emit
GameLayer.register_event_type('on_level_lost')
GameLayer.register_event_type('on_level_won')


class BackgroundLayer(Layer):
    def __init__(self):
        super(BackgroundLayer, self ).__init__()
        self.img = pyglet.resource.image('background_menu.png')

    def draw(self):
        glPushMatrix()
        self.transform()
        self.img.blit(0,0)
        glPopMatrix()


class OptionsMenu(Menu):
    def __init__(self):
        super( OptionsMenu, self).__init__(APP_NAME)

        # override the font used for the title and the items
        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (6, 172, 255, 255)
        self.font_item['font_name'] = 'Edit Undo Line BRK',
        self.font_item['color'] = (4, 123, 182, 255)
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = 'Edit Undo Line BRK'
        self.font_item_selected['color'] = (1, 51, 76, 255)
        self.font_item_selected['font_size'] = 46

        # set alignment for menus
        self.menu_anchor_y = CENTER
        self.menu_anchor_x = CENTER

        items = []
        self.volumes = ['Mute','10','20','30','40','50','60','70','80','90','100']

        items.append(MultipleMenuItem('SFX volume: ',self.on_sfx_volume,self.volumes,int(soundex.sound_vol * 10)))
        items.append(MultipleMenuItem('Music volume: ',self.on_music_volume,self.volumes,int(soundex.music_player.volume * 10)))
        items.append(ToggleMenuItem('Show FPS:', self.on_show_fps, director.show_FPS))
        items.append(ToggleMenuItem('Fullscreen:', self.on_fullscreen, director.window.fullscreen))
        items.append(MenuItem('Back', self.on_quit))
        self.create_menu(items, shake(), shake_back())

    def on_fullscreen(self, value):
        director.window.set_fullscreen(value)

    def on_quit(self):
        self.parent.switch_to(0)

    def on_show_fps(self, value):
        director.show_FPS = value

    def on_sfx_volume(self, idx):
        vol = idx / 10.0
        soundex.sound_volume(vol)

    def on_music_volume(self, idx):
        vol = idx / 10.0
        soundex.music_volume(vol)


class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__(APP_NAME)

        # set level counter on zero to start with first level
        self.current_level = 0

        # override the font used for the title and the items
        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (6, 172, 255, 255)
        self.font_item['font_name'] = 'Edit Undo Line BRK',
        self.font_item['color'] = (4, 123, 182, 255)
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = 'Edit Undo Line BRK'
        self.font_item_selected['color'] = (1, 51, 76, 255)
        self.font_item_selected['font_size'] = 46

        # example: menus can be vertical aligned and horizontal aligned
        self.menu_anchor_y = CENTER
        self.menu_anchor_x = CENTER

        items = []
        items.append(MenuItem('New Game', self.on_new_game))
        items.append(MenuItem('Options', self.on_options))
        items.append(MenuItem('Quit', self.on_quit))

        self.create_menu(items, shake(), shake_back())

    def on_new_game(self):
        # create a new game layer, insert it in a new scene and replace
        # curretly played scene with it
        next_level_data = LEVEL_DATA[self.current_level]
        new_level = GameLayer(*next_level_data)
        # register this class as listener on events from GameLayer to react
        # when player has lost/won the level
        new_level.push_handlers(self.on_level_lost, self.on_level_won)
        director.replace(FlipAngular3DTransition(Scene(new_level), 1.5))

    def on_options( self ):
        # make MultiplexLayer switch to the options menu
        self.parent.switch_to(1)

    def on_quit(self):
        pyglet.app.exit()

    def on_level_lost(self, emitter):
        print('lost!')

    def on_level_won(self, emitter):
        if self.current_level < len(LEVEL_DATA) - 1:
            self.current_level += 1
            self.on_new_game()
        else:
            print('won!')


if __name__ == "__main__":
    pyglet.resource.path.append('data/')
    pyglet.resource.reindex()
    pyglet.font.add_directory('data/')
    director.init(resizable=True, width=1024, height=768)
    scene = Scene()
    scene.add(MultiplexLayer(MainMenu(), OptionsMenu()),z=1)
    scene.add(BackgroundLayer(), z=0)
    director.run(scene)
