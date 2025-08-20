# MongoDB Replication Tool - Panduan Lengkap

## Tool Web untuk Auto Install MongoDB Replication 3 Node

Tool ini menyediakan interface web untuk otomatisasi instalasi cluster MongoDB replica set 3 node dengan konfigurasi optimal untuk environment production.

## Fitur Utama

✅ **3-Node Configuration**: Primary (read/write) + Secondary (read-only) + Analytics (reporting)  
✅ **Web Interface**: Panel kontrol lengkap dengan real-time monitoring  
✅ **SSH Terminal Browser**: Akses terminal langsung dari web  
✅ **Live Logs**: Streaming log instalasi real-time via WebSocket  
✅ **Dummy Data Generator**: Insert jutaan data dengan file support  
✅ **IOPS Benchmarking**: Testing performa database otomatis  
✅ **Lag Monitoring**: Monitor replikasi tanpa delay  
✅ **Security Ready**: KeyFile authentication + user management  
✅ **Rocky Linux 9 Support**: Optimized untuk RHEL-based systems  
✅ **GCP Integration**: Script otomatis untuk provisioning VMs  

## Quick Start

### 1. Setup Environment

```bash
# Clone dan masuk ke directory
cd /workspaces/mongodb-replication

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Web Server

```bash
# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Akses web interface di: **http://localhost:8000**

### 3. Setup GCP Demo (Opsional)

```bash
# Jalankan script untuk create 3 VMs di GCP
chmod +x setup-gcp-demo.sh
./setup-gcp-demo.sh
```

Script ini akan:
- Create 3 VMs Rocky Linux 9 di GCP
- Setup firewall rules untuk MongoDB
- Generate SSH keys
- Output cluster specification siap pakai

## Cara Penggunaan

### 1. Konfigurasi Cluster

Di web interface, isi spesifikasi cluster:

```json
{
  "primary": {
    "host": "PRIMARY_IP",
    "port": 22,
    "username": "root",
    "password": "your_password"
  },
  "secondary": {
    "host": "SECONDARY_IP", 
    "port": 22,
    "username": "root",
    "password": "your_password"
  },
  "analytics": {
    "host": "ANALYTICS_IP",
    "port": 22,
    "username": "root", 
    "password": "your_password"
  },
  "mongo_port": 27017,
  "replica_set_name": "myReplicaSet"
}
```

### 2. Instalasi Otomatis

1. **Test Connection**: Klik tombol untuk validasi koneksi SSH
2. **Install MongoDB**: Klik tombol instalasi dan monitor progress
3. **Initialize Replica Set**: Otomatis setelah instalasi selesai
4. **Create Admin User**: User admin akan dibuat otomatis

### 3. Features Testing

- **SSH Terminal**: Akses langsung ke node dari browser
- **Insert Data**: Generate jutaan dummy records dengan file
- **Benchmark IOPS**: Test performa read/write operations  
- **Monitor Lag**: Real-time replication status

## Arsitektur Cluster

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PRIMARY       │    │   SECONDARY     │    │   ANALYTICS     │
│  (Read/Write)   │◄──►│  (Read Only)    │◄──►│  (Reporting)    │
│  Priority: 2    │    │  Priority: 1    │    │  Priority: 0    │
│  Votes: 1       │    │  Votes: 1       │    │  Votes: 1       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Node Configuration:
- **Primary**: Master node untuk write operations
- **Secondary**: Replica untuk read operations dan failover
- **Analytics**: Dedicated node untuk reporting queries

## Monitoring & Management

### Real-time Features:
- Live installation logs via WebSocket
- SSH terminal emulation in browser
- Connection status indicators
- Progress tracking dengan visual feedback

### Performance Testing:
- IOPS benchmarking dengan configurasi custom
- Bulk insert testing (jutaan records)
- Replication lag monitoring
- File upload dan processing

## Security Features

- KeyFile authentication untuk inter-node communication
- Admin user creation dengan random password
- SSH connection validation
- Error handling dan timeout management

## Troubleshooting

### Common Issues:

1. **SSH Connection Failed**
   - Pastikan port 22 terbuka
   - Verify username/password
   - Check firewall settings

2. **MongoDB Install Error**
   - Ensure Rocky Linux 9 compatibility
   - Check internet connection untuk DNF repos
   - Verify root/sudo access

3. **Replica Set Init Failed**
   - Confirm MongoDB port (27017) accessibility
   - Check keyFile permissions
   - Verify network connectivity between nodes

## Technical Stack

- **Backend**: FastAPI + Uvicorn ASGI
- **MongoDB**: Version 7.0 via official DNF repos  
- **SSH**: Paramiko library untuk automation
- **Frontend**: HTML5 + JavaScript + WebSocket
- **Database Client**: PyMongo dengan replica set support
- **Target OS**: Rocky Linux 9.x

## Production Ready Features

- Comprehensive error handling
- Connection timeouts dan retries
- WebSocket connection management
- Background process monitoring
- Security best practices
- Scalable architecture

---

**Tool ini siap untuk deployment production dan testing environment MongoDB replica set.**

Untuk support dan customization lebih lanjut, silakan modifikasi sesuai kebutuhan specific environment Anda.
