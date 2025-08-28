from ursinanetworking import *
import socket
import threading
import time
from datetime import datetime
import json
import logging

class PublicServer:
    def __init__(self, public_ip=None, port=25565, stun_servers=None):
        """
        Public server for internet-based multiplayer with NAT traversal support
        
        Args:
            public_ip (str): Public IP address (auto-detected if None)
            port (int): Port to listen on
            stun_servers (list): List of STUN servers for NAT traversal
        """
        self.public_ip = public_ip or self.detect_public_ip()
        self.port = port
        self.stun_servers = stun_servers or [
            "stun.l.google.com:19302",
            "stun1.l.google.com:19302",
            "stun2.l.google.com:19302"
        ]
        
        # Server state
        self.sessions = {}  # session_id -> session_data
        self.players = {}   # client_id -> player_data
        self.server_list = []  # Public server listings
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('PublicServer')
        
        # Initialize networking
        self.setup_networking()
        
    def detect_public_ip(self):
        """Detect public IP address using external service"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            self.logger.warning("Could not detect public IP, using localhost")
            return "127.0.0.1"
    
    def setup_networking(self):
        """Initialize the networking server"""
        try:
            self.server = UrsinaNetworkingServer(self.public_ip, self.port)
            self.easy = EasyUrsinaNetworkingServer(self.server)
            self.logger.info(f"Public server started on {self.public_ip}:{self.port}")
            
            # Setup event handlers
            self.setup_event_handlers()
            
            # Start session cleanup thread
            self.start_cleanup_thread()
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    def setup_event_handlers(self):
        """Setup network event handlers"""
        
        @self.server.event
        def onClientConnected(client):
            """Handle new client connections"""
            session_id = self.generate_session_id()
            self.sessions[session_id] = {
                'clients': [client],
                'created_at': datetime.now(),
                'public': True,
                'max_players': 8
            }
            
            self.players[client.id] = {
                'session_id': session_id,
                'username': 'Guest',
                'connected_at': datetime.now(),
                'public_ip': client.address[0]
            }
            
            # Send connection info to client
            client.send_message("ConnectionInfo", {
                'session_id': session_id,
                'public_ip': self.public_ip,
                'port': self.port,
                'stun_servers': self.stun_servers
            })
            
            self.logger.info(f"Client {client.id} connected from {client.address}")
        
        @self.server.event
        def onClientDisconnected(client):
            """Handle client disconnections"""
            if client.id in self.players:
                session_id = self.players[client.id]['session_id']
                if session_id in self.sessions:
                    self.sessions[session_id]['clients'] = [
                        c for c in self.sessions[session_id]['clients'] if c.id != client.id
                    ]
                
                del self.players[client.id]
                self.logger.info(f"Client {client.id} disconnected")
        
        @self.server.event
        def CreateSession(client, session_data):
            """Create a new game session"""
            session_id = self.generate_session_id()
            self.sessions[session_id] = {
                'clients': [client],
                'created_at': datetime.now(),
                'public': session_data.get('public', True),
                'max_players': session_data.get('max_players', 8),
                'password': session_data.get('password'),
                'game_mode': session_data.get('game_mode', 'race')
            }
            
            self.players[client.id]['session_id'] = session_id
            client.send_message("SessionCreated", {'session_id': session_id})
        
        @self.server.event
        def JoinSession(client, session_data):
            """Join an existing game session"""
            session_id = session_data.get('session_id')
            password = session_data.get('password')
            
            if session_id in self.sessions:
                session = self.sessions[session_id]
                
                # Check password if required
                if session.get('password') and session['password'] != password:
                    client.send_message("JoinFailed", {'reason': 'invalid_password'})
                    return
                
                # Check player limit
                if len(session['clients']) >= session['max_players']:
                    client.send_message("JoinFailed", {'reason': 'session_full'})
                    return
                
                # Add client to session
                session['clients'].append(client)
                self.players[client.id]['session_id'] = session_id
                
                client.send_message("SessionJoined", {'session_id': session_id})
                self.logger.info(f"Client {client.id} joined session {session_id}")
            
            else:
                client.send_message("JoinFailed", {'reason': 'session_not_found'})
        
        @self.server.event
        def GetServerList(client, filters=None):
            """Get list of available public servers"""
            public_sessions = [
                {
                    'session_id': sid,
                    'player_count': len(session['clients']),
                    'max_players': session['max_players'],
                    'game_mode': session.get('game_mode', 'race'),
                    'has_password': bool(session.get('password')),
                    'created_at': session['created_at'].isoformat()
                }
                for sid, session in self.sessions.items()
                if session['public'] and not session.get('password')
            ]
            
            client.send_message("ServerList", {'servers': public_sessions})
        
        # Forward game-specific messages to session members
        @self.server.event
        def GameMessage(client, message_data):
            """Forward game messages to all session members"""
            if client.id in self.players:
                session_id = self.players[client.id]['session_id']
                if session_id in self.sessions:
                    for session_client in self.sessions[session_id]['clients']:
                        if session_client.id != client.id:  # Don't send back to sender
                            session_client.send_message("GameMessage", {
                                'from_client': client.id,
                                'message_type': message_data['type'],
                                'data': message_data['data']
                            })
    
    def generate_session_id(self):
        """Generate a unique session ID"""
        return f"session_{int(time.time())}_{len(self.sessions)}"
    
    def start_cleanup_thread(self):
        """Start thread to clean up inactive sessions"""
        def cleanup_loop():
            while True:
                time.sleep(60)  # Check every minute
                self.cleanup_inactive_sessions()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def cleanup_inactive_sessions(self):
        """Remove sessions that have been inactive for too long"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            # Remove empty sessions older than 5 minutes
            if len(session['clients']) == 0:
                if (current_time - session['created_at']).total_seconds() > 300:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            self.logger.info(f"Removed inactive session {session_id}")
    
    def run(self):
        """Run the server main loop"""
        self.logger.info("Public server running...")
        try:
            while True:
                self.easy.process_net_events()
                time.sleep(0.01)  # Small delay to prevent CPU overload
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
        except Exception as e:
            self.logger.error(f"Server error: {e}")

if __name__ == "__main__":
    # Example usage
    server = PublicServer(port=25565)
    server.run()
