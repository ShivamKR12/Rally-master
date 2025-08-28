# Internet Multiplayer System - Setup and Deployment Guide

## Overview

This guide explains how to set up and deploy the new internet-based multiplayer system for the Rally game. The system enables players to connect and play over the internet without requiring local network configuration.

## Prerequisites

### Software Requirements
- Python 3.7 or higher
- ursina==4.1.1
- ursinanetworking==2.1.4
- SQLite3 (for matchmaking service)
- Public IP address or domain name
- Port forwarding capabilities (for self-hosting)

### Network Requirements
- Open ports: 25565 (game), 25566 (matchmaking)
- Stable internet connection
- Sufficient bandwidth for multiple players

## File Structure

```
rally-game/
├── public_server.py          # Public game server
├── internet_multiplayer.py   # Enhanced client
├── matchmaking_service.py    # Matchmaking service
├── security_handler.py       # Security system
├── internet_multiplayer_config.json  # Configuration
├── INTERNET_MULTIPLAYER_DIAGRAM.md   # Architecture
└── INTERNET_MULTIPLAYER_SETUP_GUIDE.md  # This guide
```

## Deployment Options

### Option 1: Cloud Deployment (Recommended)

#### Using Cloud Services
1. **Server Hosting**: Use AWS, Google Cloud, or Azure
2. **Domain Setup**: Configure DNS for your domain
3. **Load Balancer**: Set up load balancing for multiple regions
4. **Database**: Use cloud SQL database for matchmaking

#### Steps:
1. Create cloud VM instances in desired regions
2. Install Python and dependencies
3. Upload game server files
4. Configure firewall rules to open ports
5. Set up domain name and DNS records
6. Configure load balancer
7. Deploy matchmaking service

### Option 2: Self-Hosting

#### Home Server Setup
1. **Static IP**: Obtain static IP from ISP or use dynamic DNS
2. **Port Forwarding**: Forward ports 25565 and 25566 to your server
3. **Server Machine**: Dedicated machine with good internet connection

#### Steps:
1. Install Python and dependencies on server
2. Configure router port forwarding
3. Set up dynamic DNS if no static IP
4. Start the public server and matchmaking service
5. Test connectivity from external network

## Configuration

### Server Configuration (public_server.py)
```python
server = PublicServer(
    public_ip="your.public.ip.address",  # Your public IP or domain
    port=25565,                         # Game server port
    stun_servers=[                      # STUN servers for NAT traversal
        "stun.l.google.com:19302",
        "stun1.l.google.com:19302"
    ]
)
```

### Matchmaking Service (matchmaking_service.py)
```python
matchmaking = MatchmakingService(
    host='0.0.0.0',      # Listen on all interfaces
    port=25566           # Matchmaking port
)
```

### Client Configuration (internet_multiplayer.py)
The client automatically uses the configuration from `internet_multiplayer_config.json`

## Starting the Services

### 1. Start Matchmaking Service
```bash
python matchmaking_service.py
```

### 2. Start Public Game Server
```bash
python public_server.py
```

### 3. Client Connection
Players run the main game and use the new internet multiplayer interface.

## Network Configuration

### Port Forwarding
If self-hosting, forward these ports on your router:
- **25565 TCP/UDP**: Game server communications
- **25566 TCP**: Matchmaking service
- **3478 UDP**: STUN/TURN services (if running your own)

### Firewall Rules
Allow incoming connections on:
- TCP: 25565, 25566
- UDP: 25565, 3478

## Security Setup

### SSL/TLS Certificates
For production deployment, obtain SSL certificates:
```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

### Database Security
- Use strong passwords for database access
- Enable encryption at rest
- Regular backups
- Access logging

## Monitoring and Maintenance

### Logging
Check log files for issues:
- Game server: `public_server.log`
- Matchmaking: `matchmaking_service.log`
- Security: `security_handler.log`

### Performance Monitoring
Monitor:
- CPU and memory usage
- Network bandwidth
- Player connection counts
- Error rates

### Regular Maintenance
1. **Updates**: Keep Python and dependencies updated
2. **Backups**: Regular database backups
3. **Logs**: Rotate and archive logs
4. **Security**: Regular security audits

## Testing the Setup

### Local Testing
1. Start all services locally
2. Connect from same machine
3. Verify basic functionality

### External Testing
1. Have someone outside your network connect
2. Test NAT traversal
3. Verify performance from different regions

### Load Testing
1. Simulate multiple players
2. Test under high load
3. Monitor resource usage

## Troubleshooting

### Common Issues

#### Connection Timeouts
- Check firewall settings
- Verify port forwarding
- Test network connectivity

#### NAT Traversal Failures
- Ensure STUN servers are accessible
- Check UDP port availability
- Consider TURN server fallback

#### Performance Issues
- Monitor server resources
- Check network latency
- Optimize game update rates

### Debug Mode
Enable debug logging in configuration:
```json
{
  "logging": {
    "level": "debug",
    "file": "debug.log"
  }
}
```

## Scaling for Production

### Horizontal Scaling
1. Deploy multiple server instances
2. Use load balancer
3. Implement session persistence

### Regional Deployment
1. Deploy servers in multiple regions
2. Use geo-DNS for routing
3. Sync player data between regions

### Database Scaling
1. Use database clustering
2. Implement read replicas
3. Use connection pooling

## Backup and Recovery

### Regular Backups
```bash
# Backup matchmaking database
sqlite3 matchmaking.db .dump > backup_$(date +%Y%m%d).sql
```

### Disaster Recovery
1. Keep offsite backups
2. Document recovery procedures
3. Test recovery regularly

## Security Best Practices

### Network Security
- Use VPN for administrative access
- Implement DDoS protection
- Regular security scans

### Application Security
- Keep software updated
- Use secure coding practices
- Regular security audits

### Data Protection
- Encrypt sensitive data
- Implement access controls
- Regular security training

## Performance Optimization

### Server Optimization
- Use efficient data structures
- Implement connection pooling
- Optimize database queries

### Network Optimization
- Use compression
- Implement prediction and interpolation
- Optimize update rates

### Client Optimization
- Efficient rendering of remote players
- Network state prediction
- Lag compensation

## Support and Maintenance

### Monitoring Tools
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for logs

### Alerting
- Set up monitoring alerts
- Email notifications for issues
- SMS alerts for critical problems

### Documentation
- Keep setup guides updated
- Document procedures
- Maintain runbooks

## Conclusion

This internet multiplayer system provides a robust foundation for online racing gameplay. Follow this guide carefully for deployment, and regularly maintain and monitor the system for optimal performance and security.

For additional support, refer to the architecture documentation and source code comments.
