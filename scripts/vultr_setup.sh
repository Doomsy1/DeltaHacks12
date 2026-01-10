#!/bin/bash

# Vultr VM Setup Script
# Installs Docker and Docker Compose on Ubuntu
# Run this script on a fresh Ubuntu VM

set -e

echo "=== Vultr VM Setup Script ==="
echo "Installing Docker and Docker Compose..."

# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group (optional, for running without sudo)
sudo usermod -aG docker $USER

echo ""
echo "=== Docker installation complete! ==="
echo ""
echo "Next steps:"
echo "1. Clone your repository: git clone <your-repo-url>"
echo "2. cd into the project directory"
echo "3. Create .env file: cp .env.example .env"
echo "4. Edit .env and set your MONGODB_URI (MongoDB Atlas connection string)"
echo "5. Build and start services:"
echo "   docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "Note: You may need to log out and log back in for docker group permissions to take effect."
echo "Or run docker commands with sudo until then."
