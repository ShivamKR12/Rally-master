
#!/usr/bin/env python3
"""
Simple test script for Internet Multiplayer System
This script helps verify basic functionality without running the full game.
"""

import subprocess
import time
import threading
import sys
import os
from ursinanetworking import UrsinaNetworkingClient, UrsinaNetworkingServer
import socket

def test_basic_connectivity():
    """Test basic network connectivity between services"""
    print("🔍 Testing basic connectivity...")
    
    # Test if ports are available
    def check_port(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except:
            return False
    
    ports = [25565, 25566]
    for port in ports:
        if check_port(port):
            print(f"✅ Port {port} is available")
        else:
            print(f"❌ Port {port} is already in use")
    
    return True

def test_matchmaking_service():
    """Test the matchmaking service"""
    print("\n🎯 Testing Matchmaking Service...")
    
    try:
        # Try to start matchmaking service in a subprocess
        process = subprocess.Popen(
            [sys.executable, "matchmaking_service.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Matchmaking service started successfully")
            
            # Test connection to matchmaking service
            try:
                client = UrsinaNetworkingClient("127.0.0.1", 25566)
                time.sleep(1)
                print("✅ Can connect to matchmaking service")
                # Note: UrsinaNetworkingClient doesn't have a close() method in some versions
                # We'll just let it be garbage collected
            except Exception as e:
                print(f"❌ Cannot connect to matchmaking service: {e}")
            
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Matchmaking service failed to start: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing matchmaking service: {e}")
        return False

def test_public_server():
    """Test the public server"""
    print("\n🎮 Testing Public Server...")
    
    try:
        # Try to start public server in a subprocess
        process = subprocess.Popen(
            [sys.executable, "public_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Public server started successfully")
            
            # Test connection to public server
            try:
                client = UrsinaNetworkingClient("127.0.0.1", 25565)
                time.sleep(1)
                print("✅ Can connect to public server")
                # Note: UrsinaNetworkingClient doesn't have a close() method in some versions
                # We'll just let it be garbage collected
            except Exception as e:
                print(f"❌ Cannot connect to public server: {e}")
            
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Public server failed to start: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing public server: {e}")
        return False

def test_security_handler():
    """Test the security handler"""
    print("\n🔒 Testing Security Handler...")
    
    try:
        # Import and test security handler
        from security_handler import SecurityHandler
        
        security = SecurityHandler()
        
        # Test token generation
        token = security.generate_auth_token("test_player", "Test User")
        if token:
            print("✅ Token generation works")
        else:
            print("❌ Token generation failed")
            return False
        
        # Test token validation
        is_valid, payload = security.validate_auth_token(token)
        if is_valid and payload:
            print("✅ Token validation works")
        else:
            print("❌ Token validation failed")
            return False
        
        # Test invalid token
        is_valid, payload = security.validate_auth_token("invalid_token")
        if not is_valid:
            print("✅ Invalid token rejection works")
        else:
            print("❌ Invalid token not rejected")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing security handler: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        import json
        
        with open("internet_multiplayer_config.json", "r") as f:
            config = json.load(f)
        
        required_sections = ["multiplayer", "matchmaking", "security", "network"]
        for section in required_sections:
            if section in config:
                print(f"✅ Configuration section '{section}' found")
            else:
                print(f"❌ Configuration section '{section}' missing")
                return False
        
        print("✅ Configuration file is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("INTERNET MULTIPLAYER SYSTEM - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Basic Connectivity", test_basic_connectivity),
        ("Configuration", test_configuration),
        ("Security Handler", test_security_handler),
        ("Matchmaking Service", test_matchmaking_service),
        ("Public Server", test_public_server),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The system should work correctly.")
        print("\nNext steps:")
        print("1. Run 'python matchmaking_service.py' in one terminal")
        print("2. Run 'python public_server.py' in another terminal") 
        print("3. Run 'python main.py' to test the game client")
    else:
        print("⚠️  SOME TESTS FAILED. Check the errors above.")
        print("\nTroubleshooting tips:")
        print("- Make sure ports 25565 and 25566 are available")
        print("- Check that all dependencies are installed")
        print("- Verify file permissions")
    
    return all_passed

if __name__ == "__main__":
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    run_all_tests()
