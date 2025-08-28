#!/bin/bash

# Script to create GitHub credentials secret for private repository access
# Usage: ./create-github-secret.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo -e "${BLUE}🔐 GitHub Credentials Setup for Private Repository${NC}"
echo "======================================================="

# Check if logged into OpenShift
if ! oc whoami &> /dev/null; then
    print_error "Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

print_success "Logged in as: $(oc whoami)"

# Check if secret already exists
if oc get secret github-credentials &> /dev/null; then
    print_warning "Secret 'github-credentials' already exists!"
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting existing secret..."
        oc delete secret github-credentials
    else
        echo "Keeping existing secret."
        exit 0
    fi
fi

echo ""
print_info "You need a GitHub Personal Access Token for private repository access."
print_info "If you don't have one, create it at: https://github.com/settings/tokens"
print_info "Required scopes: 'repo' (Full control of private repositories)"
echo ""

# Get GitHub username
read -p "🔑 Enter your GitHub username: " GITHUB_USERNAME

# Get GitHub token (hidden input)
echo -n "🔑 Enter your GitHub Personal Access Token: "
read -s GITHUB_TOKEN
echo ""

# Validate inputs
if [ -z "$GITHUB_USERNAME" ] || [ -z "$GITHUB_TOKEN" ]; then
    print_error "Username and token are required!"
    exit 1
fi

# Create the secret
echo ""
echo "🔐 Creating GitHub credentials secret..."

oc create secret generic github-credentials \
    --from-literal=username="$GITHUB_USERNAME" \
    --from-literal=password="$GITHUB_TOKEN"

# Label the secret
oc label secret github-credentials app=wheel-of-fortune

print_success "GitHub credentials secret created successfully!"
echo ""
print_info "You can now run './deploy.sh' to deploy your application."
echo ""

# Verify the secret
echo "🔍 Verifying secret creation..."
if oc get secret github-credentials &> /dev/null; then
    print_success "Secret 'github-credentials' is ready for use."
else
    print_error "Failed to create secret!"
    exit 1
fi
