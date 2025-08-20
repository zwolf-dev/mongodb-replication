#!/bin/bash

# MongoDB Replication Tool Demo Service
# SystemD service file untuk production deployment

cat > /etc/systemd/system/mongodb-replication-tool.service << 'EOF'
[Unit]
Description=MongoDB Replication Tool Web Service
After=network.target

[Service]
Type=simple
User=mongodb-tool
Group=mongodb-tool
WorkingDirectory=/opt/mongodb-replication-tool
Environment=PATH=/opt/mongodb-replication-tool/.venv/bin
ExecStart=/opt/mongodb-replication-tool/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mongodb-replication-tool

[Install]
WantedBy=multi-user.target
EOF

# Create dedicated user
useradd -r -s /bin/false mongodb-tool
mkdir -p /opt/mongodb-replication-tool
chown mongodb-tool:mongodb-tool /opt/mongodb-replication-tool

# Enable and start service
systemctl daemon-reload
systemctl enable mongodb-replication-tool
# systemctl start mongodb-replication-tool

echo "SystemD service file created: /etc/systemd/system/mongodb-replication-tool.service"
echo "To deploy:"
echo "1. Copy application files to /opt/mongodb-replication-tool/"
echo "2. Install dependencies in .venv"
echo "3. systemctl start mongodb-replication-tool"
