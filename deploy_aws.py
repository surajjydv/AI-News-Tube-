#!/usr/bin/env python3
"""
deploy_aws.py - One-Click AWS EC2 Deploy for AI-NewsTube 24/7 Live Stream
==========================================================================
Automates:
  1. Creates EC2 key pair (saves .pem locally)
  2. Creates security group with SSH access
  3. Launches EC2 Ubuntu instance (t3.medium)
  4. Waits for it to be running
  5. Uploads entire project via SSH/SCP (paramiko)
  6. Installs dependencies on the server
  7. Starts the stream in tmux (survives SSH disconnect)
  8. Stream runs 24/7 on AWS - your laptop can be OFF

Usage:
    python deploy_aws.py

Requirements:
    pip install boto3 paramiko
    AWS credentials: aws configure  OR  set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars
"""

import os
import sys
import time
import tarfile
import subprocess
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

YOUTUBE_STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
CHANNEL_NAME       = os.getenv("CHANNEL_NAME", "NewsTube")

# AWS Config
AWS_REGION     = "ap-south-1"          # Mumbai - closest to India
INSTANCE_TYPE  = "t3.micro"            # Free Tier eligible - 2 vCPU, 1GB RAM
AMI_ID         = "ami-0aa761682283b4cc8"  # Ubuntu 22.04 LTS ap-south-1 (verified latest)
KEY_NAME       = "ai-newstube-key"
SG_NAME        = "ai-newstube-sg"
VOLUME_SIZE_GB = 30
PROJECT_DIR    = Path(__file__).parent.resolve()
KEY_FILE       = PROJECT_DIR / f"{KEY_NAME}.pem"


def banner(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")

def step(msg):
    print(f"\n[->] {msg}")

def ok(msg):
    print(f"[OK] {msg}")


def ensure_deps():
    """Install boto3 and paramiko if not present."""
    for pkg in ["boto3", "paramiko"]:
        try:
            __import__(pkg)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])


def get_or_create_key_pair(ec2_client):
    step(f"Setting up SSH key pair: {KEY_NAME}")
    if KEY_FILE.exists():
        ok(f"Key file already exists: {KEY_FILE}")
        return str(KEY_FILE)
    try:
        ec2_client.describe_key_pairs(KeyNames=[KEY_NAME])
        ec2_client.delete_key_pair(KeyName=KEY_NAME)
    except Exception:
        pass
    response = ec2_client.create_key_pair(KeyName=KEY_NAME, KeyType="rsa")
    KEY_FILE.write_text(response["KeyMaterial"])
    # chmod 400 equivalent on Windows
    import stat
    KEY_FILE.chmod(stat.S_IRUSR)
    ok(f"Key pair saved: {KEY_FILE}")
    return str(KEY_FILE)


def get_or_create_security_group(ec2_client, vpc_id):
    step(f"Setting up security group: {SG_NAME}")
    try:
        resp = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [SG_NAME]}]
        )
        if resp["SecurityGroups"]:
            sg_id = resp["SecurityGroups"][0]["GroupId"]
            ok(f"Security group exists: {sg_id}")
            return sg_id
    except Exception:
        pass
    sg = ec2_client.create_security_group(
        GroupName=SG_NAME,
        Description="AI-NewsTube live stream server",
        VpcId=vpc_id
    )
    sg_id = sg["GroupId"]
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                        "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
    )
    ok(f"Security group created: {sg_id}")
    return sg_id


def launch_or_find_instance(ec2_resource, ec2_client, sg_id, vpc_id):
    step("Looking for existing AI-NewsTube instance...")
    instances = list(ec2_resource.instances.filter(
        Filters=[
            {"Name": "tag:Name", "Values": ["ai-newstube-live-server"]},
            {"Name": "instance-state-name", "Values": ["running", "stopped", "pending"]}
        ]
    ))
    if instances:
        inst = instances[0]
        if inst.state["Name"] == "stopped":
            step("Starting stopped instance...")
            inst.start()
            inst.wait_until_running()
            inst.reload()
        ok(f"Using existing instance: {inst.id} ({inst.public_ip_address})")
        return inst

    step(f"Launching new EC2 {INSTANCE_TYPE} in {AWS_REGION} (Mumbai)...")
    startup = """#!/bin/bash
apt-get update -qq
apt-get install -y -qq ffmpeg python3 python3-pip fonts-noto-core fonts-noto-extra fonts-indic tmux libgl1 libglib2.0-0 espeak-ng
"""
    # Get a valid subnet from default VPC
    subnets = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]},
                 {"Name": "default-for-az", "Values": ["true"]}]
    )
    subnet_id = subnets["Subnets"][0]["SubnetId"]
    ok(f"Using subnet: {subnet_id}")

    instances = ec2_resource.create_instances(
        ImageId=AMI_ID,
        MinCount=1, MaxCount=1,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        NetworkInterfaces=[{
            "AssociatePublicIpAddress": True,
            "DeviceIndex": 0,
            "SubnetId": subnet_id,
            "Groups": [sg_id]
        }],
        BlockDeviceMappings=[{"DeviceName": "/dev/sda1",
                               "Ebs": {"VolumeSize": VOLUME_SIZE_GB, "VolumeType": "gp3"}}],
        TagSpecifications=[{"ResourceType": "instance",
                            "Tags": [{"Key": "Name", "Value": "ai-newstube-live-server"}]}],
        UserData=startup
    )
    inst = instances[0]
    print(f"  Instance launched: {inst.id} — waiting to boot (2-3 min)...")
    inst.wait_until_running()
    inst.reload()
    ok(f"Instance running! IP: {inst.public_ip_address}")
    return inst


def wait_for_ssh(ip, key_path, max_wait=300):
    step(f"Waiting for SSH on {ip}...")
    import paramiko
    start = time.time()
    while time.time() - start < max_wait:
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            pkey = paramiko.RSAKey.from_private_key_file(key_path)
            c.connect(ip, username="ubuntu", pkey=pkey, timeout=10)
            c.close()
            ok("SSH ready!")
            return True
        except Exception:
            print("  SSH not ready, retrying in 10s...")
            time.sleep(10)
    return False


def pack_project():
    step("Packing project (code only, lightweight)...")
    skip_dirs  = {".git", "venv", "__pycache__", "frames", "thumbnails", "uploads", "videos", "voice", "assets", ".agents", ".gemini"}
    skip_exts  = {".pem", ".pyc", ".pyo", ".mp4", ".ts", ".mp3", ".jpg", ".png", ".tar.gz", ".gz", ".zip"}
    tarball = PROJECT_DIR / "deploy_package.tar.gz"
    with tarfile.open(str(tarball), "w:gz") as tar:
        for item in PROJECT_DIR.iterdir():
            if item.name in skip_dirs or item.suffix.lower() in skip_exts:
                continue
            if item.is_dir():
                # Add directory recursively skipping heavy files inside
                for root, dirs, files in os.walk(str(item)):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in skip_exts or fp.name in skip_exts:
                            continue
                        rel = fp.relative_to(PROJECT_DIR)
                        tar.add(str(fp), arcname=f"AI-NewsTube/{rel}")
            else:
                tar.add(str(item), arcname=f"AI-NewsTube/{item.name}")

    size_mb = tarball.stat().st_size / 1024 / 1024
    ok(f"Lightweight package ready: {size_mb:.2f} MB")
    return str(tarball)


def run_ssh(client, cmd, show_output=False):
    _, stdout, stderr = client.exec_command(cmd, timeout=300)
    code = stdout.channel.recv_exit_status()
    out  = stdout.read().decode(errors="replace")
    err  = stderr.read().decode(errors="replace")
    if show_output and out:
        print(out[-500:])
    return code, out, err


def upload_and_start(ip, key_path, tarball_path):
    import paramiko
    step(f"Connecting to {ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.RSAKey.from_private_key_file(key_path)
    client.connect(ip, username="ubuntu", pkey=pkey, timeout=30)

    # Prepare /app
    run_ssh(client, "sudo mkdir -p /app && sudo chown ubuntu:ubuntu /app")

    # Upload
    step("Uploading project (may take 2-3 minutes)...")
    sftp = client.open_sftp()
    last_pct = [0]
    def progress(sent, total):
        pct = int(sent/total*100)
        if pct - last_pct[0] >= 20:
            print(f"  {pct}% uploaded...")
            last_pct[0] = pct
    sftp.put(tarball_path, "/app/deploy_package.tar.gz", callback=progress)
    sftp.close()
    ok("Upload done!")

    # Extract
    step("Extracting...")
    run_ssh(client, "cd /app && tar -xzf deploy_package.tar.gz && rm deploy_package.tar.gz")
    ok("Extracted!")

    # Write .env
    step("Writing .env with your API keys...")
    env_content = (
        f"CHANNEL_NAME={CHANNEL_NAME}\\n"
        f"GROQ_API_KEY={GROQ_API_KEY}\\n"
        f"YOUTUBE_STREAM_KEY={YOUTUBE_STREAM_KEY}\\n"
        f"DEFAULT_TTS_VOICE=hi-IN-SwaraNeural\\n"
        f"GROQ_ORPHEUS_ENABLED=false\\n"
    )
    run_ssh(client, f"printf '{env_content}' > /app/AI-NewsTube/.env")
    ok(".env written!")

    # Install deps
    step("Installing Python deps (3-5 min first time)...")
    run_ssh(client, "pip3 install --quiet -r /app/AI-NewsTube/requirements.txt 2>&1", show_output=True)
    ok("Deps installed!")

    # Create dirs
    run_ssh(client, "mkdir -p /app/AI-NewsTube/logs /app/AI-NewsTube/videos /app/AI-NewsTube/voice /app/AI-NewsTube/assets")

    # Kill old stream
    run_ssh(client, "pkill -f continuous_live_stream 2>/dev/null; tmux kill-session -t livestream 2>/dev/null; sleep 2")

    # Launch in tmux
    step("Starting 24/7 live stream in tmux...")
    start_cmd = (
        "tmux new-session -d -s livestream "
        "'cd /app/AI-NewsTube && python3 scripts/continuous_live_stream.py "
        "> /app/AI-NewsTube/logs/stream.log 2>&1'"
    )
    run_ssh(client, start_cmd)
    time.sleep(5)

    _, tmux_out, _ = run_ssh(client, "tmux list-sessions 2>&1")
    time.sleep(8)
    _, log_out, _  = run_ssh(client, "tail -30 /app/AI-NewsTube/logs/stream.log 2>/dev/null || echo 'Starting...'")

    client.close()
    return tmux_out, log_out


def main():
    banner("AI-NewsTube AWS Deploy - One-Click 24/7 Live Stream")

    if not GROQ_API_KEY or "your_groq" in GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in .env!")
        sys.exit(1)
    if not YOUTUBE_STREAM_KEY:
        print("ERROR: YOUTUBE_STREAM_KEY not set in .env!")
        sys.exit(1)

    ensure_deps()
    import boto3

    step("Checking AWS credentials...")
    try:
        session = boto3.Session(region_name=AWS_REGION)
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        ok(f"AWS Account: {identity['Account']}")
    except Exception as e:
        print(f"\nERROR: AWS credentials not configured!")
        print(f"  {e}")
        print(f"\nPlease run one of:")
        print(f"  1) aws configure   (if AWS CLI installed)")
        print(f"  2) set AWS_ACCESS_KEY_ID=xxxx && set AWS_SECRET_ACCESS_KEY=xxxx")
        print(f"\nGet keys from: https://console.aws.amazon.com/iam/")
        sys.exit(1)

    ec2_resource = session.resource("ec2", region_name=AWS_REGION)
    ec2_client   = session.client("ec2",   region_name=AWS_REGION)

    step("Getting default VPC...")
    vpcs   = ec2_client.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    vpc_id = vpcs["Vpcs"][0]["VpcId"]
    ok(f"VPC: {vpc_id}")

    key_path = get_or_create_key_pair(ec2_client)
    sg_id    = get_or_create_security_group(ec2_client, vpc_id)
    instance = launch_or_find_instance(ec2_resource, ec2_client, sg_id, vpc_id)
    ip       = instance.public_ip_address

    if not wait_for_ssh(ip, key_path):
        print("ERROR: SSH timeout. Run the script again in a few minutes.")
        sys.exit(1)

    tarball = pack_project()
    tmux_out, log_out = upload_and_start(ip, key_path, tarball)
    Path(tarball).unlink(missing_ok=True)

    banner("DEPLOYMENT COMPLETE!")
    print(f"""
  Instance ID:   {instance.id}
  Public IP:     {ip}
  Region:        {AWS_REGION} (Mumbai)
  Stream:        Running in tmux 'livestream'
  YouTube Key:   {YOUTUBE_STREAM_KEY[:8]}...

  tmux sessions:
  {tmux_out.strip()}

  Stream log:
  {log_out.strip()[:600]}

  ─────────────────────────────────────────
  SSH to your server:
    ssh -i {KEY_FILE.name} ubuntu@{ip}

  Watch live logs:
    ssh -i {KEY_FILE.name} ubuntu@{ip} 'tail -f /app/AI-NewsTube/logs/stream.log'

  Attach to stream session:
    ssh -i {KEY_FILE.name} ubuntu@{ip} 'tmux attach -t livestream'

  Your stream is NOW LIVE 24/7! Laptop band karo - stream chalti rahegi!
  ─────────────────────────────────────────
""")


if __name__ == "__main__":
    main()
