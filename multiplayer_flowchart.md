# Rally Multiplayer Flowchart

## Server Startup Sequence
```mermaid
flowchart TD
    A[Server Application Starts] --> B[Display Server UI with IP/Port fields]
    B --> C[User clicks 'Create' button]
    C --> D[Initialize UrsinaNetworkingServer]
    D --> E[Set up event handlers]
    E --> F[Server ready for connections]
```

## Client Connection Sequence
```mermaid
flowchart TD
    A[Client enters IP/Port] --> B[Initialize UrsinaNetworkingClient]
    B --> C[Connect to server]
    C --> D{Connection successful?}
    D -->|Yes| E[Receive unique client ID]
    D -->|No| F[Show disconnected status]
    E --> G[Start sending player data]
    G --> H[Synchronize with other players]
```

## Data Synchronization Flow
```mermaid
flowchart LR
    subgraph Client1
        A[Player Input] --> B[Update Local Car]
        B --> C[Send: Position, Rotation, etc.]
    end
    
    subgraph Server
        C --> D[Receive Client Data]
        D --> E[Update Replicated Variables]
        E --> F[Broadcast to All Clients]
    end
    
    subgraph Client2
        F --> G[Receive Updates]
        G --> H[Interpolate Remote Players]
        H --> I[Update Visual Representation]
    end
    
    subgraph Client3
        F --> J[Receive Updates]
        J --> K[Interpolate Remote Players]
        K --> L[Update Visual Representation]
    end
```

## Event Handling
```mermaid
flowchart TD
    subgraph Server Events
        A[onClientConnected] --> B[Create player variable]
        C[onClientDisconnected] --> D[Remove player variable]
        E[MyPosition message] --> F[Update position]
        G[MyRotation message] --> H[Update rotation]
    end
    
    subgraph Client Events
        I[GetId] --> J[Store client ID]
        K[onReplicatedVariableCreated] --> L[Create player entity]
        M[onReplicatedVariableUpdated] --> N[Update player data]
        O[onReplicatedVariableRemoved] --> P[Remove player entity]
    end
```

## Multiplayer Game Loop
```mermaid
flowchart TD
    A[Game Update Loop] --> B{Multiplayer enabled?}
    B -->|Yes| C[Update multiplayer system]
    B -->|No| D[Continue single player]
    
    subgraph Multiplayer Update
        C --> E[Process network events]
        E --> F[Interpolate player positions]
        F --> G[Update leaderboard]
        G --> H[Check connection status]
    end
    
    subgraph Input Handling
        I[Player Input] --> J{Multiplayer active?}
        J -->|Yes| K[Send data to server]
        J -->|No| L[Local processing only]
    end
```

## Network Message Types
```mermaid
flowchart LR
    A[Client → Server Messages] --> B[MyPosition: Vec3 position]
    A --> C[MyRotation: Vec3 rotation]
    A --> D[MyModel: string model path]
    A --> E[MyTexture: string texture path]
    A --> F[MyUsername: string name]
    A --> G[MyHighscore: float score]
    A --> H[MyCosmetic: string cosmetic]
    
    I[Server → Client Messages] --> J[GetId: int client ID]
    I --> K[Replicated Variables: player data]
```

## Player Representation
```mermaid
flowchart TD
    A[Remote Player] --> B[CarRepresentation Entity]
    B --> C[3D Model & Texture]
    B --> D[Cosmetic Items]
    B --> E[Username Text]
    B --> F[Highscore Display]
    
    G[Local Player] --> H[Main Car Entity]
    H --> I[Full Physics]
    H --> J[Input Handling]
    H --> K[Audio & Effects]
    
    style H fill:#e6f3ff
