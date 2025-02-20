# client.py
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os
import socket
import threading

app = Ursina()

# ------------------------------------
# Game Setup and World Creation
# ------------------------------------
textures = {
    'grass': 'grass.png',      # Ensure this image is available in your assets.
    'stone': 'white_cube'      # Using a built-in Ursina texture.
}

player = FirstPersonController()
Sky()

# Dictionaries/lists to track blocks.
blocks = {}
terrain = []

# (Optional) Load saved world locally.
save_file = "world.json"
if os.path.exists(save_file):
    with open(save_file, 'r') as file:
        blocks = json.load(file)

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

# Generate a flat initial terrain.
terrain_size = 10
for x in range(-terrain_size, terrain_size):
    for z in range(-terrain_size, terrain_size):
        pos = (x, 0, z)
        block_type = blocks.get(str(pos), 'grass')
        terrain.append(create_block(pos, block_type))

current_block = 'grass'
mouse_locked = True
mouse.locked = mouse_locked
mouse.visible = not mouse_locked

# ------------------------------------
# Networking Setup
# ------------------------------------
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Replace 'server_ip_address' with the actual IP of your server.
server_ip = '127.0.0.1'
client_socket.connect((server_ip, 6000))

# Set up a unique identifier for the local client and a dictionary for remote players.
local_client_id = str(client_socket.getsockname())
other_players = {}  # Maps client IDs to their corresponding Entity models.

def listen_to_server():
    """Continuously listen for messages from the server and update the game state."""
    buffer = ""
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                data_json = json.loads(line)
                if data_json['type'] == 'init':
                    initial_state = data_json['data']
                    for pos_str, block_type in initial_state.get('blocks', {}).items():
                        # Convert string "(x, y, z)" back to a tuple.
                        pos = eval(pos_str)  # Note: using eval() for simplicity.
                        if str(pos) not in blocks:
                            terrain.append(create_block(pos, block_type))
                elif data_json['type'] == 'block_place':
                    block_data = data_json['data']
                    pos = tuple(block_data['position'])
                    block_type = block_data['block_type']
                    if str(pos) not in blocks:
                        terrain.append(create_block(pos, block_type))
                elif data_json['type'] == 'block_remove':
                    pos = tuple(data_json['data']['position'])
                    for block in terrain:
                        if block.position == Vec3(*pos):
                            terrain.remove(block)
                            blocks.pop(str(block.position), None)
                            destroy(block)
                            break
                elif data_json['type'] == 'player_update':
                    # Handle remote player updates.
                    client_id = data_json.get('client_id')
                    # Skip processing if the update is from the local player.
                    if client_id and client_id != local_client_id:
                        player_data = data_json['data']
                        pos = Vec3(*player_data['position'])
                        rot = Vec3(*player_data['rotation'])
                        if client_id not in other_players:
                            # Create a simple model (a cube) for the remote player.
                            other_players[client_id] = Entity(
                                model='cube', 
                                color=color.azure, 
                                scale=(1, 2, 1),
                                position=pos
                            )
                        else:
                            # Update the remote player's position and rotation.
                            other_players[client_id].position = pos
                            other_players[client_id].rotation = rot
        except Exception as e:
            print("Error in server listener:", e)
            break

threading.Thread(target=listen_to_server, daemon=True).start()

# ------------------------------------
# Input Handling and Game Updates
# ------------------------------------
def input(key):
    global current_block, mouse_locked

    if key == '1':
        current_block = 'grass'
    elif key == '2':
        current_block = 'stone'
    
    if key == 'escape':
        mouse_locked = not mouse_locked
        mouse.locked = mouse_locked
        mouse.visible = not mouse_locked

    if mouse.hovered_entity:
        block = mouse.hovered_entity
        if key == 'right mouse down':  # Place block.
            new_pos = block.position + mouse.normal
            if str(new_pos) not in blocks:
                terrain.append(create_block(new_pos, current_block))
                msg = json.dumps({
                    'type': 'block_place',
                    'data': {
                        'position': [new_pos.x, new_pos.y, new_pos.z],
                        'block_type': current_block
                    }
                }) + "\n"  # Append newline for framing.
                try:
                    client_socket.sendall(msg.encode())
                except Exception as e:
                    print("Send failed:", e)
        elif key == 'left mouse down':  # Remove block.
            pos = Vec3(block.position)  # Save position before destroying.
            if block in terrain:
                terrain.remove(block)
                blocks.pop(str(pos), None)
                destroy(block)
                msg = json.dumps({
                    'type': 'block_remove',
                    'data': {
                        'position': [pos.x, pos.y, pos.z]
                    }
                }) + "\n"
                try:
                    client_socket.sendall(msg.encode())
                except Exception as e:
                    print("Send failed:", e)

def update():
    """Send the player's current position and rotation each frame."""
    msg = json.dumps({
        'type': 'player_update',
        'data': {
            'position': [player.x, player.y, player.z],
            'rotation': [player.rotation_x, player.rotation_y, player.rotation_z]
        }
    }) + "\n"
    try:
        client_socket.sendall(msg.encode())
    except Exception as e:
        print("Failed to send player update:", e)

app.run()

# (Optional) Save the world state locally on exit.
with open(save_file, 'w') as file:
    json.dump(blocks, file)
