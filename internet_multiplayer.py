from ursinanetworking import *
from ursina import Entity, Vec3, color, destroy, Text
import socket
import threading
import time
from datetime import datetime
import logging

class InternetMultiplayer(Entity):
    def __init__(self, car, master_server_url=None):
        """
        Internet-based multiplayer client with public server support
        
        Args:
            car: The main car entity
            master_server_url: URL of the master server for server discovery
        """
        super().__init__()
        self.car = car
        
        # Server configuration
        self.master_server_url = master_server_url or "http://rally-master-server.example.com"
        self.current_server = None
        self.current_session = None
        
        # Client state
        self.connected = False
        self.connecting = False
        self.session_players = {}  # Remote players in current session
        self.server_list = []      # Available public servers
        
        # NAT traversal
        self.public_ip = None
        self.nat_type = None
        self.stun_servers = [
            "stun.l.google.com:19302",
            "stun1.l.google.com:19302", 
            "stun2.l.google.com:19302"
        ]
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('InternetMultiplayer')
        
        # UI elements
        self.setup_ui()
        
    def setup_ui(self):
        """Setup multiplayer UI elements"""
        self.connection_status = Text(
            text="Disconnected",
            position=(-0.8, 0.45),
            scale=0.8,
            color=color.red
        )
        
        self.server_browser_text = Text(
            text="Press M for Server Browser",
            position=(0, 0.4),
            scale=0.6,
            color=color.gray
        )
        
    def connect_to_master_server(self):
        """Connect to the master server for server discovery"""
        try:
            # This would typically use HTTP requests to get server list
            # For now, we'll simulate this with a local server list
            self.logger.info("Fetching server list from master server...")
            
            # Simulate server list response
            self.server_list = [
                {
                    'name': 'Public Server 1',
                    'ip': 'server1.rally-game.com',
                    'port': 25565,
                    'players': 3,
                    'max_players': 8,
                    'ping': 45,
                    'game_mode': 'race'
                },
                {
                    'name': 'Public Server 2', 
                    'ip': 'server2.rally-game.com',
                    'port': 25565,
                    'players': 0,
                    'max_players': 8,
                    'ping': 62,
                    'game_mode': 'drift'
                }
            ]
            
            self.show_server_browser()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to master server: {e}")
            self.connection_status.text = "Master Server Error"
            self.connection_status.color = color.red
    
    def connect_to_server(self, server_info):
        """Connect to a specific game server"""
        if self.connecting:
            return
            
        self.connecting = True
        self.connection_status.text = "Connecting..."
        self.connection_status.color = color.orange
        
        try:
            # Store server info
            self.current_server = server_info
            
            # Initialize networking client
            self.client = UrsinaNetworkingClient(server_info['ip'], server_info['port'])
            self.easy = EasyUrsinaNetworkingClient(self.client)
            
            # Setup event handlers
            self.setup_client_handlers()
            
            # Start connection timeout
            self.start_connection_timeout()
            
            self.logger.info(f"Connecting to {server_info['ip']}:{server_info['port']}")
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.connection_status.text = "Connection Failed"
            self.connection_status.color = color.red
            self.connecting = False
    
    def setup_client_handlers(self):
        """Setup client event handlers"""
        
        @self.client.event
        def ConnectionInfo(data):
            """Received connection information from server"""
            self.public_ip = data.get('public_ip')
            self.stun_servers = data.get('stun_servers', self.stun_servers)
            self.current_session = data.get('session_id')
            
            self.connected = True
            self.connecting = False
            self.connection_status.text = "Connected"
            self.connection_status.color = color.green
            
            self.logger.info(f"Connected to session {self.current_session}")
            
            # Perform NAT traversal if needed
            self.perform_nat_traversal()
        
        @self.client.event
        def SessionCreated(data):
            """Session created successfully"""
            self.current_session = data['session_id']
            self.logger.info(f"Created session {self.current_session}")
        
        @self.client.event
        def SessionJoined(data):
            """Joined session successfully"""
            self.current_session = data['session_id']
            self.logger.info(f"Joined session {self.current_session}")
        
        @self.client.event
        def JoinFailed(data):
            """Failed to join session"""
            self.connection_status.text = f"Join Failed: {data['reason']}"
            self.connection_status.color = color.red
            self.connecting = False
            self.logger.warning(f"Join failed: {data['reason']}")
        
        @self.client.event
        def ServerList(data):
            """Received server list from master server"""
            self.server_list = data['servers']
            self.show_server_browser()
        
        @self.client.event
        def GameMessage(data):
            """Received game message from another player"""
            self.handle_game_message(data)
        
        @self.client.event
        def PlayerJoined(data):
            """Another player joined the session"""
            player_id = data['player_id']
            username = data['username']
            self.logger.info(f"Player {username} joined the session")
            
            # Create representation for new player
            self.create_player_representation(player_id, data)
        
        @self.client.event
        def PlayerLeft(data):
            """Player left the session"""
            player_id = data['player_id']
            if player_id in self.session_players:
                destroy(self.session_players[player_id])
                del self.session_players[player_id]
                self.logger.info(f"Player {player_id} left the session")
    
    def perform_nat_traversal(self):
        """Perform NAT traversal to establish optimal connection"""
        self.logger.info("Performing NAT traversal...")
        
        # This would typically involve:
        # 1. STUN to discover public IP and NAT type
        # 2. TURN fallback if direct connection not possible
        # 3. ICE to establish best connection path
        
        # For simplicity, we'll just log this step
        self.logger.info("NAT traversal completed")
    
    def handle_game_message(self, data):
        """Handle incoming game messages"""
        message_type = data['message_type']
        message_data = data['data']
        from_client = data['from_client']
        
        if message_type == 'player_update':
            # Update remote player position/rotation
            if from_client in self.session_players:
                player = self.session_players[from_client]
                player.target_position = Vec3(message_data['position'])
                player.target_rotation = Vec3(message_data['rotation'])
                
                # Update other player properties
                if 'model' in message_data:
                    player.model = message_data['model']
                if 'texture' in message_data:
                    player.texture = message_data['texture']
                if 'username' in message_data:
                    if hasattr(player, 'username_text'):
                        player.username_text.text = message_data['username']
    
    def create_player_representation(self, player_id, player_data):
        """Create visual representation for a remote player"""
        from car import CarRepresentation, CarUsername
        
        position = Vec3(player_data.get('position', (-80, -30, 15)))
        rotation = Vec3(player_data.get('rotation', (0, 90, 0)))
        
        player_rep = CarRepresentation(self.car, position, rotation)
        
        # Set player properties
        if 'model' in player_data:
            player_rep.model = player_data['model']
        if 'texture' in player_data:
            player_rep.texture = player_data['texture']
        if 'username' in player_data:
            player_rep.text_object.text = player_data['username']
        
        self.session_players[player_id] = player_rep
    
    def send_player_update(self):
        """Send current player state to server"""
        if not self.connected:
            return
            
        try:
            self.client.send_message("PlayerUpdate", {
                'position': tuple(self.car.position),
                'rotation': tuple(self.car.rotation),
                'model': str(self.car.model_path),
                'texture': str(self.car.texture),
                'username': str(self.car.username_text),
                'highscore': round(self.car.highscore_count, 2),
                'cosmetic': str(self.car.current_cosmetic)
            })
        except Exception as e:
            self.logger.error(f"Failed to send player update: {e}")
            self.disconnect()
    
    def show_server_browser(self):
        """Display server browser UI"""
        # This would typically show a GUI with server list
        # For now, we'll just log the available servers
        self.logger.info("Available servers:")
        for server in self.server_list:
            self.logger.info(f"  {server['name']} - {server['players']}/{server['max_players']} players")
    
    def start_connection_timeout(self):
        """Start connection timeout timer"""
        def timeout_check():
            time.sleep(10)  # 10 second timeout
            if not self.connected and self.connecting:
                self.connection_status.text = "Connection Timeout"
                self.connection_status.color = color.red
                self.connecting = False
                self.logger.warning("Connection timeout")
        
        thread = threading.Thread(target=timeout_check, daemon=True)
        thread.start()
    
    def disconnect(self):
        """Disconnect from current server"""
        if hasattr(self, 'client'):
            try:
                self.client.close()
            except:
                pass
        
        self.connected = False
        self.connecting = False
        self.current_server = None
        self.current_session = None
        
        # Clean up player representations
        for player_id, player in self.session_players.items():
            destroy(player)
        self.session_players.clear()
        
        self.connection_status.text = "Disconnected"
        self.connection_status.color = color.red
        self.logger.info("Disconnected from server")
    
    def update(self):
        """Update multiplayer state"""
        if self.connected:
            # Send player updates regularly
            if hasattr(self, 'client'):
                try:
                    self.easy.process_net_events()
                    
                    # Send updates at a reasonable rate (e.g., 10 times per second)
                    current_time = time.time()
                    if not hasattr(self, 'last_update_time'):
                        self.last_update_time = 0
                    
                    if current_time - self.last_update_time > 0.1:  # 10 Hz
                        self.send_player_update()
                        self.last_update_time = current_time
                    
                    # Update remote player positions smoothly
                    for player_id, player in self.session_players.items():
                        if hasattr(player, 'target_position') and hasattr(player, 'target_rotation'):
                            player.position += (player.target_position - player.position) / 25
                            player.rotation += (player.target_rotation - player.rotation) / 25
                            
                except Exception as e:
                    self.logger.error(f"Network error: {e}")
                    self.disconnect()
    
    def input(self, key):
        """Handle input for multiplayer features"""
        if key == 'm':
            # Open server browser
            self.connect_to_master_server()
        
        elif key == 'n':
            # Create new session
            if self.connected:
                self.client.send_message("CreateSession", {
                    'public': True,
                    'max_players': 8,
                    'game_mode': 'race'
                })
        
        elif key == 'd':
            # Disconnect
            self.disconnect()
