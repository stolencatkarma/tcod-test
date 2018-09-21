import time
import tcod
import sys
import random
import tcod.map

# Setup the font.
tcod.console_set_custom_font('dejavu16x16_gs_tc.png', tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
WIDTH = 40
HEIGHT = 40
key = tcod.Key()

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
 
    def move(self, x, y):
        # move to the given position
        self.x = x
        self.y = y
 
    def draw(self, console):
        # set the color and then draw the character that represents this object at its position
        tcod.console_set_default_foreground(console, self.color)
        tcod.console_put_char(console, self.x, self.y, self.char, tcod.BKGND_NONE)
 
    def clear(self, console):
        # erase the character that represents this object
        tcod.console_put_char(console, self.x, self.y, ' ', tcod.BKGND_NONE)

class Player(Object):
    def __init__(self, x, y, char, color, name):
        super().__init__(x, y, char, color)
        self.name = name

class Monster(Object):
    def __init__(self, x, y, char, color, ident):
        super().__init__(x, y, char, color)
        self.ident = ident # pull monster stats from a dict from ident

class Stairs(Object):
    def __init__(self, x, y, char, color):
        # char decides direction. < is down. > is up. player just needs to activate stairs. not choose direction.
        super().__init__(x, y, char, color)
        
        def draw(self, console):
            # set the color and then draw the character that represents this object at its position
            tcod.console_set_default_foreground(console, self.color)
            tcod.console_put_char(console, self.x, self.y, self.char, tcod.BKGND_NONE)
 
        def clear(self, console):
            # erase the character that represents this object
            tcod.console_put_char(console, self.x, self.y, ' ', tcod.BKGND_NONE)



MAP_WIDTH = WIDTH # map size is screen width
MAP_HEIGHT = HEIGHT - 2 # leave us two at the bottom for messages.

def make_map(difficulty): # how deep or difficult should the level be we generate.
        
    new_map = tcod.map.Map(width=MAP_WIDTH, height=MAP_HEIGHT)
    
       
    # loop - create a room (different types, some are hazard, puzzle, treasure)
    #    add monsters if combat room, treasure if treasure room, etc.
    
    # create hallway and loop.
    # create up and down stairs.
    # generate a possible chest.


    
    return new_map

def create_town():
    new_map = dict()
    # this is dungeon level zero. where the shops and inn are.
    for y in range(MAP_HEIGHT):
        new_map[y] = dict()
        for x in range(MAP_WIDTH):
            new_map[y][x] = Tile(False, x, y, tcod.CHAR_BLOCK1, tcod.color.Color(25, 25, 25)) # initalize our map.

    # needs minimum stairs down.
    # TODO: shops? magic store?

    return new_map

class dungeon_level(): # each dungeon level should have it's own references to the creatures and items on it, a map
    def __init__(self, difficulty):
        self.creatures = list()
        self.objects = list()
        if(difficulty == 0): # generate a town. always start in town.
            self.map = create_town()
        else:
            self.map = make_map(difficulty)

player = Player(WIDTH // 2, HEIGHT // 2, '@', tcod.white, 'The Hero')
current_level = 0 # level zero is a special starting area.
full_dungeon_stack = dict() # i want to save all previously generated levels so the player can go back to them. dict so we can have the freedom to make level 8 before 5,6,7 if we need to.
full_dungeon_stack[0] = dungeon_level(0) # full_dungeon_stack[0].map would be the town.

# Initialize the root console in a context.
with tcod.console_init_root(WIDTH, HEIGHT, 'tcod-test', False) as root_console:
    
    tcod.sys_set_fps(144)
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
            _level = full_dungeon_stack[current_level]
            _map = _level.map
            _creatures = _level.creatures
            _objects = _level.objects
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    tcod.console_put_char(root_console, x, y, _map[y][x].char, tcod.BKGND_NONE)



            # blit the map - around the player

                    
            # blit items and chests and stairs.
            # blit the player and creatures (creatures cover items)
            # blit weather or fog effects.
            
            # wait for input - parse input and do the following.
            # if key is up, down, left, right - move player or attack
            # if key is 
            # if key is (w)ait - pass one turn by.
            # if key F1 open help screen

            ev = tcod.sys_wait_for_event(tcod.EVENT_KEY_RELEASE, key, None, True)
            if ev :
                root_console.print_(0, 0, repr(key))
            
            

        
        # if the player is grabbing items from a container.
        elif(state == 'grab_items'):
            # blit player's inventory space left and grabbable items
            # assign a letter to all grabable items
            # wait for input - if a letter assigned to an item grab the item.
            pass

        # if state is 'inventory' show items of value full screen.
        elif(state == 'inventory'):
            # assign letters to each item.
            # if key pressed then drop the item destroying it.
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