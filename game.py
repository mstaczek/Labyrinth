import pygame
import time
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SQUARE_SIZE = 80
GRID_WIDTH = SCREEN_WIDTH // SQUARE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // SQUARE_SIZE
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
TRANSPARENT = (0, 0, 0, 0)


import os
import zipfile
import xml.etree.ElementTree as ET

def extract_ora_file(path):
    # extract zip to adjacent folder
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(os.path.join(os.path.dirname(path),'extracted'))

# load xml
def load_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root

# get all layer namer and paths from xml
def get_layer_names_and_paths(xml, path):
    layers = []
    for layer in xml.iter('layer'):
        img_path = os.path.join(path,layer.attrib['src']).replace('/','\\')
        layers.append((layer.attrib['name'], img_path))
    
    return layers

def get_tile_paths(root, ora_name):
    ora_path = os.path.join(root, ora_name)
    extract_ora_file(ora_path)

    xml_path = os.path.join(root,'extracted','stack.xml')
    xml = load_xml(xml_path)

    layers = get_layer_names_and_paths(xml, os.path.dirname(xml_path))
    return layers


root = 'textures'
ora_name = 'tiles.ora'
texture_paths = get_tile_paths(root, ora_name)

images = {
    k: pygame.image.load(v) for k, v in texture_paths
    if all([letter.lower() in ['u', 'r', 'd', 'l'] for letter in k.lower()]) 
        or k == 'NoTilePossible'
        or k.startswith('encounter')
}

ordered_rotated_keys = {'u': 1, 'U': 2, 'r': 3, 'R': 4, 'd': 5, 'D': 6, 'l': 7, 'L': 8}

def make_all_rotations_of_tile(code):
    order_small = ['u', 'r', 'd', 'l']
    order_large = ['U', 'R', 'D', 'L']
    
    letters_in_key = [letter for letter in code]
    rotated_90 = ''
    rotated_180 = ''
    rotated_270 = ''
    for letter in letters_in_key:
        if letter in order_small:
            rotated_90 += order_small[(order_small.index(letter) + 1) % 4]
            rotated_180 += order_small[(order_small.index(letter) + 2) % 4]
            rotated_270 += order_small[(order_small.index(letter) + 3) % 4]
        elif letter in order_large:
            rotated_90 += order_large[(order_large.index(letter) + 1) % 4]
            rotated_180 += order_large[(order_large.index(letter) + 2) % 4]
            rotated_270 += order_large[(order_large.index(letter) + 3) % 4]
    rotated_90 = ''.join(sorted(rotated_90, key=lambda x: ordered_rotated_keys[x]))
    rotated_180 = ''.join(sorted(rotated_180, key=lambda x: ordered_rotated_keys[x]))
    rotated_270 = ''.join(sorted(rotated_270, key=lambda x: ordered_rotated_keys[x]))
    return code, rotated_90, rotated_180, rotated_270

def add_rotated_images(images):
    additional_images = {}
    for k, v in images.items():
        if len(k) > 4:
            continue
        k, rotated_90, rotated_180, rotated_270 = make_all_rotations_of_tile(k)
        additional_images[rotated_90] = pygame.transform.rotate(v, 270)
        additional_images[rotated_180] = pygame.transform.rotate(v, 180)
        additional_images[rotated_270] = pygame.transform.rotate(v, 90)
    return images | additional_images

images = add_rotated_images(images)
print(images.keys())

frequencies_normalized = {
    'UrD' : 16,
    'UrDl' : 14,
    'UD' : 20,
    'UR' : 20,
    'URd' : 14,
    'URl' : 14,
    'URdl' : 22,
    'URDl' : 4,
    'URDL' : 4,
    'URD' : 4,
    'U' : 4,
    'u' : 30,
    'ud' : 9,
    'ur' : 11,
    'urd' : 20,
    'urdl' : 10
}

encounter_frequencies_normalized = {
    'encounter_stairs' : 10,
    'encounter_mirror' : 10,
    'encounter_fountain' : 5,
    'encounter_statue' : 5,
    'encounter_trap_door' : 5,
    'encounter_furniture' : 5,
    'encounter_altar' : 5,
    'encounter_artwork' : 5,
    'no_encounter' : 30
}
    

# Randomly choose new tile
def randomly_choose_new_tile():
    tile_names = []
    tile_frequencies = []
    for k, v in frequencies_normalized.items():
        tile_names.append(k)
        tile_frequencies.append(v)
    new_tile_generalized = random.choices(tile_names, weights=tile_frequencies)[0]
    new_tile_name = random.choice(make_all_rotations_of_tile(new_tile_generalized))
    return new_tile_name

# Randomly choose new encounter tile
def randomly_choose_new_encounter():
    encounter_names = []
    encounter_frequencies = []
    for k, v in encounter_frequencies_normalized.items():
        encounter_names.append(k)
        encounter_frequencies.append(v)
    new_encounter_name = random.choices(encounter_names, weights=encounter_frequencies)[0]
    if new_encounter_name == 'no_encounter':
        return None
    return new_encounter_name

# Set the initial visibility and timer variables
visible = True
timer = time.time()

# Initialize Pygame
pygame.init()

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Labyrinth")

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        
        # make it a transparent square with red boundary
        self.image.fill(TRANSPARENT)
        pygame.draw.rect(self.image, RED, [0, 0, SQUARE_SIZE, SQUARE_SIZE], 3)
        self.image.set_colorkey(TRANSPARENT)
        
        self.rect = self.image.get_rect()
        self.rect.x = x * SQUARE_SIZE
        self.rect.y = y * SQUARE_SIZE
        

    def update(self, move_up, move_down, move_left, move_right):
        if move_up and self.rect.y > 0:
            self.rect.y -= SQUARE_SIZE
            move_up = False
        if move_left and self.rect.x > 0:
            self.rect.x -= SQUARE_SIZE
            move_left = False
        if move_down and self.rect.y < SCREEN_HEIGHT - SQUARE_SIZE:
            self.rect.y += SQUARE_SIZE
            move_down = False
        if move_right and self.rect.x < SCREEN_WIDTH - SQUARE_SIZE:
            self.rect.x += SQUARE_SIZE
            move_right = False

# Create player object
player = Player(GRID_WIDTH // 2, GRID_HEIGHT // 2)

# Create sprite groups for player
player_group = pygame.sprite.Group()
player_group.add(player)

# Convert names to filename
def convert_names_to_filename(exits):
    image_name = ''
    for exit_name, exit_code in {
        'up': 'u',
        'Up': 'U',
        'right': 'r',
        'Right': 'R',
        'down': 'd',
        'Down': 'D',
        'left': 'l',
        'Left': 'L'
    }.items():
        if exit_name in exits:
            image_name += exit_code

    if image_name not in images.keys():
        return None
    
    return image_name

def convert_filename_to_names(image_name):
    exits = []
    for exit_name, exit_code in {
        'up': 'u',
        'Up': 'U',
        'right': 'r',
        'Right': 'R',
        'down': 'd',
        'Down': 'D',
        'left': 'l',
        'Left': 'L'
    }.items():
        if exit_code in image_name:
            exits.append(exit_name)
    return exits

# Normalize code name
def normalize_name(exits_code):
    normalized = ''
    for letter in ['u', 'U', 'r', 'R', 'd', 'D', 'l', 'L']:
        if letter in exits_code:
            normalized += letter
    return normalized

# Rectangle class
class GraySquare(pygame.sprite.Sprite):
    def __init__(self, width, position, exits = ['Up', 'Down', 'Left', 'Right']):
        super().__init__()

        # Create the rectangle sprite
        image_name = convert_names_to_filename(exits)
        self.image = images[image_name]
        self.image = pygame.transform.scale(self.image, (width, width))

        # Set the position of the sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        # Exits from this tile
        self.exits = exits

# Rectangle class
class EncounterTile(pygame.sprite.Sprite):
    def __init__(self, width, position, exits, encounter):
        super().__init__()

        # Create the rectangle sprite
        image_name = convert_names_to_filename(exits)
        underlaying_image = images[image_name]
        overlaying_transparent_image = images[encounter]
        overlaying_transparent_image.set_alpha(128)
        self.image = underlaying_image.copy()
        self.image.blit(overlaying_transparent_image, (0, 0))
        self.image = pygame.transform.scale(self.image, (width, width))

        # Set the position of the sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        # Exits from this tile
        self.exits = exits
        # Encounter on this tile
        self.encounter = encounter


# Rectangle class
class NoTilePossible(pygame.sprite.Sprite):
    def __init__(self, width, position):
        super().__init__()

        # Create the rectangle sprite
        self.image = images['NoTilePossible']
        self.image = pygame.transform.scale(self.image, (width, width))

        # Set the position of the sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        # Exits from this tile
        self.exits = []


# List to track visited squares
visited_squares = []
visited_squares.append((player.rect.x, player.rect.y))

# Create sprite groups for visited and unvisited squares
visited_squares_group = pygame.sprite.Group()
visited_squares_group.add(GraySquare(SQUARE_SIZE, (player.rect.x, player.rect.y)))

move_up, move_down, move_left, move_right = False, False, False, False

# Calculate future player position
def get_future_player_pos(player_pos, movement):
    future_player_pos = player_pos

    if movement[0] and player_pos[1] > 0:
        future_player_pos = (player_pos[0], player_pos[1] - SQUARE_SIZE)
    elif movement[1] and player_pos[1] < SCREEN_HEIGHT - SQUARE_SIZE:
        future_player_pos = (player_pos[0], player_pos[1] + SQUARE_SIZE)
    elif movement[2] and player_pos[0] > 0:
        future_player_pos = (player_pos[0] - SQUARE_SIZE, player_pos[1])
    elif movement[3] and player_pos[0] < SCREEN_WIDTH - SQUARE_SIZE:
        future_player_pos = (player_pos[0] + SQUARE_SIZE, player_pos[1])

    return future_player_pos

def _get_adjacent_tiles(player_pos):
    adjacent_tiles = {}
    for tile in visited_squares_group:
        if tile.rect.topleft == (player_pos[0], player_pos[1] - SQUARE_SIZE):
            adjacent_tiles['up'] = tile
        elif tile.rect.topleft == (player_pos[0], player_pos[1] + SQUARE_SIZE):
            adjacent_tiles['down'] = tile
        elif tile.rect.topleft == (player_pos[0] - SQUARE_SIZE, player_pos[1]):
            adjacent_tiles['left'] = tile
        elif tile.rect.topleft == (player_pos[0] + SQUARE_SIZE, player_pos[1]):
            adjacent_tiles['right'] = tile
    return adjacent_tiles

# Choose new tile
def choose_new_tile(player_pos):
    # Find adjacent tiles from visited_squares_group
    adjacent_tiles = _get_adjacent_tiles(player_pos)

    # Check exits coming to the current tile
    necessary_exits = []
    impossible_exits = []

    if 'up' in adjacent_tiles:
        if 'down' in adjacent_tiles['up'].exits:
            necessary_exits.append('up')
        elif 'Down' in adjacent_tiles['up'].exits:
            necessary_exits.append('Up')
        else:
            impossible_exits.append('up')
            impossible_exits.append('Up')
    if 'down' in adjacent_tiles:
        if 'up' in adjacent_tiles['down'].exits:
            necessary_exits.append('down')
        elif 'Up' in adjacent_tiles['down'].exits:
            necessary_exits.append('Down')
        else:
            impossible_exits.append('down')
            impossible_exits.append('Down')
    if 'left' in adjacent_tiles:
        if 'right' in adjacent_tiles['left'].exits:
            necessary_exits.append('left')
        elif 'Right' in adjacent_tiles['left'].exits:
            necessary_exits.append('Left')
        else:
            impossible_exits.append('left')
            impossible_exits.append('Left')
    if 'right' in adjacent_tiles:
        if 'left' in adjacent_tiles['right'].exits:
            necessary_exits.append('right')
        elif 'Left' in adjacent_tiles['right'].exits:
            necessary_exits.append('Right')
        else:
            impossible_exits.append('right')
            impossible_exits.append('Right')


    # Use unequal probabilies
    new_tile_name = randomly_choose_new_tile()
    new_tile_exits = convert_filename_to_names(new_tile_name)
    for neccessary_exit in necessary_exits:
        if neccessary_exit not in new_tile_exits:
            return None
    for impossible_exit in impossible_exits:
        if impossible_exit in new_tile_exits:
            return None
    if all([letter in ['u', 'r', 'd', 'l'] for letter in new_tile_name]) \
        and (encounter_name := randomly_choose_new_encounter()) is not None:
        return EncounterTile(SQUARE_SIZE, player_pos, new_tile_exits, encounter_name)
    else:
        return GraySquare(SQUARE_SIZE, player_pos, new_tile_exits)

        

impossible_positions = []

# Check if movement is possible
def check_movement_possible(player_pos, movement):
    # Find current tile
    current_tile = None
    for tile in visited_squares_group:
        if tile.rect.topleft == player_pos:
            current_tile = tile
            break
    
    # Check if movement is possible
    move_up, move_down, move_left, move_right = movement
    if move_up and 'up' not in current_tile.exits and 'Up' not in current_tile.exits:
        return False
    elif move_down and 'down' not in current_tile.exits and 'Down' not in current_tile.exits:
        return False
    elif move_left and 'left' not in current_tile.exits and 'Left' not in current_tile.exits:
        return False
    elif move_right and 'right' not in current_tile.exits and 'Right' not in current_tile.exits:
        return False
    elif get_future_player_pos(player_pos, movement) in impossible_positions:
        return False
    else:
        return True

# Game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                move_up = True
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                move_left = True
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                move_down = True
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                move_right = True

            # Update visited squares
            player_pos = (player.rect.x, player.rect.y)
            movement = (move_up, move_down, move_left, move_right)
            is_movement_allowed = check_movement_possible(player_pos, movement)

            if is_movement_allowed:
                future_player_pos = get_future_player_pos(player_pos, movement)
                if future_player_pos in visited_squares:
                    # Player movement
                    player.update(move_up, move_down, move_left, move_right)
                else:
                    counter = 0
                    no_tile_possible_flag = False
                    while (new_tile := choose_new_tile(future_player_pos)) is None:
                        counter += 1
                        if counter > 100:
                            no_tile_possible_flag = True
                            break
                        pass
                    # adding new tile
                    if no_tile_possible_flag:
                        new_tile = NoTilePossible(SQUARE_SIZE, future_player_pos)
                        impossible_positions.append(future_player_pos)
                        visited_squares_group.add(new_tile)
                    else:
                        # Player movement
                        player.update(move_up, move_down, move_left, move_right)
                        player_pos = (player.rect.x, player.rect.y)
                        visited_squares.append(player_pos)
                        visited_squares_group.add(new_tile)
            move_up, move_down, move_left, move_right = False, False, False, False




    # Flashing boundary
    if visible and time.time() - timer >= 0.5:
        visible = not visible
        timer = time.time()
    if not visible and time.time() - timer >= 0.25:
        visible = not visible
        timer = time.time()

    # Clear the screen
    screen.fill(BLACK)

    # Draw visited squares
    visited_squares_group.draw(screen)
    
    # Draw player
    if visible:
        player_group.draw(screen)
    
    # Update the screen
    pygame.display.flip()

    clock = pygame.time.Clock()
    clock.tick(60)

# Quit the game
pygame.quit()
