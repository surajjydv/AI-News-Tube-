import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('98.84.135.236', username='ubuntu', key_filename=r'C:\Users\suraj\Downloads\NewsTube.pem', timeout=15)

stdin, stdout, stderr = ssh.exec_command("tail -n 25 /app/AI-NewsTube/logs/autopublisher.log")
print("=== LATEST AUTOPUBLISHER LOGS ===")
print(stdout.read().decode('utf-8'))

stdin, stdout, stderr = ssh.exec_command("cat /app/AI-NewsTube/processed_stories.json")
print("=== PROCESSED STORIES ===")
print(stdout.read().decode('utf-8'))

ssh.close()
