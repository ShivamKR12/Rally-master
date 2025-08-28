import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Tuple
import secrets
import base64

class SecurityHandler:
    def __init__(self, secret_key=None):
        """
        Security handler for internet multiplayer system
        
        Args:
            secret_key: Secret key for encryption and signatures (auto-generated if None)
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.sessions: Dict[str, dict] = {}  # session_id -> session_data
        self.player_tokens: Dict[str, str] = {}  # player_id -> auth_token
        
        # Anti-cheat measures
        self.cheat_detection_rules = self.setup_cheat_detection()
        self.suspicious_players: Dict[str, dict] = {}  # player_id -> suspicion_data
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('SecurityHandler')
        
        # Rate limiting
        self.rate_limits: Dict[str, dict] = {}  # ip -> rate_limit_data
        
        self.logger.info("Security handler initialized")
    
    def setup_cheat_detection(self) -> Dict:
        """Setup cheat detection rules"""
        return {
            'speed_hacking': {
                'max_speed': 50.0,  # Maximum allowed speed
                'acceleration_limit': 2.0,  # Maximum acceleration
                'check_interval': 1.0  # Check every second
            },
            'position_cheating': {
                'max_position_change': 100.0,  # Maximum position change per second
                'teleport_threshold': 50.0  # Teleport detection threshold
            },
            'time_manipulation': {
                'min_time_between_updates': 0.01,  # Minimum time between updates
                'max_time_between_updates': 2.0  # Maximum time between updates
            }
        }
    
    def generate_auth_token(self, player_id: str, username: str, expires_hours: int = 24) -> str:
        """
        Generate authentication token for player
        
        Args:
            player_id: Unique player identifier
            username: Player username
            expires_hours: Token expiration time in hours
            
        Returns:
            Base64 encoded authentication token
        """
        # Create token payload
        payload = {
            'player_id': player_id,
            'username': username,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
            'nonce': secrets.token_hex(16)
        }
        
        # Serialize and sign
        payload_json = json.dumps(payload, sort_keys=True)
        signature = self._generate_signature(payload_json)
        
        # Combine payload and signature
        token_data = {
            'payload': payload,
            'signature': signature
        }
        
        # Encode to base64
        token_json = json.dumps(token_data)
        token_b64 = base64.urlsafe_b64encode(token_json.encode()).decode()
        
        # Store token for validation
        self.player_tokens[player_id] = token_b64
        
        self.logger.info(f"Generated auth token for player {player_id}")
        return token_b64
    
    def validate_auth_token(self, token_b64: str) -> Tuple[bool, Optional[dict]]:
        """
        Validate authentication token
        
        Args:
            token_b64: Base64 encoded authentication token
            
        Returns:
            Tuple of (is_valid, payload) or (False, None)
        """
        try:
            # Decode token
            token_json = base64.urlsafe_b64decode(token_b64.encode()).decode()
            token_data = json.loads(token_json)
            
            # Check signature
            payload_json = json.dumps(token_data['payload'], sort_keys=True)
            expected_signature = self._generate_signature(payload_json)
            
            if not hmac.compare_digest(token_data['signature'], expected_signature):
                self.logger.warning("Token signature validation failed")
                return False, None
            
            # Check expiration
            expires_at = datetime.fromisoformat(token_data['payload']['expires_at'])
            if datetime.now() > expires_at:
                self.logger.warning("Token has expired")
                return False, None
            
            return True, token_data['payload']
            
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return False, None
    
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC signature for data"""
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def encrypt_data(self, data: dict) -> str:
        """
        Encrypt sensitive data (simplified version - would use proper encryption in production)
        
        Args:
            data: Data to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        # In production, this would use proper encryption like AES
        # For this example, we'll use a simple obfuscation
        data_json = json.dumps(data)
        encrypted = base64.urlsafe_b64encode(data_json.encode()).decode()
        return encrypted
    
    def decrypt_data(self, encrypted_data: str) -> Optional[dict]:
        """
        Decrypt data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted data or None if invalid
        """
        try:
            decrypted = base64.urlsafe_b64decode(encrypted_data.encode()).decode()
            return json.loads(decrypted)
        except:
            return None
    
    def check_rate_limit(self, ip_address: str, action: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """
        Check if request is within rate limits
        
        Args:
            ip_address: Client IP address
            action: Type of action being performed
            max_requests: Maximum allowed requests
            window_seconds: Time window in seconds
            
        Returns:
            True if within limits, False if rate limited
        """
        current_time = time.time()
        rate_key = f"{ip_address}_{action}"
        
        if rate_key not in self.rate_limits:
            self.rate_limits[rate_key] = {
                'requests': 1,
                'first_request': current_time,
                'last_request': current_time
            }
            return True
        
        rate_data = self.rate_limits[rate_key]
        
        # Reset if window has passed
        if current_time - rate_data['first_request'] > window_seconds:
            rate_data['requests'] = 1
            rate_data['first_request'] = current_time
            rate_data['last_request'] = current_time
            return True
        
        # Check if within limits
        if rate_data['requests'] >= max_requests:
            self.logger.warning(f"Rate limit exceeded for {ip_address} - {action}")
            return False
        
        rate_data['requests'] += 1
        rate_data['last_request'] = current_time
        
        return True
    
    def detect_cheating(self, player_id: str, game_data: dict) -> Dict[str, bool]:
        """
        Detect potential cheating based on game data
        
        Args:
            player_id: Player identifier
            game_data: Game state data
            
        Returns:
            Dictionary of cheat detection results
        """
        results = {
            'speed_hacking': False,
            'position_cheating': False,
            'time_manipulation': False
        }
        
        # Speed hacking detection
        if 'speed' in game_data:
            if game_data['speed'] > self.cheat_detection_rules['speed_hacking']['max_speed']:
                results['speed_hacking'] = True
                self.log_suspicious_activity(player_id, 'speed_hacking', game_data['speed'])
        
        # Position cheating detection
        if 'position' in game_data and 'previous_position' in game_data:
            position_change = self._calculate_distance(
                game_data['position'],
                game_data['previous_position']
            )
            
            if position_change > self.cheat_detection_rules['position_cheating']['max_position_change']:
                results['position_cheating'] = True
                self.log_suspicious_activity(player_id, 'position_cheating', position_change)
        
        # Time manipulation detection
        if 'update_interval' in game_data:
            interval = game_data['update_interval']
            rules = self.cheat_detection_rules['time_manipulation']
            
            if interval < rules['min_time_between_updates'] or interval > rules['max_time_between_updates']:
                results['time_manipulation'] = True
                self.log_suspicious_activity(player_id, 'time_manipulation', interval)
        
        return results
    
    def _calculate_distance(self, pos1, pos2):
        """Calculate distance between two positions"""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2 + (pos1[2] - pos2[2])**2)**0.5
    
    def log_suspicious_activity(self, player_id: str, cheat_type: str, value: float):
        """Log suspicious activity for monitoring"""
        if player_id not in self.suspicious_players:
            self.suspicious_players[player_id] = {
                'first_detection': datetime.now(),
                'detections': {},
                'total_score': 0
            }
        
        player_data = self.suspicious_players[player_id]
        
        if cheat_type not in player_data['detections']:
            player_data['detections'][cheat_type] = {
                'count': 0,
                'last_detection': datetime.now(),
                'max_value': value
            }
        
        detection_data = player_data['detections'][cheat_type]
        detection_data['count'] += 1
        detection_data['last_detection'] = datetime.now()
        detection_data['max_value'] = max(detection_data['max_value'], value)
        
        # Calculate suspicion score
        score_weights = {
            'speed_hacking': 10,
            'position_cheating': 8,
            'time_manipulation': 5
        }
        
        player_data['total_score'] += score_weights.get(cheat_type, 1)
        
        self.logger.warning(f"Suspicious activity detected: {player_id} - {cheat_type} - {value}")
        
        # Auto-ban if score exceeds threshold
        if player_data['total_score'] > 50:
            self.ban_player(player_id, f"Auto-ban: excessive cheat detection score {player_data['total_score']}")
    
    def ban_player(self, player_id: str, reason: str):
        """Ban player from the game"""
        # In production, this would persist to database and notify all servers
        self.logger.warning(f"Player {player_id} banned: {reason}")
        
        # Remove any active tokens
        if player_id in self.player_tokens:
            del self.player_tokens[player_id]
        
        # TODO: Implement persistent ban system
    
    def validate_player_input(self, player_id: str, input_data: dict) -> bool:
        """
        Validate player input for potential manipulation
        
        Args:
            player_id: Player identifier
            input_data: Input data to validate
            
        Returns:
            True if input appears valid, False if suspicious
        """
        # Check for extreme values
        if 'steering' in input_data and abs(input_data['steering']) > 2.0:
            return False
        
        if 'throttle' in input_data and (input_data['throttle'] < 0 or input_data['throttle'] > 1.5):
            return False
        
        if 'brake' in input_data and (input_data['brake'] < 0 or input_data['brake'] > 1.5):
            return False
        
        return True
    
    def generate_session_key(self) -> str:
        """Generate unique session key for secure communications"""
        return secrets.token_hex(32)
    
    def cleanup_old_sessions(self):
        """Clean up expired sessions and tokens"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session_data in self.sessions.items():
            if 'expires_at' in session_data and current_time > session_data['expires_at']:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        # Clean up old rate limits
        current_time_ts = time.time()
        rate_keys_to_remove = [
            key for key, data in self.rate_limits.items()
            if current_time_ts - data['last_request'] > 3600  # 1 hour
        ]
        
        for key in rate_keys_to_remove:
            del self.rate_limits[key]
    
    def get_security_report(self) -> dict:
        """Get security status report"""
        return {
            'active_sessions': len(self.sessions),
            'active_tokens': len(self.player_tokens),
            'suspicious_players': len(self.suspicious_players),
            'rate_limited_ips': len(self.rate_limits),
            'total_bans': 0  # Would track actual bans in production
        }

# Example usage
if __name__ == "__main__":
    security = SecurityHandler()
    
    # Generate auth token
    token = security.generate_auth_token("player123", "TestPlayer")
    print(f"Generated token: {token}")
    
    # Validate token
    is_valid, payload = security.validate_auth_token(token)
    print(f"Token valid: {is_valid}")
    if is_valid:
        print(f"Payload: {payload}")
