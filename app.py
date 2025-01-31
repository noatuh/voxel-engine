from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os

app = Ursina()

# Load block textures
textures = {
    'grass': 'grass.png',
    'stone': 'white_cube'  # Using a built-in Ursina texture for stone
}

# Player setup
player = FirstPersonController()
Sky()

# Blocks dictionary to store placed blocks
blocks = {}

# Load saved world if available
save_file = "world.json"
if os.path.exists(save_file):
    with open(save_file, 'r') as file:
        blocks = json.load(file)

# Function to create a block
def create_block(position, block_type='grass'):
    block = Button(
        color=color.white,
        model='cube',
        position=position,
        texture=textures[block_type],
        parent=scene,
        origin_y=0.5
    )
    blocks[str(position)] = block_type
    return block

# Generate initial terrain
terrain_size = 10  # Expands as player moves
terrain = []
for x in range(-terrain_size, terrain_size):
    for z in range(-terrain_size, terrain_size):
        pos = (x, 0, z)
        if str(pos) in blocks:
            block_type = blocks[str(pos)]
        else:
            block_type = 'grass'  # Default terrain block
        terrain.append(create_block(pos, block_type))

# Current block type (switch between grass and stone)
current_block = 'grass'
mouse_locked = True  # Mouse starts locked in the game

# Handle player inputs
def input(key):
    global current_block, mouse_locked

    if key == '1':  # Press '1' for grass
        current_block = 'grass'
    elif key == '2':  # Press '2' for stone
        current_block = 'stone'
    
    # Toggle mouse lock on ESC
    if key == 'escape':
        mouse_locked = not mouse_locked
        mouse.locked = mouse_locked
        mouse.visible = not mouse_locked

    # Block placement and removal
    if mouse.hovered_entity:
        block = mouse.hovered_entity
        if key == 'right mouse down':  # Place block
            new_pos = block.position + mouse.normal
            if str(new_pos) not in blocks:
                terrain.append(create_block(new_pos, current_block))
        elif key == 'left mouse down':  # Break block
            if block in terrain:
                terrain.remove(block)
                blocks.pop(str(block.position), None)
                destroy(block)

# Save world on exit
def save_world():
    with open(save_file, 'w') as file:
        json.dump(blocks, file)

app.run()
save_world()
