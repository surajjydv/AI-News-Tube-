# ✅ AI-NewsTube AWS Deployment Checklist

## Pre-Deployment (Do These First)

### 1. Get AWS Account Ready
- [ ] Have AWS account (free tier available)
- [ ] Have AWS Access Key ID
- [ ] Have AWS Secret Access Key
- [ ] Know your preferred region (default: us-east-1)

### 2. Get Groq API Key
- [ ] Go to https://console.groq.com
- [ ] Create account/login
- [ ] Generate API key
- [ ] Copy the key (you'll need it in Step 4)

### 3. Install AWS CLI (if not already installed)
```powershell
# Check if installed
aws --version

# If not, download from:
# https://aws.amazon.com/cli/
```

### 4. Configure AWS Credentials
```powershell
# Run this command
aws configure

# When prompted, enter:
# - Access Key ID
# - Secret Access Key
# - Default region: us-east-1
# - Default format: json
```

### 5. Edit Configuration File
```powershell
# Open aws.env in editor
notepad .\aws.env

# MUST CHANGE THIS LINE:
# GROQ_API_KEY=your_groq_api_key_here
# TO:
# GROQ_API_KEY=gsk_1234567890abcdef... (your actual key)

# OPTIONAL: Change other settings
# - AWS_REGION (default: us-east-1)
# - AWS_INSTANCE_TYPE (default: t3.medium)
# - STREAM_QUALITY (default: 1080p)

# Save and close
```

---

## Deployment (Run These)

### 6. Deploy to AWS
```powershell
# Navigate to project folder
cd "C:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube"

# Run deployment script
.\deploy_to_aws.ps1

# OR with custom settings:
.\deploy_to_aws.ps1 -Region us-west-2 -InstanceType t3.large
```

### 7. Wait for Deployment
- ⏳ EC2 instance creation: ~1-2 minutes
- ⏳ Docker installation: ~2-3 minutes
- ⏳ App build & startup: ~5-10 minutes
- **Total: ~10-15 minutes**

### 8. Save Connection Info
After deployment completes, you'll receive:
```
✅ Instance ID: i-0123456789abcdef0
✅ Public IP: 54.123.45.67
✅ SSH Command: ssh -i ai-newstube-key.pem ubuntu@54.123.45.67
✅ Access URL: http://54.123.45.67:8080
```
- [ ] Copy and save this information safely
- [ ] File will be saved to: `aws-connection-info.txt`

---

## Post-Deployment (Verify Everything Works)

### 9. SSH Into Server & Verify
```bash
# SSH into your server (replace IP)
ssh -i ai-newstube-key.pem ubuntu@54.123.45.67

# Once connected, run:
docker ps                    # Should see 1-2 containers
docker-compose logs -f       # Should see app logs
exit                        # Disconnect when done
```

### 10. Test in Browser
```
Open: http://54.123.45.67:8080

Expected: AI-NewsTube application loads
```

### 11. Monitor Server
```bash
# SSH back in
ssh -i ai-newstube-key.pem ubuntu@54.123.45.67

# Run monitoring
/home/ubuntu/monitor.sh

# Should show:
# - Container status: running
# - CPU/Memory usage: reasonable
# - No error messages
```

---

## First Run Issues? Debug Here

### App won't start?
```bash
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP
docker-compose logs ai-newstube | head -50
# Look for error messages
```

### Can't access the app?
```bash
# Check security group allows port 8080
aws ec2 describe-security-groups --group-names ai-newstube-sg

# Check if container is running
docker ps
```

### Out of disk space?
```bash
# Check usage
df -h

# Clean up Docker
docker system prune -a

# Or resize volume in AWS Console
```

### API keys not working?
```bash
# SSH in
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP

# Edit environment
nano /home/ubuntu/AI-NewsTube/.env

# Update GROQ_API_KEY line

# Restart
docker-compose restart
```

---

## Ongoing Management

### Daily Usage
- [ ] Check app is running: visit http://YOUR-IP:8080
- [ ] Monitor logs: `docker-compose logs -f`
- [ ] Check disk space: `df -h`

### Weekly Tasks
- [ ] Review CloudWatch logs
- [ ] Check AWS billing
- [ ] Verify backups are happening

### When Not Using
```bash
# Stop instance to save money (~50% cost reduction)
aws ec2 stop-instances --instance-ids i-xxxxx --region us-east-1
```

### When Needed Again
```bash
# Start instance
aws ec2 start-instances --instance-ids i-xxxxx --region us-east-1

# SSH in and restart
docker-compose up -d
```

---

## Quick Reference Commands

```bash
# View your instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# SSH into server
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Start services
docker-compose up -d

# Backup data
/home/ubuntu/backup.sh

# Update code
git pull origin main
docker-compose up -d

# Monitor system
/home/ubuntu/monitor.sh

# Stop instance (save money)
aws ec2 stop-instances --instance-ids i-xxxxx --region us-east-1

# Terminate instance (DELETE - permanent)
aws ec2 terminate-instances --instance-ids i-xxxxx --region us-east-1
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `START_HERE.md` | Quick overview |
| `AWS_DEPLOYMENT_GUIDE.md` | Full documentation |
| `AWS_QUICK_COMMANDS.md` | Copy-paste commands |
| `deploy_to_aws.ps1` | Deployment script (Windows) |
| `deploy_to_aws.sh` | Deployment script (Mac/Linux) |
| `aws.env` | Configuration file |
| `docker-compose.prod.yml` | Production setup |
| `init-server.sh` | Server initialization |
| `aws-connection-info.txt` | Generated after deployment |

---

## ✅ Done!

Once you've completed all steps:
- ✅ App is running on AWS EC2
- ✅ Accessible 24/7 at http://YOUR-IP:8080
- ✅ Your laptop is completely free
- ✅ Daily backups configured
- ✅ Monitoring setup
- ✅ Cost-effective (~$30-50/month)

**Enjoy your live streaming! 🎬**

---

## Need Help?

1. **Stuck on setup?** → Read `AWS_DEPLOYMENT_GUIDE.md`
2. **Can't remember commands?** → Check `AWS_QUICK_COMMANDS.md`
3. **Want to understand AWS?** → AWS docs are excellent
4. **Having issues?** → Check logs: `docker-compose logs -f`

---

Last updated: 2024-01-15
Status: Ready to Deploy ✅
