# server.py
import socket
import threading
import json

HOST = '0.0.0.0'   # Listen on all network interfaces.
PORT = 6000        # Arbitrary port number.

clients = []  # List to track connected clients.
world_state = {
    'blocks': {},   # Format: { "(x, y, z)": "block_type", ... }
    'players': {}   # Format: { "client_id": { 'position': [...], ... }, ... }
}

def broadcast(message, source_client=None):
    """Send a message (already a string ending in '\n') to all clients except the source_client."""
    for client in clients:
        if client != source_client:
            try:
                client.sendall(message.encode())
            except Exception as e:
                print("Broadcast error:", e)
                if client in clients:
                    clients.remove(client)

def handle_client(client, addr):
    print(f"New connection from: {addr}")
    clients.append(client)
    
    # Send the initial world state to the new client.
    try:
        init_message = json.dumps({'type': 'init', 'data': world_state}) + "\n"
        client.sendall(init_message.encode())
    except Exception as e:
        print("Error sending initial state:", e)
    
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                # Split off one complete message.
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                if message['type'] == 'block_place':
                    block_data = message['data']  # Expects 'position' and 'block_type'
                    pos = block_data['position']
                    block_type = block_data['block_type']
                    world_state['blocks'][str(pos)] = block_type
                    broadcast(json.dumps(message) + "\n", source_client=client)
                elif message['type'] == 'block_remove':
                    pos = message['data']['position']
                    world_state['blocks'].pop(str(pos), None)
                    broadcast(json.dumps(message) + "\n", source_client=client)
                elif message['type'] == 'player_update':
                    # Attach a unique identifier (using the client's address) to the message.
                    message['client_id'] = str(addr)
                    world_state['players'][str(addr)] = message['data']
                    broadcast(json.dumps(message) + "\n", source_client=client)
        except Exception as e:
            print("Error handling client message:", e)
            break

    print(f"Connection closed from: {addr}")
    client.close()
    if client in clients:
        clients.remove(client)

# Set up the server socket.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print("Server started. Waiting for connections...")

while True:
    client_socket, client_addr = server.accept()
    threading.Thread(target=handle_client, args=(client_socket, client_addr), daemon=True).start()
