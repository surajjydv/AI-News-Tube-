# AI-NewsTube AWS Quick Commands

## 🚀 DEPLOY (First Time)

```powershell
# Windows PowerShell
.\deploy_to_aws.ps1 -Region us-east-1 -InstanceType t3.medium
```

```bash
# Mac/Linux
chmod +x deploy_to_aws.sh
./deploy_to_aws.sh us-east-1 t3.medium
```

---

## 🔗 CONNECT TO YOUR SERVER

```bash
# Get your server's public IP
aws ec2 describe-instances --query 'Reservations[].Instances[].[PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' --output table

# SSH into server (replace YOUR-IP)
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP

# Once connected, check if everything is running
docker ps
docker-compose logs -f ai-newstube
```

---

## 📊 MONITORING & LOGS

```bash
# SSH into server first, then:

# View all running containers
docker ps

# View logs in real-time
docker-compose logs -f

# View logs of specific container
docker-compose logs -f ai-newstube

# View last 50 lines
docker-compose logs --tail=50

# System monitor (if installed)
/home/ubuntu/monitor.sh

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top
```

---

## 🔄 RESTART & STOP

```bash
# SSH into server, then:

# Restart all services
/home/ubuntu/restart.sh
# OR manually:
docker-compose down
docker-compose up -d

# Stop services (keeps data)
docker-compose down

# Start services (data preserved)
docker-compose up -d

# View status
docker-compose ps
```

---

## 💾 BACKUP

```bash
# SSH into server, then:

# Manual backup
/home/ubuntu/backup.sh

# View backup files
ls -lh /home/ubuntu/backups/

# Download backup to your PC
scp -i ai-newstube-key.pem ubuntu@YOUR-IP:/home/ubuntu/backups/* ./backups/
```

---

## 🌐 UPDATE ENVIRONMENT (API KEYS, SETTINGS)

```bash
# SSH into server, then:

# Edit environment file
nano /home/ubuntu/AI-NewsTube/.env

# After changes, restart
docker-compose down
docker-compose up -d
```

---

## 🐳 DOCKER COMMANDS

```bash
# SSH into server, then:

# View container stats
docker stats

# Rebuild image (after code changes)
docker build -t ai-newstube:latest .
docker-compose up -d

# Remove all unused containers/images (free space)
docker system prune -a

# View image details
docker images

# Remove specific image
docker rmi ai-newstube:latest
```

---

## 💰 AWS COST MANAGEMENT

```bash
# Stop instance (pause billing, saves ~$0.02/hour)
aws ec2 stop-instances --instance-ids i-xxxxxxxxxx --region us-east-1

# Start instance (resume)
aws ec2 start-instances --instance-ids i-xxxxxxxxxx --region us-east-1

# Reboot instance (keeps it running)
aws ec2 reboot-instances --instance-ids i-xxxxxxxxxx --region us-east-1

# Get current running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query 'Reservations[].Instances[].[InstanceId,InstanceType,PublicIpAddress,LaunchTime]' --output table

# Terminate instance (DELETE PERMANENTLY)
aws ec2 terminate-instances --instance-ids i-xxxxxxxxxx --region us-east-1
```

---

## 📝 UPDATE CODE

```bash
# SSH into server, then:

# Go to app directory
cd /home/ubuntu/AI-NewsTube

# Get latest code
git pull origin main

# Rebuild if needed
docker build -t ai-newstube:latest .

# Restart services
docker-compose down
docker-compose up -d
```

---

## 🆘 TROUBLESHOOTING

### Container keeps crashing
```bash
docker-compose logs ai-newstube | head -50
```

### Out of disk space
```bash
# Check usage
df -h

# Clean up Docker
docker system prune -a

# Resize volume (in AWS Console)
```

### Can't SSH
```bash
# Check security group allows port 22
aws ec2 describe-security-groups --group-names ai-newstube-sg

# Make sure key file permissions are correct
chmod 400 ai-newstube-key.pem

# Check instance is running
aws ec2 describe-instances --instance-ids i-xxxxxxxxxx
```

### Streaming not working
```bash
# Check Docker is listening on port 8080
docker ps
netstat -tulnp | grep 8080

# Check security group allows port 8080
aws ec2 describe-security-groups --group-names ai-newstube-sg
```

---

## 📍 WHERE TO FIND THINGS

| Item | Location |
|------|----------|
| Application | http://YOUR-IP:8080 |
| Logs | `/home/ubuntu/AI-NewsTube/logs/` |
| Data | `/home/ubuntu/AI-NewsTube/data/` |
| Config | `/home/ubuntu/AI-NewsTube/.env` |
| Docker compose | `/home/ubuntu/AI-NewsTube/docker-compose.yml` |
| SSH Key | `./ai-newstube-key.pem` (on your PC) |

---

## 🎯 TYPICAL WORKFLOW

```bash
# 1. Deploy
.\deploy_to_aws.ps1

# 2. Wait for setup (3-5 min)
# (Check AWS Console for progress)

# 3. Connect
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP

# 4. Check logs
docker-compose logs -f

# 5. Verify running
docker ps

# 6. Access app
# Open browser: http://YOUR-IP:8080

# 7. Monitor
/home/ubuntu/monitor.sh

# 8. When done for the day (save money)
# Disconnect: exit
aws ec2 stop-instances --instance-ids i-xxxxxxxxxx --region us-east-1

# 9. Next day - restart
aws ec2 start-instances --instance-ids i-xxxxxxxxxx --region us-east-1
```

---

## 💡 TIPS

- **Save money**: Stop instance at night (costs ~$0/hour when stopped)
- **Auto-backup**: Script runs daily at 3 AM
- **Monitor real-time**: SSH in and run `/home/ubuntu/monitor.sh`
- **Update code**: `git pull && docker-compose up -d`
- **Check health**: Docker has health checks running automatically
- **Scale up**: If lagging, stop → resize → start with larger instance

---

## 📞 NEED HELP?

1. Check logs: `docker-compose logs ai-newstube`
2. Check AWS Console: https://console.aws.amazon.com
3. Check your IP can SSH: `ssh -i ai-newstube-key.pem ubuntu@YOUR-IP`
4. Check Docker is running: `docker ps`
