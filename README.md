 # MongoDB Replication Orchestrator

A FastAPI-based web tool to automatically install and configure a 3-node MongoDB replica set on Rocky Linux 9 (GCP friendly), with:

- Primary (read/write), Secondary (read-only), Analytics (hidden, reporting)
- Web UI to submit node credentials and watch logs
- WebSocket SSH terminal per node
- Dummy data generator (millions of docs) + optional file uploads to GridFS
- Simple benchmarking (IOPS-ish) and lag monitoring

## Quick start

1) Create three Rocky Linux 9 VMs in GCP and ensure:
- Ports open: 22 (SSH), 27017 between nodes, and your web port (default 8000) from your IP
- SSH user and password or SSH key available

2) Run the app locally in this devcontainer

```
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000

3) Fill the JSON spec with your VM IPs and credentials; click Install & Configure.

4) Seed data and run Benchmark/Health.

## Notes
- The installer uses MongoDB 7.0 packages for RHEL9-compatible distros (Rocky 9).
- Security is enabled (authorization, keyFile). Root and app users are created.
- Analytics node is hidden with low priority to avoid elections.
- For large data loads, consider running from a VM near your cluster to reduce latency.

## Disclaimer
This tool is for demo/testing and not a replacement for production-grade automation. Review and harden before production (firewalls, TLS, backups, monitoring).
