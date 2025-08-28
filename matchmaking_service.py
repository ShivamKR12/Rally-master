from ursinanetworking import *
import threading
import time
from datetime import datetime
import json
import logging
import sqlite3
from typing import Dict, List, Optional

class MatchmakingService:
    def __init__(self, host='0.0.0.0', port=25566):
        """
        Matchmaking service for internet-based multiplayer
        
        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        
        # Database for persistent storage
        self.db_path = "matchmaking.db"
        self.setup_database()
        
        # In-memory storage
        self.servers: Dict[str, dict] = {}  # server_id -> server_data
        self.players: Dict[str, dict] = {}  # player_id -> player_data
        self.lobbies: Dict[str, dict] = {}  # lobby_id -> lobby_data
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('MatchmakingService')
        
        # Initialize networking
        self.setup_networking()
        
        # Start maintenance threads
        self.start_maintenance_threads()
    
    def setup_database(self):
        """Setup SQLite database for persistent storage"""
        # Setup logging first if not already set up
        if not hasattr(self, 'logger'):
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger('MatchmakingService')
            
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    server_id TEXT PRIMARY KEY,
                    ip TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    name TEXT,
                    max_players INTEGER,
                    current_players INTEGER,
                    game_mode TEXT,
                    region TEXT,
                    ping INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    username TEXT,
                    region TEXT,
                    skill_level INTEGER,
                    last_seen TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS lobbies (
                    lobby_id TEXT PRIMARY KEY,
                    name TEXT,
                    max_players INTEGER,
                    current_players INTEGER,
                    game_mode TEXT,
                    password TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            self.logger.info("Database setup complete")
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            raise
    
    def setup_networking(self):
        """Initialize the networking server"""
        try:
            self.server = UrsinaNetworkingServer(self.host, self.port)
            self.easy = EasyUrsinaNetworkingServer(self.server)
            self.logger.info(f"Matchmaking service started on {self.host}:{self.port}")
            
            # Setup event handlers
            self.setup_event_handlers()
            
        except Exception as e:
            self.logger.error(f"Failed to start matchmaking service: {e}")
            raise
    
    def setup_event_handlers(self):
        """Setup network event handlers"""
        
        @self.server.event
        def RegisterServer(client, server_data):
            """Register a game server with the matchmaking service"""
            server_id = f"server_{client.id}_{int(time.time())}"
            
            server_info = {
                'server_id': server_id,
                'ip': server_data['ip'],
                'port': server_data['port'],
                'name': server_data.get('name', 'Unnamed Server'),
                'max_players': server_data.get('max_players', 8),
                'current_players': server_data.get('current_players', 0),
                'game_mode': server_data.get('game_mode', 'race'),
                'region': server_data.get('region', 'global'),
                'ping': server_data.get('ping', 0),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Store in memory
            self.servers[server_id] = server_info
            
            # Store in database
            self.cursor.execute('''
                INSERT OR REPLACE INTO servers 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                server_id, server_info['ip'], server_info['port'], server_info['name'],
                server_info['max_players'], server_info['current_players'], server_info['game_mode'],
                server_info['region'], server_info['ping'], server_info['created_at'], server_info['updated_at']
            ))
            self.conn.commit()
            
            client.send_message("ServerRegistered", {'server_id': server_id})
            self.logger.info(f"Server registered: {server_info['name']}")
        
        @self.server.event
        def UpdateServer(client, update_data):
            """Update server information"""
            server_id = update_data.get('server_id')
            if server_id in self.servers:
                # Update server data
                for key, value in update_data.items():
                    if key != 'server_id' and key in self.servers[server_id]:
                        self.servers[server_id][key] = value
                
                self.servers[server_id]['updated_at'] = datetime.now()
                
                # Update database
                self.cursor.execute('''
                    UPDATE servers SET 
                    current_players = ?, updated_at = ?
                    WHERE server_id = ?
                ''', (
                    self.servers[server_id]['current_players'],
                    self.servers[server_id]['updated_at'],
                    server_id
                ))
                self.conn.commit()
        
        @self.server.event
        def GetServerList(client, filters=None):
            """Get list of available servers with optional filters"""
            filters = filters or {}
            
            # Filter servers based on criteria
            filtered_servers = []
            for server in self.servers.values():
                # Apply filters
                if filters.get('region') and server['region'] != filters['region']:
                    continue
                if filters.get('game_mode') and server['game_mode'] != filters['game_mode']:
                    continue
                if filters.get('max_players') and server['max_players'] < filters['max_players']:
                    continue
                if filters.get('min_players') and server['current_players'] < filters['min_players']:
                    continue
                
                filtered_servers.append(server)
            
            # Sort by ping (lowest first)
            filtered_servers.sort(key=lambda x: x['ping'])
            
            client.send_message("ServerList", {'servers': filtered_servers})
        
        @self.server.event
        def CreateLobby(client, lobby_data):
            """Create a new lobby"""
            lobby_id = f"lobby_{client.id}_{int(time.time())}"
            
            lobby_info = {
                'lobby_id': lobby_id,
                'name': lobby_data.get('name', 'New Lobby'),
                'max_players': lobby_data.get('max_players', 4),
                'current_players': 1,  # Creator is first player
                'game_mode': lobby_data.get('game_mode', 'race'),
                'password': lobby_data.get('password'),
                'created_by': client.id,
                'created_at': datetime.now(),
                'players': [client.id]
            }
            
            self.lobbies[lobby_id] = lobby_info
            
            # Store in database
            self.cursor.execute('''
                INSERT INTO lobbies 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lobby_id, lobby_info['name'], lobby_info['max_players'],
                lobby_info['current_players'], lobby_info['game_mode'],
                lobby_info['password'], lobby_info['created_by'], lobby_info['created_at']
            ))
            self.conn.commit()
            
            client.send_message("LobbyCreated", {'lobby_id': lobby_id})
            self.logger.info(f"Lobby created: {lobby_info['name']}")
        
        @self.server.event
        def JoinLobby(client, join_data):
            """Join an existing lobby"""
            lobby_id = join_data.get('lobby_id')
            password = join_data.get('password')
            
            if lobby_id in self.lobbies:
                lobby = self.lobbies[lobby_id]
                
                # Check password
                if lobby.get('password') and lobby['password'] != password:
                    client.send_message("JoinFailed", {'reason': 'invalid_password'})
                    return
                
                # Check player limit
                if len(lobby['players']) >= lobby['max_players']:
                    client.send_message("JoinFailed", {'reason': 'lobby_full'})
                    return
                
                # Add player to lobby
                lobby['players'].append(client.id)
                lobby['current_players'] = len(lobby['players'])
                
                # Update database
                self.cursor.execute('''
                    UPDATE lobbies SET current_players = ? WHERE lobby_id = ?
                ''', (lobby['current_players'], lobby_id))
                self.conn.commit()
                
                # Notify all lobby members
                for player_id in lobby['players']:
                    # This would typically send to each player's client
                    pass
                
                client.send_message("LobbyJoined", {'lobby_id': lobby_id})
                self.logger.info(f"Player joined lobby {lobby_id}")
            
            else:
                client.send_message("JoinFailed", {'reason': 'lobby_not_found'})
        
        @self.server.event
        def FindPlayers(client, criteria):
            """Find players based on skill level and preferences"""
            # This would implement skill-based matchmaking
            # For now, return some dummy data
            suggested_players = [
                {'player_id': 'player1', 'username': 'Racer1', 'skill_level': 5},
                {'player_id': 'player2', 'username': 'Speedster', 'skill_level': 7}
            ]
            
            client.send_message("PlayerSuggestions", {'players': suggested_players})
        
        @self.server.event
        def Heartbeat(client):
            """Handle client heartbeat for connection monitoring"""
            # Update last seen time for the client
            # This helps detect disconnected clients
            pass
    
    def start_maintenance_threads(self):
        """Start maintenance threads for cleanup and updates"""
        
        def cleanup_old_servers():
            """Remove servers that haven't been updated recently"""
            while True:
                time.sleep(60)  # Check every minute
                current_time = datetime.now()
                servers_to_remove = []
                
                for server_id, server in self.servers.items():
                    if (current_time - server['updated_at']).total_seconds() > 300:  # 5 minutes
                        servers_to_remove.append(server_id)
                
                # Use thread-local database connection
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for server_id in servers_to_remove:
                    del self.servers[server_id]
                    cursor.execute('DELETE FROM servers WHERE server_id = ?', (server_id,))
                    self.logger.info(f"Removed stale server: {server_id}")
                
                conn.commit()
                conn.close()
        
        def cleanup_old_lobbies():
            """Remove empty lobbies"""
            while True:
                time.sleep(120)  # Check every 2 minutes
                lobbies_to_remove = []
                
                for lobby_id, lobby in self.lobbies.items():
                    if lobby['current_players'] == 0:
                        lobbies_to_remove.append(lobby_id)
                
                # Use thread-local database connection
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for lobby_id in lobbies_to_remove:
                    del self.lobbies[lobby_id]
                    cursor.execute('DELETE FROM lobbies WHERE lobby_id = ?', (lobby_id,))
                    self.logger.info(f"Removed empty lobby: {lobby_id}")
                
                conn.commit()
                conn.close()
        
        # Start maintenance threads
        threading.Thread(target=cleanup_old_servers, daemon=True).start()
        threading.Thread(target=cleanup_old_lobbies, daemon=True).start()
    
    def get_server_stats(self):
        """Get statistics about current servers"""
        total_servers = len(self.servers)
        total_players = sum(server['current_players'] for server in self.servers.values())
        total_lobbies = len(self.lobbies)
        
        return {
            'total_servers': total_servers,
            'total_players': total_players,
            'total_lobbies': total_lobbies,
            'regions': list(set(server['region'] for server in self.servers.values()))
        }
    
    def find_best_server(self, player_region, game_mode=None, min_players=0):
        """Find the best server for a player based on criteria"""
        best_server = None
        best_score = float('inf')
        
        for server in self.servers.values():
            # Skip if doesn't match criteria
            if game_mode and server['game_mode'] != game_mode:
                continue
            if server['current_players'] < min_players:
                continue
            if server['current_players'] >= server['max_players']:
                continue
            
            # Calculate score (lower is better)
            score = server['ping']  # Base score on ping
            
            # Penalize servers in different regions
            if server['region'] != player_region:
                score += 100  # Add penalty for different region
            
            if score < best_score:
                best_score = score
                best_server = server
        
        return best_server
    
    def run(self):
        """Run the matchmaking service main loop"""
        self.logger.info("Matchmaking service running...")
        try:
            while True:
                self.easy.process_net_events()
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.logger.info("Matchmaking service shutting down...")
            self.conn.close()
        except Exception as e:
            self.logger.error(f"Matchmaking service error: {e}")
            self.conn.close()

if __name__ == "__main__":
    # Example usage
    matchmaking = MatchmakingService(port=25566)
    matchmaking.run()
