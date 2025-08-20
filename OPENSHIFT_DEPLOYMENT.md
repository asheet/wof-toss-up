# 🎡 Wheel of Fortune - OpenShift Deployment Guide

This guide will help you deploy the Wheel of Fortune game to OpenShift using Kubernetes YAML manifests.

## 📋 Prerequisites

- **OpenShift CLI (oc)**: Install from [OpenShift CLI Tools](https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html)
- **OpenShift Cluster Access**: Either local (CodeReady Containers) or cloud-based
- **Git Repository**: Your code hosted on GitHub/GitLab with public access
- **oc login**: Authenticated session to your OpenShift cluster

## 🚀 Quick Start

### 1. Login to OpenShift
```bash
# Login to your OpenShift cluster
oc login --token=<your-token> --server=<your-server>

# Or with username/password
oc login -u <username> -p <password> <cluster-url>
```

### 2. Create and Deploy
```bash
# Clone the repository
git clone <your-repo-url>
cd wof

# Create namespace
oc apply -f openshift/namespace.yaml

# Switch to the namespace
oc project wheel-of-fortune

# Deploy all resources
oc apply -k openshift/
```

### 3. Build Images
```bash
# Start builds (if using BuildConfigs)
oc start-build wof-backend
oc start-build wof-frontend

# Monitor build progress
oc logs -f bc/wof-backend
oc logs -f bc/wof-frontend
```

### 4. Access the Game
```bash
# Get the route URL
oc get route wof-frontend-route -o jsonpath='{.spec.host}'

# Visit the URL in your browser
echo "Game available at: https://$(oc get route wof-frontend-route -o jsonpath='{.spec.host}')"
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     OpenShift Cluster                   │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │   Frontend      │    │    Backend      │            │
│  │   (nginx:8080)  │────│ (FastAPI:8000)  │            │
│  │                 │    │                 │            │
│  │ • Static Files  │    │ • WebSocket API │            │
│  │ • Proxy Config  │    │ • Game Logic    │            │
│  │ • 2 Replicas    │    │ • 2 Replicas    │            │
│  └─────────────────┘    └─────────────────┘            │
│           │                                             │
│  ┌─────────────────┐                                   │
│  │   OpenShift     │                                   │
│  │   Route (HTTPS) │                                   │
│  └─────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

## 📁 OpenShift Resources

### **Created Files:**
```
📦 openshift/
├── 🏷️  namespace.yaml              # Project namespace
├── 📦 kustomization.yaml          # Resource management
├── 🖼️  backend-imagestream.yaml    # Backend image stream
├── 🔨 backend-buildconfig.yaml    # Backend build config
├── 🚀 backend-deployment.yaml     # Backend deployment
├── 🔗 backend-service.yaml        # Backend service
├── 🖼️  frontend-imagestream.yaml   # Frontend image stream
├── 🔨 frontend-buildconfig.yaml   # Frontend build config
├── ⚙️  nginx-configmap.yaml        # Nginx configuration
├── 🚀 frontend-deployment.yaml    # Frontend deployment
├── 🔗 frontend-service.yaml       # Frontend service
└── 🌐 route.yaml                  # External route (HTTPS)
```

## ⚙️ Configuration Details

### **Backend Configuration:**
- **Image**: Built from `backend/` directory
- **Port**: 8000 (internal)
- **Replicas**: 2 for high availability
- **Resources**: 256Mi-512Mi RAM, 100m-500m CPU
- **Health Checks**: HTTP probes on `/`

### **Frontend Configuration:**
- **Image**: Built from `frontend/` directory  
- **Port**: 8080 (OpenShift compatible)
- **Replicas**: 2 for high availability
- **Resources**: 64Mi-128Mi RAM, 50m-200m CPU
- **Config**: Nginx configuration via ConfigMap

### **Security Features:**
- **Non-root containers**: Both services run as user 1001
- **Security context**: No privilege escalation allowed
- **TLS termination**: HTTPS via OpenShift Route
- **Network policies**: Internal service communication only

## 🔧 Alternative Deployment Methods

### **Method 1: Using oc apply (Recommended)**
```bash
# Deploy everything at once
oc apply -k openshift/

# Or deploy resources individually
oc apply -f openshift/namespace.yaml
oc apply -f openshift/nginx-configmap.yaml
oc apply -f openshift/backend-imagestream.yaml
oc apply -f openshift/backend-buildconfig.yaml
oc apply -f openshift/backend-deployment.yaml
oc apply -f openshift/backend-service.yaml
oc apply -f openshift/frontend-imagestream.yaml
oc apply -f openshift/frontend-buildconfig.yaml
oc apply -f openshift/frontend-deployment.yaml
oc apply -f openshift/frontend-service.yaml
oc apply -f openshift/route.yaml
```

### **Method 2: Using OpenShift Web Console**
1. **Login to OpenShift Web Console**
2. **Create Project**: `wheel-of-fortune`
3. **Import YAML**: Copy/paste each YAML file
4. **Monitor Builds**: Watch build progress in console
5. **Access Route**: Click on route URL

### **Method 3: Using oc new-app (Source-to-Image)**
```bash
# Create new project
oc new-project wheel-of-fortune

# Deploy backend from source
oc new-app python:3.11~https://github.com/your-username/wof.git \
    --context-dir=backend \
    --name=wof-backend

# Deploy frontend from source
oc new-app nginx:1.25~https://github.com/your-username/wof.git \
    --context-dir=frontend \
    --name=wof-frontend

# Expose frontend
oc expose svc/wof-frontend
```

## 🔍 Monitoring & Troubleshooting

### **Check Build Status:**
```bash
# List all builds
oc get builds

# Check build logs
oc logs -f build/wof-backend-1
oc logs -f build/wof-frontend-1

# Describe build for details
oc describe bc/wof-backend
```

### **Check Pod Status:**
```bash
# List all pods
oc get pods

# Check pod logs
oc logs -f deployment/wof-backend
oc logs -f deployment/wof-frontend

# Describe pod for events
oc describe pod <pod-name>
```

### **Check Services & Routes:**
```bash
# List services
oc get svc

# List routes
oc get routes

# Test internal connectivity
oc exec deployment/wof-frontend -- curl http://wof-backend:8000/
```

### **Resource Status:**
```bash
# Check all resources
oc get all

# Check resource quotas
oc describe quota

# Check limits
oc describe limits
```

## 🔧 Customization

### **Update Git Repository:**
Edit `backend-buildconfig.yaml` and `frontend-buildconfig.yaml`:
```yaml
source:
  git:
    uri: https://github.com/YOUR-USERNAME/wof.git  # Update this
    ref: main
```

### **Custom Domain:**
Edit `route.yaml`:
```yaml
spec:
  host: wof.yourdomain.com  # Add custom hostname
  to:
    kind: Service
    name: wof-frontend
```

### **Resource Scaling:**
```bash
# Scale backend
oc scale deployment/wof-backend --replicas=3

# Scale frontend
oc scale deployment/wof-frontend --replicas=4

# Auto-scaling (if HPA available)
oc autoscale deployment/wof-backend --min=2 --max=10 --cpu-percent=70
```

### **Environment Variables:**
Add to deployment YAML:
```yaml
env:
- name: GAME_DEBUG
  value: "false"
- name: GAME_ROUND_TIME
  value: "45"
```

## 📊 Production Considerations

### **Resource Quotas:**
```bash
# Set resource quotas for the namespace
oc apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: wof-quota
  namespace: wheel-of-fortune
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    pods: "10"
EOF
```

### **Network Policies:**
```bash
# Restrict network access
oc apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: wof-network-policy
  namespace: wheel-of-fortune
spec:
  podSelector:
    matchLabels:
      app: wheel-of-fortune
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: wheel-of-fortune
EOF
```

### **Persistent Storage (Future):**
```yaml
# For game statistics/logs
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wof-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

## 🔄 CI/CD Integration

### **GitHub Actions:**
```yaml
# .github/workflows/openshift.yml
name: Deploy to OpenShift
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Login to OpenShift
      run: oc login --token=${{ secrets.OPENSHIFT_TOKEN }} --server=${{ secrets.OPENSHIFT_SERVER }}
    - name: Deploy
      run: oc apply -k openshift/
    - name: Start Builds
      run: |
        oc start-build wof-backend
        oc start-build wof-frontend
```

### **GitLab CI:**
```yaml
# .gitlab-ci.yml
deploy:
  image: openshift/origin-cli
  script:
    - oc login --token=$OPENSHIFT_TOKEN --server=$OPENSHIFT_SERVER
    - oc apply -k openshift/
    - oc start-build wof-backend wof-frontend
  only:
    - main
```

## 🆘 Common Issues

### **Build Failures:**
```bash
# Check build logs
oc logs bc/wof-backend

# Common fixes:
oc set env bc/wof-backend GIT_SSL_NO_VERIFY=true  # SSL issues
oc patch bc/wof-backend -p '{"spec":{"resources":{"limits":{"memory":"1Gi"}}}}'  # Memory limits
```

### **Pod CrashLoopBackOff:**
```bash
# Check pod events
oc describe pod <pod-name>

# Check logs
oc logs <pod-name> --previous

# Debug by shell access
oc rsh deployment/wof-backend
```

### **Route Not Accessible:**
```bash
# Check route
oc get route wof-frontend-route

# Check if TLS is working
curl -I https://$(oc get route wof-frontend-route -o jsonpath='{.spec.host}')

# Check service endpoints
oc get endpoints
```

---

🎮 **Your Wheel of Fortune game is now ready for OpenShift!** 

Access it via the route URL and enjoy your multiplayer game in the cloud! 🎡☁️
