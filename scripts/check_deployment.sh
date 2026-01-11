#!/bin/bash

# Quick deployment check script
# Run this on your Vultr VM to check if services are running

echo "=== Checking Deployment Status ==="
echo ""

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
    echo "❌ Docker is not running"
    exit 1
else
    echo "✅ Docker is running"
fi

echo ""

# Check if we're in the project directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "⚠️  docker-compose.prod.yml not found in current directory"
    echo "Looking for project directory..."
    
    if [ -d "$HOME/DeltaHacks12" ]; then
        cd "$HOME/DeltaHacks12"
        echo "Found project at: $HOME/DeltaHacks12"
    elif [ -d "/root/DeltaHacks12" ]; then
        cd /root/DeltaHacks12
        echo "Found project at: /root/DeltaHacks12"
    else
        echo "❌ Project directory not found. Please navigate to your project directory first."
        exit 1
    fi
fi

echo ""
echo "=== Docker Compose Service Status ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== Testing Health Endpoints ==="

# Test backend (port 8000 - publicly accessible)
echo -n "Backend (port 8000): "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ OK"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "❌ Failed"
fi

echo ""

# Test headless (port 8001 - only accessible locally)
echo -n "Headless (port 8001): "
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ OK"
    curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8001/health
else
    echo "❌ Failed"
fi

echo ""

# Test video (port 8002 - only accessible locally)
echo -n "Video (port 8002): "
if curl -sf http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ OK"
    curl -s http://localhost:8002/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8002/health
else
    echo "❌ Failed"
fi

echo ""
echo "=== Recent Logs (last 20 lines) ==="
echo "Backend logs:"
docker compose -f docker-compose.prod.yml logs --tail=20 backend

echo ""
echo "=== External Access ==="
VM_IP=$(hostname -I | awk '{print $1}')
echo "Backend should be accessible at: http://${VM_IP}:8000/health"
echo "Test from outside: curl http://${VM_IP}:8000/health"
