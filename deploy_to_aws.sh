#!/bin/bash

# AWS EC2 Deployment Script for AI-NewsTube Live Streaming
# Usage: ./deploy_to_aws.sh <AWS_REGION> <INSTANCE_TYPE>

set -e

AWS_REGION=${1:-us-east-1}
INSTANCE_TYPE=${2:-t3.medium}
KEY_NAME="ai-newstube-key"
SECURITY_GROUP="ai-newstube-sg"
INSTANCE_NAME="ai-newstube-live-server"

echo "🚀 Deploying AI-NewsTube to AWS EC2..."
echo "Region: $AWS_REGION"
echo "Instance Type: $INSTANCE_TYPE"

# 1. Create Key Pair (if not exists)
echo "📝 Creating SSH key pair..."
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $AWS_REGION 2>/dev/null; then
    aws ec2 create-key-pair --key-name $KEY_NAME --region $AWS_REGION --query 'KeyMaterial' --output text > "$KEY_NAME.pem"
    chmod 400 "$KEY_NAME.pem"
    echo "✅ Key pair created: $KEY_NAME.pem"
else
    echo "✅ Key pair already exists"
fi

# 2. Create Security Group
echo "🔐 Setting up security group..."
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SECURITY_GROUP" --region $AWS_REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    SG_ID=$(aws ec2 create-security-group --group-name $SECURITY_GROUP --description "Security group for AI-NewsTube" --region $AWS_REGION --query 'GroupId' --output text)
    
    # Allow SSH
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $AWS_REGION
    
    # Allow HTTP
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWS_REGION
    
    # Allow HTTPS
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $AWS_REGION
    
    # Allow custom ports for streaming (RTMP, HLS)
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 1935 --cidr 0.0.0.0/0 --region $AWS_REGION
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $AWS_REGION
    
    echo "✅ Security group created: $SG_ID"
else
    echo "✅ Security group already exists: $SG_ID"
fi

# 3. Get latest Ubuntu AMI
echo "🖼️  Finding latest Ubuntu 22.04 AMI..."
AMI_ID=$(aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" --query 'sort_by(Images, &CreationDate)[-1].[ImageId]' --output text --region $AWS_REGION)
echo "✅ AMI ID: $AMI_ID"

# 4. Launch EC2 Instance
echo "🖥️  Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3,DeleteOnTermination=true}" \
    --region $AWS_REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo "⏳ Waiting for instance to be running..."

aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

# Get Public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $AWS_REGION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "✅ Public IP: $PUBLIC_IP"

# 5. Create init script
echo "📝 Creating initialization script..."
cat > /tmp/init-server.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    docker.io \
    docker-compose \
    git \
    curl \
    wget \
    ffmpeg \
    python3-pip

sudo usermod -aG docker ubuntu

echo "📦 Cloning AI-NewsTube repository..."
cd /home/ubuntu
git clone https://github.com/yourusername/AI-NewsTube.git
cd AI-NewsTube

echo "🐳 Building Docker image..."
sudo docker build -t ai-newstube:latest .

echo "🚀 Starting container..."
sudo docker-compose up -d

echo "✅ Deployment complete!"
echo "Application running on: http://$(hostname -I | awk '{print $1}'):8080"
EOF

# 6. Transfer and run init script
echo "📤 Transferring setup script..."
scp -i "$KEY_NAME.pem" -o StrictHostKeyChecking=no /tmp/init-server.sh ubuntu@$PUBLIC_IP:/tmp/
ssh -i "$KEY_NAME.pem" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "chmod +x /tmp/init-server.sh && /tmp/init-server.sh"

echo "✅ Deployment Complete!"
echo ""
echo "📊 Server Details:"
echo "   Instance ID: $INSTANCE_ID"
echo "   Public IP: $PUBLIC_IP"
echo "   SSH Command: ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo "🌐 Access your live stream at: http://$PUBLIC_IP:8080"
echo "💾 Save this information securely!"
