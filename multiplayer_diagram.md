# Rally Game Multiplayer Architecture

## Overview
The Rally game uses a client-server architecture with the `ursinanetworking` library for multiplayer functionality. The system allows multiple players to race together in real-time, with synchronized car positions, rotations, models, textures, usernames, and cosmetics.

## Architecture Diagram

```
┌─────────────────┐      Network Communication     ┌─────────────────┐
│   Client        │◄──────────────────────────────►│   Server        │
│ (multiplayer.py)│                                │   (server.py)   │
└─────────────────┘                                └─────────────────┘
        │                                                   │
        │ Game Integration                                  │ Game Logic
        ▼                                                   ▼
┌─────────────────┐                                ┌─────────────────┐
│   Main Game     │                                │   Server UI     │
│   (main.py)     │                                │   (server.py)   │
└─────────────────┘                                └─────────────────┘
```

## Components

### 1. Server (server.py)
- **Purpose**: Hosts the multiplayer session and manages client connections
- **Key Features**:
  - Uses `UrsinaNetworkingServer` and `EasyUrsinaNetworkingServer`
  - Creates replicated variables for each connected player
  - Handles client connection/disconnection events
  - Updates player data in real-time

### 2. Client (multiplayer.py)
- **Purpose**: Connects to server and synchronizes player data
- **Key Features**:
  - Uses `UrsinaNetworkingClient` and `EasyUrsinaNetworkingClient`
  - Manages local representation of remote players
  - Interpolates positions and rotations for smooth movement
  - Handles replicated variable events

### 3. Main Game Integration (main.py)
- **Purpose**: Integrates multiplayer functionality with the main game
- **Key Features**:
  - Initializes multiplayer when enabled
  - Sends player data to server continuously
  - Updates multiplayer state in game loop

## Data Synchronization

### Server → Client (Replicated Variables)
The server maintains replicated variables for each player containing:
- `position`: Current 3D position (x, y, z)
- `rotation`: Current rotation (x, y, z)
- `model`: Car model file path
- `texture`: Car texture file path
- `username`: Player's display name
- `highscore`: Player's highscore
- `cosmetic`: Active cosmetic item
- `type`: Always "player"
- `id`: Unique client ID

### Client → Server (Message Events)
Clients send these messages to the server:
- `MyPosition`: Current car position
- `MyRotation`: Current car rotation
- `MyModel`: Current car model
- `MyTexture`: Current car texture
- `MyUsername`: Player username
- `MyHighscore`: Current highscore
- `MyCosmetic`: Active cosmetic

## Network Flow

### Connection Process
1. Server starts and listens for connections
2. Client connects with IP and port
3. Server creates replicated variable for the client
4. Server sends client their unique ID
5. Client receives ID and begins synchronization

### Data Update Process
1. Client sends position/rotation updates to server
2. Server updates replicated variables
3. All clients receive updated variable data
4. Clients interpolate remote player positions smoothly

### Disconnection Process
1. Client disconnects or times out
2. Server removes replicated variable
3. All clients remove the disconnected player

## Technical Implementation

### Server Events
```python
@server.event
def onClientConnected(client):
    # Create replicated variable for new player
    easy.create_replicated_variable(f"player_{client.id}", {...})

@server.event  
def onClientDisconnected(client):
    # Remove player's replicated variable
    easy.remove_replicated_variable_by_name(f"player_{client.id}")
```

### Client Events
```python
@client.event
def GetId(id):
    # Receive unique client ID from server
    self.selfId = id

@easy.event
def onReplicatedVariableCreated(variable):
    # Create visual representation for new player

@easy.event  
def onReplicatedVariableUpdated(variable):
    # Update player data when variables change

@easy.event
def onReplicatedVariableRemoved(variable):
    # Remove player when they disconnect
```

## Smooth Movement Interpolation

The client uses linear interpolation for smooth movement:
```python
def update_multiplayer(self):
    for player in self.players:
        # Smooth position interpolation
        self.players[p].position += (target_pos - current_pos) / 25
        # Smooth rotation interpolation  
        self.players[p].rotation += (target_rot - current_rot) / 25
```

## Leaderboard System

The multiplayer system maintains a real-time leaderboard showing:
- Player usernames
- Current highscore values
- Up to 5 players displayed

## Cosmetic Synchronization

Cosmetic items are synchronized across all players:
- Viking helmet
- Duck
- Banana
- Surfinbird
- Surfboard

## Network Requirements

- **Library**: ursinanetworking==2.1.4
- **Protocol**: TCP-based networking
- **Port**: Configurable (default shows "PORT")
- **IP**: Configurable (default shows "IP")

## Usage

### Starting a Server
1. Run `server.py` separately
2. Enter IP and port (or use defaults)
3. Click "Create" to start server

### Joining as Client
1. In main game, enable multiplayer
2. Enter server IP and port
3. Connect and start racing with others

## Limitations

- No built-in matchmaking system
- Manual IP/port configuration required
- No authentication/security features
- Limited to local network or port-forwarded servers
