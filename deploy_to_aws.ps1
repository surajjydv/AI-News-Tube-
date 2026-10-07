# AWS EC2 Deployment Script for AI-NewsTube (Windows PowerShell)
# Usage: .\deploy_to_aws.ps1 -Region us-east-1 -InstanceType t3.medium

param(
    [string]$Region = "us-east-1",
    [string]$InstanceType = "t3.medium",
    [string]$KeyName = "ai-newstube-key",
    [string]$SecurityGroup = "ai-newstube-sg",
    [string]$InstanceName = "ai-newstube-live-server"
)

Write-Host "🚀 Deploying AI-NewsTube to AWS EC2..." -ForegroundColor Green
Write-Host "Region: $Region"
Write-Host "Instance Type: $InstanceType"

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Host "❌ AWS CLI not found. Install it from: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check if AWS credentials are configured
try {
    aws sts get-caller-identity --region $Region | Out-Null
} catch {
    Write-Host "❌ AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}

# Step 1: Create Key Pair
Write-Host "`n📝 Creating SSH key pair..." -ForegroundColor Cyan
try {
    $keyExists = aws ec2 describe-key-pairs --key-names $KeyName --region $Region --query 'KeyPairs' --output text 2>$null
    if ($LASTEXITCODE -ne 0) {
        $keyPair = aws ec2 create-key-pair --key-name $KeyName --region $Region
        $keyPair | Select-Object -ExpandProperty KeyMaterial | Out-File -FilePath "$KeyName.pem" -Encoding UTF8
        Write-Host "✅ Key pair created: $KeyName.pem" -ForegroundColor Green
    } else {
        Write-Host "✅ Key pair already exists" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error creating key pair: $_" -ForegroundColor Red
}

# Step 2: Create Security Group
Write-Host "`n🔐 Setting up security group..." -ForegroundColor Cyan
try {
    $sg = aws ec2 describe-security-groups --filters "Name=group-name,Values=$SecurityGroup" --region $Region --query 'SecurityGroups[0].GroupId' --output text 2>$null
    
    if ($sg -eq "None" -or [string]::IsNullOrEmpty($sg)) {
        $sgResponse = aws ec2 create-security-group --group-name $SecurityGroup --description "Security group for AI-NewsTube" --region $Region
        $sgId = $sgResponse | ConvertFrom-Json | Select-Object -ExpandProperty GroupId
        
        Write-Host "✅ Security group created: $sgId" -ForegroundColor Green
        
        # Allow SSH
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $Region
        
        # Allow HTTP
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region
        
        # Allow HTTPS
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $Region
        
        # Allow streaming ports
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 1935 --cidr 0.0.0.0/0 --region $Region
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $Region
        
        Write-Host "✅ Firewall rules added" -ForegroundColor Green
    } else {
        Write-Host "✅ Security group already exists: $sg" -ForegroundColor Green
        $sgId = $sg
    }
} catch {
    Write-Host "❌ Error with security group: $_" -ForegroundColor Red
}

# Step 3: Get Latest Ubuntu AMI
Write-Host "`n🖼️  Finding latest Ubuntu 22.04 AMI..." -ForegroundColor Cyan
try {
    $amiJson = aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" --query 'sort_by(Images, &CreationDate)[-1].[ImageId]' --output json --region $Region
    $amiId = ($amiJson | ConvertFrom-Json)[0]
    Write-Host "✅ AMI ID: $amiId" -ForegroundColor Green
} catch {
    Write-Host "❌ Error finding AMI: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Launch EC2 Instance
Write-Host "`n🖥️  Launching EC2 instance..." -ForegroundColor Cyan
try {
    $instanceJson = aws ec2 run-instances `
        --image-id $amiId `
        --instance-type $InstanceType `
        --key-name $KeyName `
        --security-group-ids $sgId `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$InstanceName}]" `
        --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3,DeleteOnTermination=true}" `
        --region $Region `
        --output json
    
    $instanceId = ($instanceJson | ConvertFrom-Json).Instances[0].InstanceId
    Write-Host "✅ Instance launched: $instanceId" -ForegroundColor Green
    
    Write-Host "⏳ Waiting for instance to be running (this may take 1-2 minutes)..." -ForegroundColor Yellow
    aws ec2 wait instance-running --instance-ids $instanceId --region $Region
    
    # Get Public IP
    $ipJson = aws ec2 describe-instances --instance-ids $instanceId --region $Region --query 'Reservations[0].Instances[0].PublicIpAddress' --output json
    $publicIp = $ipJson | ConvertFrom-Json
    Write-Host "✅ Instance running at: $publicIp" -ForegroundColor Green
    
    # Save connection info
    $connInfo = @"
📋 AI-NewsTube AWS Deployment Info
===================================
Date: $(Get-Date)
Instance ID: $instanceId
Public IP: $publicIp
Region: $Region
Instance Type: $InstanceType
Key File: $KeyName.pem

🔗 Connection Command:
ssh -i $KeyName.pem ubuntu@$publicIp

🌐 Access Application At:
http://$publicIp:8080

⚠️  IMPORTANT SECURITY NOTES:
- Keep $KeyName.pem safe! Don't share it
- Restrict SSH to your IP for security
- Change default passwords
- Set up HTTPS for production

📝 Next Steps:
1. Wait 2-3 minutes for Docker to install
2. SSH into the server
3. Monitor: docker-compose logs -f
4. Access: http://$publicIp:8080

💾 Backup this file!
"@
    
    $connInfo | Out-File -FilePath "aws-connection-info.txt" -Encoding UTF8
    Write-Host "`n$connInfo" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error launching instance: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Deployment initiated! Waiting for setup to complete..." -ForegroundColor Green
Write-Host "This may take 3-5 minutes. Check the AWS Console for real-time status." -ForegroundColor Yellow
