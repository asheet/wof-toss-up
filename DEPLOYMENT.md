# 🎡 Wheel of Fortune - Docker Deployment Guide

This guide will help you deploy the Wheel of Fortune game using Docker containers.

## 📋 Prerequisites

- **Docker**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)
- **Git**: To clone the repository
- **Minimum 2GB RAM**: For running both containers
- **Port 3000**: Should be available on your system

## 🚀 Quick Start

### 1. Clone & Navigate
```bash
git clone <your-repo-url>
cd wof
```

### 2. Build & Run
```bash
# Build and start both services
docker-compose up --build

# Or run in background (detached mode)
docker-compose up --build -d
```

### 3. Access the Game
- **Game URL**: http://localhost:3000
- **Game will be ready in ~30-60 seconds**

### 4. Stop the Game
```bash
# Stop services
docker-compose down

# Stop and remove volumes (complete cleanup)
docker-compose down -v
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   (nginx:3000)  │────│  (FastAPI:8000) │
│                 │    │                 │
│ • Static Files  │    │ • WebSocket API │
│ • WebSocket     │    │ • Game Logic    │
│   Proxy         │    │ • Host Messages │
└─────────────────┘    └─────────────────┘
```

### Service Details

#### Frontend Container
- **Base**: `nginx:alpine`
- **Port**: 3000
- **Contents**: HTML, CSS, JavaScript
- **Features**: 
  - Static file serving
  - WebSocket proxy to backend
  - Gzip compression
  - Security headers

#### Backend Container
- **Base**: `python:3.11-slim`
- **Port**: 8000 (internal only)
- **Contents**: FastAPI application
- **Features**:
  - WebSocket game server
  - RESTful API endpoints
  - Game state management

## 🔧 Advanced Configuration

### Environment Variables

Create `.env` file in project root:
```env
# Port configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000

# Game settings (if implementing)
GAME_ROUND_TIME=45
GAME_ANSWER_TIME=10
```

### Custom Docker Compose

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  frontend:
    ports:
      - "8080:3000"  # Change external port
  
  backend:
    environment:
      - DEBUG=True
    ports:
      - "8000:8000"  # Expose backend directly
```

### Production Deployment

For production environments:

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With resource limits
docker-compose up -d --scale frontend=2
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 3000
lsof -i :3000

# Use different port
FRONTEND_PORT=8080 docker-compose up
```

#### Backend Not Responding
```bash
# Check backend logs
docker-compose logs backend

# Check backend health
docker-compose exec backend python -c "import requests; print(requests.get('http://localhost:8000/').status_code)"
```

#### WebSocket Connection Issues
```bash
# Check nginx configuration
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Test WebSocket proxy
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:3000/ws/test
```

### Health Checks

Both containers have built-in health checks:

```bash
# Check service health
docker-compose ps

# Detailed health status
docker inspect wof-frontend --format='{{.State.Health.Status}}'
docker inspect wof-backend --format='{{.State.Health.Status}}'
```

### Logs & Debugging

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Backend only
docker-compose logs backend

# Frontend only  
docker-compose logs frontend

# Last 50 lines
docker-compose logs --tail=50
```

## 📊 Performance Optimization

### Resource Limits

Add to `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
  
  frontend:
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'
```

### Caching Strategy

The nginx frontend includes:
- **Static asset caching**: 1 year for CSS/JS/images
- **Gzip compression**: Reduces bandwidth by ~70%
- **Browser caching**: Optimized cache headers

## 🔒 Security Features

### Built-in Security
- **Non-root containers**: Both services run as non-root users
- **Security headers**: XSS protection, content type sniffing prevention
- **Network isolation**: Services communicate through internal Docker network
- **Health monitoring**: Automated health checks and restart policies

### Additional Security (Production)
```bash
# Run with read-only filesystem
docker-compose up --read-only

# Scan for vulnerabilities
docker scan wof-backend
docker scan wof-frontend
```

## 🌐 Deployment Platforms

### AWS ECS
```bash
# Install ecs-cli
curl -Lo ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest

# Deploy to ECS
ecs-cli compose up --create-log-groups
```

### Digital Ocean Apps
```yaml
# .do/app.yaml
name: wheel-of-fortune
services:
- name: frontend
  source_dir: frontend
  github:
    repo: your-username/wof
    branch: main
  run_command: nginx -g "daemon off;"
```

### Heroku
```bash
# Install Heroku CLI and login
heroku create wof-app
heroku container:push web --app wof-app
heroku container:release web --app wof-app
```

## 📝 Maintenance

### Updates
```bash
# Pull latest images
docker-compose pull

# Rebuild with no cache
docker-compose build --no-cache

# Update and restart
docker-compose up --build -d
```

### Cleanup
```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Complete cleanup
docker system prune -a --volumes
```

## 🎯 Next Steps

- **SSL/HTTPS**: Add SSL certificates for production
- **Load Balancing**: Scale frontend for high traffic
- **Monitoring**: Add logging aggregation (ELK stack)
- **CI/CD**: Automate builds and deployments
- **Database**: Add persistent storage for game statistics

## 🆘 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs`
2. **Verify health**: `docker-compose ps`
3. **Test connectivity**: `curl http://localhost:3000`
4. **Restart services**: `docker-compose restart`
5. **Clean rebuild**: `docker-compose down && docker-compose up --build`

---

🎮 **Ready to play!** Your Wheel of Fortune game should now be running at http://localhost:3000
