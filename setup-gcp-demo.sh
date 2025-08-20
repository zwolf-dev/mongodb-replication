#!/bin/bash

# MongoDB Replication Orchestrator Demo
# This script shows how to create GCP VMs and use the tool

echo "🚀 MongoDB Replication Orchestrator Demo"
echo "========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
ZONE="us-central1-a"
MACHINE_TYPE="e2-medium"
IMAGE_FAMILY="rocky-linux-9"
IMAGE_PROJECT="rocky-linux-cloud"
NETWORK="default"
SUBNET="default"

echo "📋 Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Zone: $ZONE"
echo "  Machine: $MACHINE_TYPE"
echo "  OS: Rocky Linux 9"
echo ""

# Create VMs
echo "🖥️  Creating 3 VMs for MongoDB cluster..."

# Primary node
echo "Creating primary node..."
gcloud compute instances create mongo-primary \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=$SUBNET \
    --metadata=enable-oslogin=true \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=mongo-cluster \
    --create-disk=auto-delete=yes,boot=yes,device-name=mongo-primary,image=projects/$IMAGE_PROJECT/global/images/family/$IMAGE_FAMILY,mode=rw,size=20,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=role=mongo-primary \
    --reservation-affinity=any

# Secondary node
echo "Creating secondary node..."
gcloud compute instances create mongo-secondary \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=$SUBNET \
    --metadata=enable-oslogin=true \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=mongo-cluster \
    --create-disk=auto-delete=yes,boot=yes,device-name=mongo-secondary,image=projects/$IMAGE_PROJECT/global/images/family/$IMAGE_FAMILY,mode=rw,size=20,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=role=mongo-secondary \
    --reservation-affinity=any

# Analytics node
echo "Creating analytics node..."
gcloud compute instances create mongo-analytics \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=$SUBNET \
    --metadata=enable-oslogin=true \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=mongo-cluster \
    --create-disk=auto-delete=yes,boot=yes,device-name=mongo-analytics,image=projects/$IMAGE_PROJECT/global/images/family/$IMAGE_FAMILY,mode=rw,size=20,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=role=mongo-analytics \
    --reservation-affinity=any

echo "✅ VMs created successfully!"

# Create firewall rules
echo "🔥 Creating firewall rules..."

# SSH access
gcloud compute firewall-rules create mongo-ssh \
    --project=$PROJECT_ID \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=mongo-cluster \
    --description="SSH access to MongoDB cluster"

# MongoDB internal communication
gcloud compute firewall-rules create mongo-internal \
    --project=$PROJECT_ID \
    --allow=tcp:27017 \
    --source-tags=mongo-cluster \
    --target-tags=mongo-cluster \
    --description="MongoDB internal communication"

echo "✅ Firewall rules created!"

# Get IP addresses
echo "📍 Getting IP addresses..."
PRIMARY_IP=$(gcloud compute instances describe mongo-primary --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
SECONDARY_IP=$(gcloud compute instances describe mongo-secondary --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
ANALYTICS_IP=$(gcloud compute instances describe mongo-analytics --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "  Primary:   $PRIMARY_IP"
echo "  Secondary: $SECONDARY_IP"
echo "  Analytics: $ANALYTICS_IP"

# Generate cluster specification
echo "📝 Generating cluster specification..."
cat > cluster-spec.json << EOF
{
  "replset": "rs0",
  "creds": {
    "root_user": "rootadmin",
    "root_pass": "MongoRoot$(openssl rand -base64 8)!",
    "app_user": "appuser",
    "app_pass": "MongoApp$(openssl rand -base64 8)!"
  },
  "db_name": "appdb",
  "coll_name": "events",
  "nodes": {
    "primary": {
      "host": "$PRIMARY_IP",
      "username": "rocky",
      "password": "MongoDB123!",
      "mongo_port": 27017,
      "role": "primary"
    },
    "secondary": {
      "host": "$SECONDARY_IP",
      "username": "rocky", 
      "password": "MongoDB123!",
      "mongo_port": 27017,
      "role": "secondary"
    },
    "analytics": {
      "host": "$ANALYTICS_IP",
      "username": "rocky",
      "password": "MongoDB123!",
      "mongo_port": 27017,
      "role": "analytics"
    }
  }
}
EOF

# Set passwords on VMs
echo "🔐 Setting up user passwords on VMs..."
for vm in mongo-primary mongo-secondary mongo-analytics; do
    echo "Setting password for $vm..."
    gcloud compute ssh $vm --zone=$ZONE --command="echo 'rocky:MongoDB123!' | sudo chpasswd" --ssh-flag="-o StrictHostKeyChecking=no"
done

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy the content of cluster-spec.json into the web UI"
echo "2. Open http://localhost:8000 in your browser" 
echo "3. Click 'Test SSH Connections' to verify connectivity"
echo "4. Click 'Install & Configure' to set up MongoDB"
echo "5. Use the benchmark and health check features"
echo ""
echo "💾 Cluster specification saved to: cluster-spec.json"
echo ""
echo "🧹 To cleanup later, run:"
echo "   gcloud compute instances delete mongo-primary mongo-secondary mongo-analytics --zone=$ZONE --quiet"
echo "   gcloud compute firewall-rules delete mongo-ssh mongo-internal --quiet"
echo ""
