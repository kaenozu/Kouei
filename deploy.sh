#!/bin/bash
set -e

echo "🔨 Building frontend..."
cd /home/exedev/Kouei/web-ui
npm run build

echo "📦 Deploying to /var/www/kouei..."
sudo rm -rf /var/www/kouei/*
sudo cp -r dist/* /var/www/kouei/
sudo chown -R www-data:www-data /var/www/kouei

echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo "🌐 Access at: https://tree-router.exe.xyz:8000/"
