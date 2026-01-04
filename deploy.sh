#!/bin/bash

# Kouei Deployment Script

echo "🚀 Deploying Kouei AI Kyotei System..."

# 1. Stop existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop kouei-api 2>/dev/null || true
sudo systemctl stop kouei-web 2>/dev/null || true

# 2. Install systemd services
echo "🔧 Installing systemd services..."
sudo cp kouei-api.service /etc/systemd/system/
sudo cp kouei-web.service /etc/systemd/system/

# 3. Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# 4. Enable services
echo "✅ Enabling services..."
sudo systemctl enable kouei-api
sudo systemctl enable kouei-web

# 5. Start services
echo "🚀 Starting services..."
sudo systemctl start kouei-api
sudo systemctl start kouei-web

# 6. Check status
echo "📋 Service status:"
sudo systemctl status kouei-api --no-pager -l
sudo systemctl status kouei-web --no-pager -l

echo "🎉 Deployment complete!"
echo "API: http://localhost:8001"
echo "Web UI: http://localhost:8080"
