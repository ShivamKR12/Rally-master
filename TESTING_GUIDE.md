# Internet Multiplayer System - Testing Guide

## Overview
This guide explains how to test the new internet multiplayer system for the Rally game. Follow these steps to verify that all components work correctly.

## Prerequisites for Testing
- Python 3.7+ installed
- ursina and ursinanetworking packages
- At least two computers for proper testing (can use virtual machines)
- Network connectivity between test machines

## Testing Scenarios

### 1. Local Machine Testing (All components on same computer)

#### Step 1: Start Matchmaking Service
```bash
python matchmaking_service.py
```
**Expected**: Service starts on port 25566, shows "Matchmaking service started" message

#### Step 2: Start Public Server
```bash
python public_server.py
```
**Expected**: Server starts on port 25565, shows "Public server started" message

#### Step 3: Test Client Connection
1. Open the main game (`python main.py`)
2. Press 'M' to open server browser
3. Verify server list appears
4. Connect to local server

**Expected**: Connection status changes to "Connected", player representations appear

### 2. Local Network Testing (Multiple computers)

#### Setup:
- Computer A: Run matchmaking service + public server
- Computer B: Run game client

#### Step 1: On Computer A
```bash
# Find local IP address (e.g., 192.168.1.100)
ipconfig (Windows) or ifconfig (Linux/Mac)

# Start services
python matchmaking_service.py
python public_server.py
```

#### Step 2: On Computer B
1. Edit `internet_multiplayer_config.json`:
```json
{
  "matchmaking": {
    "master_server_url": "http://192.168.1.100:25566"
  }
}
```
2. Start game: `python main.py`
3. Press 'M' to connect

**Expected**: Successful connection, players visible on both machines

### 3. Internet Testing (Different networks)

#### Requirements:
- Public IP address or port forwarding
- Or use cloud testing services

#### Step 1: Set Up Public Server
1. Configure router port forwarding for ports 25565 and 25566
2. Start services on public server machine
3. Note public IP address

#### Step 2: Remote Client Testing
1. On remote machine, update config with public IP
2. Test connection
3. Verify NAT traversal works

## Testing Checklist

### ✅ Basic Functionality Tests
- [ ] Matchmaking service starts without errors
- [ ] Public server starts without errors  
- [ ] Client can discover servers
- [ ] Client can connect to server
- [ ] Player positions synchronize
- [ ] Player rotations synchronize
- [ ] Player models/textures sync
- [ ] Disconnections handled properly

### ✅ Network Tests
- [ ] Localhost connection works
- [ ] LAN connection works
- [ ] NAT traversal functions
- [ ] Connection timeouts handled
- [ ] Network lag simulated correctly
- [ ] Packet loss recovery works

### ✅ Security Tests
- [ ] Authentication token generation
- [ ] Token validation works
- [ ] Rate limiting functions
- [ ] Cheat detection triggers
- [ ] Input validation works

### ✅ Performance Tests
- [ ] Multiple players (2-8) supported
- [ ] Memory usage reasonable
- [ ] CPU usage acceptable
- [ ] Network bandwidth usage optimal

## Step-by-Step Testing Procedure

### Phase 1: Single Machine Validation
1. **Start Services**: Run matchmaking and server on same machine
2. **Client Test**: Connect from same machine
3. **Basic Verification**: Check if players appear, positions sync
4. **Stress Test**: Create multiple player representations

### Phase 2: Local Network Testing
1. **Server Setup**: Run services on one machine
2. **Client Setup**: Connect from another machine on same network
3. **Network Tests**: Verify connectivity, test with firewall
4. **Multiplayer Test**: Have multiple clients connect

### Phase 3: Internet Testing
1. **Public Setup**: Configure port forwarding
2. **Remote Connection**: Test from different network
3. **NAT Test**: Verify traversal works
4. **Performance Test**: Measure latency and bandwidth

### Phase 4: Edge Case Testing
1. **Connection Loss**: Test network disconnections
2. **Server Restart**: Test reconnection ability
3. **Full Server**: Test player limits
4. **Invalid Data**: Test error handling

## Test Data and Expected Results

### Connection Test
**Input**: Client connects to server
**Expected**: Connection status "Connected", player entity created

### Position Sync Test  
**Input**: Player moves car
**Expected**: Remote players see movement with smooth interpolation

### Disconnection Test
**Input**: Client disconnects
**Expected**: Player entity removed, cleanup performed

### Security Test
**Input**: Invalid token
**Expected**: Connection rejected, appropriate error message

## Debugging Common Issues

### Connection Failures
1. Check firewall settings
2. Verify port forwarding
3. Test network connectivity
4. Check service logs

### Sync Issues
1. Verify update rates
2. Check network latency
3. Test interpolation settings

### Performance Problems
1. Monitor CPU/Memory usage
2. Check network bandwidth
3. Optimize update frequency

## Log Analysis

### Matchmaking Service Logs
Look for:
- Server registration events
- Client connection attempts
- Error messages

### Public Server Logs
Look for:
- Player connections/disconnections
- Game message processing
- NAT traversal events

### Client Logs
Look for:
- Connection status changes
- Network errors
- Sync issues

## Automated Testing Scripts

For development, you can create test scripts:

```python
# test_connection.py
import socket

def test_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((host, port))
            return True
    except:
        return False

# Test matchmaking service
print("Matchmaking service:", test_port("localhost", 25566))
print("Public server:", test_port("localhost", 25565))
```

## Performance Metrics to Monitor

- **Latency**: Round-trip time for updates
- **Bandwidth**: Data transfer rates
- **CPU Usage**: Server and client processing
- **Memory**: RAM usage patterns
- **Connections**: Active player count

## Testing Tools

### Network Simulation
- Use `tc` (Linux) for network throttling
- WANem for network condition simulation
- Clumsy (Windows) for packet manipulation

### Monitoring Tools
- Wireshark for packet analysis
- htop/top for resource monitoring
- netstat for connection monitoring

## Conclusion

Thorough testing is essential for a reliable multiplayer experience. Start with local testing, progress to network testing, and finally test internet connectivity. Monitor performance and address any issues found during testing.

Remember to test both normal operation and edge cases to ensure robustness.
