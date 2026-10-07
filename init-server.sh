#!/bin/bash
set -e

# AI-NewsTube AWS Server Initialization Script
# This runs automatically on EC2 instance startup

echo "================================"
echo "🔧 AI-NewsTube Server Setup"
echo "================================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
echo "📦 Installing Docker and dependencies..."
sudo apt-get install -y \
    docker.io \
    docker-compose \
    git \
    curl \
    wget \
    ffmpeg \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    htop \
    nano \
    vim

# Start Docker
echo "🐳 Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Clone repository
echo "📥 Cloning AI-NewsTube repository..."
cd /home/ubuntu
git clone https://github.com/yourusername/AI-NewsTube.git
cd AI-NewsTube

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs frames videos assets/audio assets/avatar voice

# Copy environment file
echo "⚙️  Setting up environment..."
if [ ! -f ".env" ]; then
    cp aws.env .env
    echo "⚠️  IMPORTANT: Edit .env file with your API keys!"
fi

# Load environment variables
set -a
source .env
set +a

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt --no-cache-dir

# Build Docker image
echo "🐳 Building Docker image (this may take 10-15 minutes)..."
sudo docker build -t ai-newstube:latest .

# Create docker-compose override for production
echo "📝 Creating production compose file..."
sudo cp docker-compose.prod.yml docker-compose.override.yml

# Start services
echo "🚀 Starting AI-NewsTube services..."
sudo docker-compose up -d

# Wait for container to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check status
echo "✅ Checking service status..."
sudo docker-compose ps

# Print logs
echo ""
echo "📋 Recent logs:"
sudo docker-compose logs --tail=20 ai-newstube

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > /home/ubuntu/monitor.sh << 'MONITOR_EOF'
#!/bin/bash
clear
echo "🖥️  AI-NewsTube System Monitor"
echo "=============================="
echo ""
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "💾 Disk Usage:"
df -h / | tail -1
echo ""
echo "🔥 CPU & Memory:"
free -h
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""
echo "📋 Recent Logs:"
docker-compose logs --tail=10 ai-newstube
echo ""
echo "Press Ctrl+C to exit. Refresh with: watch -n 5 'bash monitor.sh'"
MONITOR_EOF
chmod +x /home/ubuntu/monitor.sh

# Create restart script
echo "🔄 Creating restart script..."
cat > /home/ubuntu/restart.sh << 'RESTART_EOF'
#!/bin/bash
echo "🔄 Restarting AI-NewsTube..."
sudo docker-compose down
sudo docker-compose up -d
echo "✅ Restart complete!"
RESTART_EOF
chmod +x /home/ubuntu/restart.sh

# Create backup script
echo "💾 Creating backup script..."
cat > /home/ubuntu/backup.sh << 'BACKUP_EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "💾 Backing up data to S3..."
tar -czf $BACKUP_DIR/ai-newstube-backup-$TIMESTAMP.tar.gz \
    /home/ubuntu/AI-NewsTube/data \
    /home/ubuntu/AI-NewsTube/logs \
    /home/ubuntu/AI-NewsTube/.env
echo "✅ Local backup created: $BACKUP_DIR/ai-newstube-backup-$TIMESTAMP.tar.gz"

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/ai-newstube-backup-$TIMESTAMP.tar.gz s3://your-bucket/backups/
BACKUP_EOF
chmod +x /home/ubuntu/backup.sh

# Set up cron for daily backups
echo "📅 Setting up automated backups..."
(crontab -l 2>/dev/null; echo "0 3 * * * /home/ubuntu/backup.sh") | crontab -

# Install CloudWatch agent (optional)
echo "📊 Installing CloudWatch agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb

# Print final status
echo ""
echo "✅ ========================================="
echo "✅ AI-NewsTube Server Setup Complete!"
echo "✅ ========================================="
echo ""
echo "🌐 Access your app at: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "📊 Monitoring:"
echo "   - View logs: docker-compose logs -f"
echo "   - Run monitor: /home/ubuntu/monitor.sh"
echo "   - Restart: /home/ubuntu/restart.sh"
echo "   - Backup: /home/ubuntu/backup.sh"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Edit .env with your API keys"
echo "   - Check logs for any errors"
echo "   - Set up HTTPS for production"
echo "   - Monitor disk space and memory"
echo ""
echo "📝 Configuration file: /home/ubuntu/AI-NewsTube/.env"
echo "📋 Docker logs: docker-compose logs -f"
echo ""
