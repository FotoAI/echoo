#!/bin/bash

# Echoo API Kubernetes Deployment Script for DEV environment
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="dev"
SECRET_NAME="echoo-secrets"
IMAGE_NAME="sjc.vultrcr.com/fotoowl/echoo:latest"

echo -e "${BLUE}🚀 Deploying Echoo API to DEV environment...${NC}"

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ kubectl is available${NC}"
}

# Function to check cluster connectivity
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        echo -e "${YELLOW}💡 Make sure KUBECONFIG is set: export KUBECONFIG=/path/to/config-prod.yaml${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
}

# Function to create namespace if it doesn't exist
create_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo -e "${YELLOW}📦 Creating namespace: $NAMESPACE${NC}"
        kubectl create namespace "$NAMESPACE"
    else
        echo -e "${GREEN}✅ Namespace $NAMESPACE already exists${NC}"
    fi
}

# Function to create secrets from .env file
create_secrets() {
    echo -e "${BLUE}🔐 Creating secrets from .env file...${NC}"
    
    # Run the create-secrets script
    ./create-secrets.sh
    
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}❌ Failed to create secrets${NC}"
        exit 1
    fi
}

# Function to apply Kubernetes manifests
apply_manifests() {
    echo -e "${BLUE}📋 Applying Kubernetes manifests...${NC}"
    
    # Apply in order
    echo -e "${YELLOW}🔧 Creating ConfigMap...${NC}"
    kubectl apply -f configmap.yaml
    
    echo -e "${YELLOW}👤 Creating Service Account...${NC}"
    kubectl apply -f service-account.yaml
    
    echo -e "${YELLOW}🚢 Creating Deployment...${NC}"
    kubectl apply -f deployment.yaml
    
    echo -e "${YELLOW}🌐 Creating Services...${NC}"
    kubectl apply -f service.yaml
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "${BLUE}⏳ Waiting for deployment to be ready...${NC}"
    kubectl rollout status deployment/echoo-api -n "$NAMESPACE" --timeout=300s
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Deployment is ready!${NC}"
    else
        echo -e "${RED}❌ Deployment failed to become ready${NC}"
        echo -e "${YELLOW}🔍 Checking pod status...${NC}"
        kubectl get pods -n "$NAMESPACE" -l app=echoo-api
        kubectl describe pods -n "$NAMESPACE" -l app=echoo-api
        exit 1
    fi
}

# Function to show deployment status
show_status() {
    echo -e "${BLUE}📊 Deployment Status:${NC}"
    kubectl get pods,svc -n "$NAMESPACE" -l app=echoo-api
    
    echo -e "\n${BLUE}🏥 Health Check:${NC}"
    # Get LoadBalancer IP/hostname
    LB_HOSTNAME=$(kubectl get svc echoo-api-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    LB_IP=$(kubectl get svc echoo-api-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    
    if [[ -n "$LB_HOSTNAME" ]]; then
        echo -e "${GREEN}🌐 LoadBalancer Hostname: $LB_HOSTNAME${NC}"
        echo -e "${YELLOW}💡 Health check: http://$LB_HOSTNAME/health${NC}"
    elif [[ -n "$LB_IP" ]]; then
        echo -e "${GREEN}🌐 LoadBalancer IP: $LB_IP${NC}"
        echo -e "${YELLOW}💡 Health check: http://$LB_IP/health${NC}"
    else
        echo -e "${YELLOW}⏳ LoadBalancer is provisioning... Check status with: kubectl get svc -n $NAMESPACE${NC}"
    fi
    
    # Show recent logs
    echo -e "\n${BLUE}📝 Recent Logs:${NC}"
    kubectl logs -n "$NAMESPACE" -l app=echoo-api --tail=20 || echo -e "${YELLOW}⚠️  Logs not available yet${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Pre-flight checks...${NC}"
    check_kubectl
    check_cluster
    
    echo -e "${BLUE}📦 Setting up namespace...${NC}"
    create_namespace
    
    echo -e "${BLUE}🔐 Setting up secrets...${NC}"
    create_secrets
    
    echo -e "${BLUE}🚀 Deploying application...${NC}"
    apply_manifests
    
    echo -e "${BLUE}⏳ Waiting for deployment...${NC}"
    wait_for_deployment
    
    echo -e "${BLUE}📊 Showing status...${NC}"
    show_status
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo -e "   1. Wait for LoadBalancer to get an external IP"
    echo -e "   2. Build and push Docker image to container registry"
    echo -e "   3. Update deployment with your image"
    echo -e "   4. Test the API endpoints"
    echo -e "   5. Monitor with: kubectl logs -f deployment/echoo-api -n $NAMESPACE"
}

# Run main function
main "$@"