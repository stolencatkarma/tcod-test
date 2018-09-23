import time
import tcod
import sys
import random
import tcod.map
import os
import json
from collections import defaultdict
import math

class Tile:
    # a tile of the map and its properties
    def __init__(self, impassable, x, y, char, color, block_sight=None):
        self.impassable = impassable
        self.x = x
        self.y = y
        self.char = char
        self.color = color
 
        # by default, if a tile is impassable, it also blocks sight
        if(block_sight is None):
            block_sight = impassable
        else:
            self.block_sight = block_sight

class Object:
    # this is a generic object: the player, a monster, stairs, etc.
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.stats = None # base objects have no stats. 
 
    def move(self, x, y):
        # move to the given position
        self.x = self.x + x
        self.y = self.y + y
 
    def draw(self, console):
        # set the color and then draw the character that represents this object at its position
        tcod.console_set_default_foreground(console, self.color)
        tcod.console_put_char(console, self.x, self.y, self.char, tcod.BKGND_NONE)
 
    def clear(self, console):
        # erase the character that represents this object
        tcod.console_put_char(console, self.x, self.y, ' ', tcod.BKGND_NONE)

class Door(Object):
    def __init__(self, x, y, char, color):
        super().__init__(x, y, char, color)
        self.impassable = True
        self.block_sight = True

    def on_examined(self, x, y, objects):
        if(self.impassable):
            self.impassable = None
            self.block_sight = None
        else:
            self.impassable = True
            self.block_sight = True

class Player(Object):
    def __init__(self, x, y, char, color, name):
        super().__init__(x, y, char, color)
        self.name = name
        self.stats = dict()
        self.hp = 10
    
    def examine(self, x, y, objects):
        global current_level
        # look for an object with an on_examined() at the x,y
        for obj in objects:
            if obj.x == x and obj.y == y:
                _result = obj.on_examined(x,y,objects)
                if(_result == 'up'):
                    current_level = current_level - 1
                elif(_result == 'down'):
                    current_level = current_level + 1
                else:
                    pass

class Monster(Object):
    def __init__(self, x, y, char, color, reference):
        super().__init__(x, y, char, color)
        #self.ident = ident # pull monster stats from a dict from ident
        self.ident = reference['ident']
        self.color = my_colors[reference['color']]
        self.hp = reference['hp']
    
    def do_action(self):
        pass

class Stairs(Object):
    def __init__(self, x, y, char, color):
        # char decides direction. < is down. > is up. player just needs to activate stairs. not choose direction.
        super().__init__(x, y, char, color)
    
    def on_examined(self, x, y, objects):
       # move the player down or up a level depending on the stairs.
        if(self.char == tcod.CHAR_ARROW2_N):
           # up stairs
           return 'up'
        else:
            # down stairs
            return 'down'
        
class MonsterManager:
    def __init__(self, root_console):
        self.MONSTER_TYPES = defaultdict(dict)
        for root, dirs, files in os.walk('./data/json/monsters/'):
            for file_data in files:
                if file_data.endswith('.json'):
                    with open(root+'/'+file_data, encoding='utf-8') as data_file:
                        data = json.load(data_file)
                    for item in data:
                        try:
                            for key, value in item.items():
                                if(isinstance(value, list)):
                                    self.MONSTER_TYPES[item['ident']][key] = []
                                    for add_value in value:
                                        self.MONSTER_TYPES[item['ident']][key].append(str(add_value))
                                else:
                                    self.MONSTER_TYPES[item['ident']][key] = str(value)
                        except Exception:
                            root_console.print_(0, 0, '!! couldn\'t parse: ' + str(item) + ' -- likely missing ident.')
                            sys.exit()
        root_console.print_(0, 0, 'total MONSTER_TYPES loaded: ' + str(len(self.MONSTER_TYPES)))

# Setup the font.
tcod.console_set_custom_font('dejavu16x16_gs_tc.png', tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
WIDTH = 60
HEIGHT = 40
MAP_WIDTH = WIDTH # map size is screen width
MAP_HEIGHT = HEIGHT - 2 # leave us two at the bottom for messages.

key = tcod.Key()

my_colors = dict()
my_colors['black'] = tcod.color.Color(0,0,0)
my_colors['white'] = tcod.color.Color(255,255,255)

def make_map(difficulty): # how deep or difficult should the level be we generate.
    new_map = dict()
    rooms = list()
    creatures = list()
    objects = list()
    for y in range(MAP_HEIGHT):
        new_map[y] = dict()
        for x in range(MAP_WIDTH):
            new_map[y][x] = Tile(False, x, y, tcod.CHAR_BLOCK1, tcod.color.Color(25, 25, 25)) # initalize our map.
    
    _check_map = dict()
    for y in range(MAP_HEIGHT):
        _check_map[y] = dict()
        for x in range(MAP_WIDTH):
            _check_map[y][x] = False # when we place a room we don't want any overlap so we'll check this to see if we've drawn there before.

    '''
    _x = random.randint(0,MAP_WIDTH-1)
    _y = random.randint(0,MAP_HEIGHT-1)
    _creatures.append(Monster(_x, _y, MM.MONSTER_TYPES['zombie']['char'],MM.MONSTER_TYPES['zombie']['color'], MM.MONSTER_TYPES['zombie']))
    '''
    
    # next_room = random.choice(['blank', 'combat', 'treasure', 'puzzle'])
    next_room = 'blank'

    if(len(rooms) == 0): # this is the first room on this level. put up stairs here.
        # put UP Stairs where the player went down from.
        objects.append(Stairs(player.x, player.y, tcod.CHAR_ARROW2_N, tcod.color.Color(25, 125, 125)))
        # draw a simple room around the player.
        for y in range(player.y - 1, player.y + 2):
            for x in range(player.x - 1, player.x + 2):
                new_map[y][x].char = ' '
                _check_map[y][x] = True # tell the generator this tile isn't usable anymore.
    
    cursor_y = player.y # use this is a basepoint to draw the next rooms.
    cursor_x = player.x
        
    should_continue = True
    while should_continue:
        if(next_room == 'blank'):
            # need to make a decent sized room then loop and make another room until we run out of room for rooms. =)
            next_room_width = random.randint(3,7)
            next_room_height = random.randint(3,7)
            room_distance = random.randint(6,8)
            # find a spot for the next room and then connect the two rooms with a hallway.
            
            if(cursor_y <= 1):
                cursor_y = 2
            if(cursor_y >= MAP_HEIGHT):
                cursor_y = MAP_HEIGHT-2
            
            if(cursor_x <= 1):
                cursor_x = 2
            if(cursor_x >= MAP_WIDTH):
                cursor_x = MAP_WIDTH-2
                       

            can_build_up = True
            for j in range(cursor_y - room_distance, cursor_y - room_distance + next_room_height):
                for i in range(cursor_x, cursor_x + next_room_width):
                    try:
                        if(_check_map[j][i]):
                            can_build_up = False
                    except KeyError:
                        can_build_up = False
            if(can_build_up):
                for j in range(cursor_y - room_distance, cursor_y - room_distance + next_room_height):
                    for i in range(cursor_x, cursor_x + next_room_width):
                        new_map[j][i].char = ' '
                        _check_map[j][i] = True
                for k in range(room_distance):
                    new_map[cursor_y - k][cursor_x].char = ' '
                    if(k is room_distance // 2):
                        objects.append(Door(cursor_x, cursor_y-k, 'U', tcod.blue))
                    _check_map[cursor_y - k][cursor_x] = True
               
                continue
            
            can_build_left = True
            for j in range(cursor_y, cursor_y + next_room_height):
                for i in range(cursor_x - room_distance, cursor_x - room_distance + next_room_width):
                    try:
                        if(_check_map[j][i]):
                            can_build_left = False
                    except KeyError:
                        can_build_left = False
            if(can_build_left):
                for j in range(cursor_y, cursor_y + next_room_height):
                    for i in range(cursor_x - room_distance, cursor_x - room_distance + next_room_width):
                        new_map[j][i].char = ' '
                        _check_map[j][i] = True
                for k in range(room_distance):
                    new_map[cursor_y][cursor_x-k].char = ' '
                    _check_map[cursor_y][cursor_x-k] = True
                
                continue

            can_build_down = True
            for j in range(cursor_y + room_distance, cursor_y + room_distance + next_room_height):
                for i in range(cursor_x, cursor_x + next_room_width):
                    try:
                        if(_check_map[j][i]):
                            can_build_down = False
                    except KeyError:
                        can_build_down = False
            if(can_build_down):
                for j in range(cursor_y+room_distance, cursor_y + room_distance + next_room_height):
                    for i in range(cursor_x, cursor_x + next_room_width):
                        new_map[j][i].char = ' '
                        _check_map[j][i] = True
                for k in range(room_distance):
                    new_map[cursor_y + k][cursor_x].char = ' '
                    _check_map[cursor_y + k][cursor_x] = True
                
                continue
            
            can_build_right = True
            for j in range(cursor_y, cursor_y + next_room_height):
                for i in range(cursor_x + room_distance, cursor_x + room_distance + next_room_width):
                    try:
                        if(_check_map[j][i]):
                            can_build_right = False
                    except KeyError:
                        can_build_right = False
            if(can_build_right):
                for j in range(cursor_y, cursor_y + next_room_height):
                    for i in range(cursor_x + room_distance, cursor_x + room_distance + next_room_width):
                        new_map[j][i].char = ' '
                        _check_map[j][i] = True
                for k in range(room_distance):
                    new_map[cursor_y][cursor_x+k].char = ' '
                    _check_map[cursor_y][cursor_x+k] = True
                
                continue
            
            


            # if we made it here without finding a place to build

            objects.append(Stairs(cursor_x, cursor_y, tcod.CHAR_ARROW2_S, tcod.color.Color(125, 125, 25)))
            should_continue = False
                

            '''
            can_build_down = True
            for j in range(next_room_height):
                for i in range(next_room_width):
                    if(_check_map[j + cursor_y - room_distance][i + cursor_x]):
                        can_build_down = False
            '''




    # loop - create a room (different types, some are hazard, puzzle, treasure)
    #    add monsters if combat room, treasure if treasure room, etc.
    
    # create hallway and loop.
    # create up and down stairs.
    # generate a possible chest.
    
    return new_map, creatures, objects

def create_town():
    new_map = dict()
    creatures = list()
    objects = list()
    # this is dungeon level zero. where the shops and inn are.
    for y in range(MAP_HEIGHT):
        new_map[y] = dict()
        for x in range(MAP_WIDTH):
            new_map[y][x] = Tile(False, x, y, tcod.CHAR_BLOCK1, tcod.color.Color(25, 25, 25)) # initalize our map.

    # needs minimum stairs down.
    objects.append(Stairs(player.x+2, player.y, tcod.CHAR_ARROW2_S, tcod.color.Color(25, 25, 25)))
    # TODO: shops? magic store?

    return new_map, creatures, objects

class dungeon_level(): # each dungeon level should have it's own references to the creatures and items on it, a map
    def __init__(self, difficulty):
        self.creatures = list()
        self.objects = list() # anything that's not a player or a Monster.
        if(difficulty == 0): # generate a town. always start in town.
             self.map, self.creatures, self.objects = create_town()
        else:
            self.map, self.creatures, self.objects = make_map(difficulty)




player = Player(WIDTH // 3, HEIGHT // 2, '@', tcod.white, 'The Hero')
full_dungeon_stack = dict() # i want to save all previously generated levels so the player can go back to them. dict so we can have the freedom to make level 8 before 5,6,7 if we need to.
full_dungeon_stack[0] = dungeon_level(0) # full_dungeon_stack[0].map would be town.
full_dungeon_stack[0].creatures.append(player)
current_level = 0 # level zero is a special starting area.



# Initialize the root console in a context.
with tcod.console_init_root(WIDTH, HEIGHT, 'tcod-test', False) as root_console:
    MM = MonsterManager(root_console)
    tcod.sys_set_fps(24)
    state = 'main' # set back to a main menu when we get there.
    
    while not tcod.console_is_window_closed():
        tcod.console_clear(root_console) # clear screen between frames.

        # if state is 'start' blit the opening screen asking the player to start a new game.
        if(state == 'start'):
            tcod.console_flush()
            ev = tcod.sys_wait_for_event(tcod.EVENT_ANY, key, None, True)
            if ev & tcod.EVENT_KEY:
                state = 'main'
        
        # if state is 'main' blit the map and the player on the screen as well as the noise level.
        elif(state == 'main'):
            # figure out what level we are on and use that data to display.
            try:
                _level = full_dungeon_stack[current_level]
            except KeyError:
                full_dungeon_stack[current_level] = dungeon_level(current_level)
                _level = full_dungeon_stack[current_level]
            _map = _level.map
            _creatures = _level.creatures
            _objects = _level.objects

            player.clear(root_console)
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    tcod.console_put_char(root_console, x, y, _map[y][x].char)
            
            for obj in _objects:
                obj.clear(root_console)
                obj.draw(root_console)

            for creature in _creatures:
                # don't do this for the player, they have a special way to act.
                if(isinstance(creature, Monster)):
                    creature.clear(root_console)
                    creature.do_action() # have creatures do thier move or attack here.
                    creature.draw(root_console) # finally redraw
            
            player.draw(root_console)
            # TODO: blit weather or fog effects.
            tcod.console_flush()
            # wait for input - parse input and do the following.
            # if key is up, down, left, right - move player or attack
            # if key is 
            # if key is (w)ait - pass one turn by.
            # if key F1 open help screen

            ev = tcod.sys_wait_for_event(tcod.EVENT_KEY_RELEASE, key, None, True)
            if ev:
                # root_console.print_(0, 0, repr(key))
                '''_x = random.randint(0,MAP_WIDTH-1)
                _y = random.randint(0,MAP_HEIGHT-1)
                _creatures.append(Monster(_x, _y, MM.MONSTER_TYPES['zombie']['char'],MM.MONSTER_TYPES['zombie']['color'], MM.MONSTER_TYPES['zombie']))'''
                if key.vk == tcod.KEY_CHAR:
                    #TODO handle player attacks
                    if key.c == ord('w'):
                        player.move(0, -1)
                    elif key.c == ord('s'):
                        player.move(0, 1)
                    elif key.c == ord('a'):
                        player.move(-1, 0)
                    elif key.c == ord('d'):
                        player.move(1, 0)
                    elif key.c == ord('e'): # (e)xamine or use
                        root_console.print_(MAP_HEIGHT//2, MAP_WIDTH//2, 'Examine what? valid keys. e, w, s, a, d')
                        tcod.console_flush() # flush to draw the examine box.
                        ev = tcod.sys_wait_for_event(tcod.EVENT_KEY_RELEASE, key, None, True)
                        if ev:
                            if key.c == ord('e'): # (e)xamine here.
                                player.examine(player.x, player.y, _objects)
                            elif key.c == ord('w'):
                                player.examine(player.x, player.y-1, _objects)
                            elif key.c == ord('s'):
                                player.examine(player.x, player.y+1, _objects)
                            elif key.c == ord('a'):
                                player.examine(player.x-1, player.y, _objects)
                            elif key.c == ord('d'):
                                player.examine(player.x+1, player.y, _objects)

                        
                    elif key.c == ord('1'):
                        # use attack skill 1
                        pass
                    elif key.c == ord('2'):
                        # use attack skill 2
                        pass
                    elif key.c == ord('3'):
                        # use chosen skill 1
                        pass
                    elif key.c == ord('4'):
                        # use chosen skill 2
                        pass

            
                   

        
        # if state is 'help' show help screen.
        elif(state == 'help'):
            # blit all the commands in a help window.
            # close on any key.
            ev = tcod.sys_wait_for_event(tcod.EVENT_ANY, key, None, True)
            if ev & tcod.EVENT_KEY:
                state = 'main'

        # if state is 'score' screen show the score at the end of the game.
        elif(state == 'score'):
            pass
        
        tcod.console_flush()
    
# The window is closed here, after the above context exits.