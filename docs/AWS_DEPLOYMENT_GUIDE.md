# 🚀 AI-NewsTube AWS Deployment Guide

## Quick Start (5 minutes)

### Step 1: Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
```

### Step 2: Update Configuration
Edit `aws.env` and replace:
- `GROQ_API_KEY=your_groq_api_key_here` - Get from [Groq Console](https://console.groq.com)
- `your-aws-account-id` - Your AWS Account ID (12-digit number)

### Step 3: Deploy to AWS
```bash
# Make script executable (Windows: skip this)
chmod +x deploy_to_aws.sh

# Run deployment (default: us-east-1, t3.medium)
./deploy_to_aws.sh

# Or specify custom region and instance type
./deploy_to_aws.sh us-west-2 t3.large
```

### Step 4: Access Your Live Stream
After deployment completes, you'll see:
```
🌐 Access your live stream at: http://YOUR-PUBLIC-IP:8080
💾 SSH into server: ssh -i ai-newstube-key.pem ubuntu@YOUR-PUBLIC-IP
```

---

## What Gets Deployed

✅ **EC2 Instance** (t3.medium = $0.03/hour ≈ $22/month)
✅ **Docker Container** - Your entire app
✅ **Auto-Backup to S3** - Daily backups (optional storage cost)
✅ **Security Group** - Firewall rules for streaming
✅ **CloudWatch Logs** - Monitor your app

---

## Instance Types & Costs

| Type | vCPU | RAM | Monthly Cost | Best For |
|------|------|-----|--------------|----------|
| t3.micro | 1 | 1GB | ~$7 | Testing only |
| t3.small | 2 | 2GB | ~$15 | Light streaming |
| **t3.medium** | 2 | 4GB | ~$30 | 1080p streaming |
| t3.large | 2 | 8GB | ~$61 | 4K/Multiple streams |

---

## Managing Your Server

### Check Server Status
```bash
aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Name,Values=ai-newstube-live-server"
```

### Connect via SSH
```bash
ssh -i ai-newstube-key.pem ubuntu@YOUR-PUBLIC-IP
cd AI-NewsTube
docker ps  # See running containers
docker logs -f ai-newstube-live  # View logs
```

### Start/Stop Server (Save Money!)
```bash
# Stop instance (pause billing)
aws ec2 stop-instances --instance-ids i-xxxxxxxxxx --region us-east-1

# Start instance (resume)
aws ec2 start-instances --instance-ids i-xxxxxxxxxx --region us-east-1

# Terminate (delete permanently)
aws ec2 terminate-instances --instance-ids i-xxxxxxxxxx --region us-east-1
```

---

## Environment Variables

Edit `aws.env` before deployment:

```env
# Essential
GROQ_API_KEY=your_key_here
AWS_REGION=us-east-1

# Streaming Quality (higher = more CPU/bandwidth)
STREAM_QUALITY=1080p      # 720p, 1080p, 2K, 4K
STREAM_BITRATE=5000k      # kbps
STREAM_FPS=30             # 24, 30, 60

# Scale settings
AWS_INSTANCE_TYPE=t3.medium
MIN_INSTANCES=1
MAX_INSTANCES=5
```

---

## Monitoring & Logs

### CloudWatch Logs
```bash
# View logs in real-time
aws logs tail /aws/ecs/ai-newstube --follow

# View last 1000 log lines
aws logs tail /aws/ecs/ai-newstube --max-items 1000
```

### SSH into Server & Check Status
```bash
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP
docker-compose logs -f
top  # View CPU/Memory usage
df -h  # View disk space
```

---

## Uploading Your Assets to S3

### First Time Setup
```bash
# Create S3 bucket
aws s3 mb s3://ai-newstube-assets-$(date +%s) --region us-east-1

# Upload assets
aws s3 sync ./assets s3://ai-newstube-assets-TIMESTAMP/assets
aws s3 sync ./models s3://ai-newstube-assets-TIMESTAMP/models
```

### Update docker-compose to use S3 assets
```yaml
volumes:
  - s3://ai-newstube-assets-TIMESTAMP/assets:/app/assets
```

---

## Cost Breakdown (Monthly Estimate)

| Component | Cost |
|-----------|------|
| EC2 t3.medium | $22 |
| Data transfer (egress) | $5-15 |
| S3 storage (if used) | $5-10 |
| CloudWatch logs | $2-5 |
| **Total** | **$34-52/month** |

💡 **Free Tier**: If this is your first year with AWS, you get 750 hours/month of t2.micro free!

---

## Troubleshooting

### Instance won't start
```bash
# Check security group rules
aws ec2 describe-security-groups --group-names ai-newstube-sg

# Check instance status
aws ec2 describe-instance-status --instance-ids i-xxxxxx
```

### Can't SSH into server
```bash
# Make sure key has right permissions
chmod 400 ai-newstube-key.pem

# Check security group allows SSH (port 22)
aws ec2 describe-security-groups --filters "Name=group-name,Values=ai-newstube-sg"
```

### Docker not running
```bash
ssh -i ai-newstube-key.pem ubuntu@YOUR-IP
sudo systemctl status docker
sudo systemctl restart docker
docker-compose up -d
```

### Out of disk space
```bash
# Check disk usage
df -h

# Resize volume (AWS Console or CLI)
aws ec2 modify-volume --volume-id vol-xxxxx --size 150
```

---

## Next Steps

1. ✅ Configure `aws.env`
2. ✅ Run `./deploy_to_aws.sh`
3. ✅ Access at `http://YOUR-IP:8080`
4. ✅ Set up DNS (optional)
5. ✅ Enable HTTPS with Let's Encrypt

---

## Questions?

- AWS Docs: https://docs.aws.amazon.com/
- EC2 Pricing: https://aws.amazon.com/ec2/pricing/on-demand/
- Docker Docs: https://docs.docker.com/
