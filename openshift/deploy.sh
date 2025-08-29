#!/bin/bash

# OpenShift Deployment Script for Wheel of Fortune Game
# Usage: ./deploy.sh [build|deploy|clean|status]

set -e

NAMESPACE="wheel-of-fortune"
PROJECT_NAME="wheel-of-fortune"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🎡 Wheel of Fortune - OpenShift Deployment${NC}"
    echo "=================================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_oc_login() {
    if ! oc whoami &> /dev/null; then
        print_error "Not logged in to OpenShift. Please run 'oc login' first."
        exit 1
    fi
    print_success "Logged in as: $(oc whoami)"
}

deploy() {
    print_header
    check_oc_login
    
    echo "🚀 Deploying Wheel of Fortune to OpenShift..."
    
    
    # Deploy all resources
    echo "📦 Applying Kubernetes resources..."
    oc apply -k .
    
    # Wait for builds to be created
    echo "⏳ Waiting for BuildConfigs to be created..."
    sleep 5
    
    # Start builds
    echo "🔨 Starting builds..."
    oc start-build wof-backend || print_warning "Backend build may already be running"
    oc start-build wof-frontend || print_warning "Frontend build may already be running"
    
    # Wait for builds to complete
    echo "⏳ Waiting for builds to complete..."
    oc wait --for=condition=Complete build/wof-backend-1 --timeout=600s || true
    oc wait --for=condition=Complete build/wof-frontend-1 --timeout=300s || true
    
    # Wait for deployments to be ready
    echo "⏳ Waiting for deployments to be ready..."
    oc wait --for=condition=Available deployment/wof-backend --timeout=300s
    oc wait --for=condition=Available deployment/wof-frontend --timeout=300s
    
    # Get route URL
    ROUTE_URL=$(oc get route wof-frontend-route -o jsonpath='{.spec.host}' 2>/dev/null || echo "Not available yet")
    
    print_success "Deployment completed!"
    echo ""
    echo "🌐 Game URL: https://${ROUTE_URL}"
    echo ""
    echo "🔍 Check status with: ./deploy.sh status"
}

build_only() {
    print_header
    check_oc_login
    
    echo "🔨 Starting builds only..."
    
    # Switch to project
    oc project $NAMESPACE || print_error "Project $NAMESPACE not found. Run deploy first."
    
    # Start builds
    oc start-build wof-backend
    oc start-build wof-frontend
    
    # Follow logs
    echo "📋 Following build logs (Ctrl+C to stop)..."
    oc logs -f bc/wof-backend &
    oc logs -f bc/wof-frontend &
    
    wait
}

status() {
    print_header
    check_oc_login
    
    echo "📊 Checking deployment status..."
    echo ""
    
    # Switch to project
    if ! oc project $NAMESPACE &> /dev/null; then
        print_error "Project $NAMESPACE not found. Run deploy first."
        exit 1
    fi
    
    echo "🏗️  Build Status:"
    oc get builds
    echo ""
    
    echo "🚀 Pod Status:"
    oc get pods
    echo ""
    
    echo "🔗 Service Status:"
    oc get svc
    echo ""
    
    echo "🌐 Route Status:"
    oc get routes
    echo ""
    
    # Check if route is accessible
    ROUTE_URL=$(oc get route wof-frontend-route -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    if [ ! -z "$ROUTE_URL" ]; then
        echo "🔍 Testing route accessibility..."
        if curl -s -o /dev/null -w "%{http_code}" "https://${ROUTE_URL}" | grep -q "200\|301\|302"; then
            print_success "Game is accessible at: https://${ROUTE_URL}"
        else
            print_warning "Route exists but may not be responding yet"
        fi
    fi
}

clean() {
    print_header
    check_oc_login
    
    echo "🧹 Cleaning up deployment..."
    
    # Delete all resources
    echo "🗑️  Deleting resources..."
    oc delete -k . || print_warning "Some resources may not exist"
    
    # Delete project
    echo "🗑️  Deleting project..."
    oc delete project $NAMESPACE || print_warning "Project may not exist"
    
    print_success "Cleanup completed!"
}

logs() {
    print_header
    check_oc_login
    
    # Switch to project
    oc project $NAMESPACE || print_error "Project $NAMESPACE not found."
    
    echo "📋 Streaming logs (Ctrl+C to stop)..."
    echo ""
    
    # Follow logs from both deployments
    oc logs -f deployment/wof-backend --prefix=true &
    oc logs -f deployment/wof-frontend --prefix=true &
    
    wait
}

case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        build_only
        ;;
    "status")
        status
        ;;
    "clean")
        clean
        ;;
    "logs")
        logs
        ;;
    *)
        echo "Usage: $0 [deploy|build|status|clean|logs]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the complete application (default)"
        echo "  build   - Start builds only"
        echo "  status  - Check deployment status"
        echo "  clean   - Remove all resources"
        echo "  logs    - Stream application logs"
        exit 1
        ;;
esac
