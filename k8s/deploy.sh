#!/bin/bash

# Echoo API Kubernetes Deployment Script
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-default}
ECR_REGISTRY=${ECR_REGISTRY:-"your-account.dkr.ecr.us-east-2.amazonaws.com"}
IMAGE_TAG=${IMAGE_TAG:-latest}

echo -e "${BLUE}🚀 Deploying Echoo API to Kubernetes...${NC}"

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
        echo -e "${YELLOW}💡 Make sure your kubeconfig is set up correctly${NC}"
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

# Function to apply Kubernetes manifests
apply_manifests() {
    echo -e "${BLUE}📋 Applying Kubernetes manifests...${NC}"
    
    # Apply in order
    echo -e "${YELLOW}🔧 Creating ConfigMap...${NC}"
    kubectl apply -f configmap.yaml -n "$NAMESPACE"
    
    echo -e "${YELLOW}👤 Creating Service Account...${NC}"
    kubectl apply -f service-account.yaml -n "$NAMESPACE"
    
    echo -e "${YELLOW}🔐 Creating Secrets (if secrets.yaml exists)...${NC}"
    if [[ -f "secrets.yaml" ]]; then
        kubectl apply -f secrets.yaml -n "$NAMESPACE"
    else
        echo -e "${RED}⚠️  secrets.yaml not found. You need to create secrets manually!${NC}"
        echo -e "${YELLOW}💡 Run: kubectl create secret generic echoo-secrets --from-literal=...${NC}"
    fi
    
    echo -e "${YELLOW}🚢 Creating Deployment...${NC}"
    # Replace image placeholder with actual ECR registry
    sed "s|<your-ecr-registry>|$ECR_REGISTRY|g" deployment.yaml | kubectl apply -f - -n "$NAMESPACE"
    
    echo -e "${YELLOW}🌐 Creating Services...${NC}"
    kubectl apply -f service.yaml -n "$NAMESPACE"
    
    echo -e "${YELLOW}🌍 Creating Ingress...${NC}"
    kubectl apply -f ingress.yaml -n "$NAMESPACE"
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "${BLUE}⏳ Waiting for deployment to be ready...${NC}"
    kubectl rollout status deployment/echoo-api -n "$NAMESPACE" --timeout=300s
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Deployment is ready!${NC}"
    else
        echo -e "${RED}❌ Deployment failed to become ready${NC}"
        exit 1
    fi
}

# Function to show deployment status
show_status() {
    echo -e "${BLUE}📊 Deployment Status:${NC}"
    kubectl get pods,svc,ingress -n "$NAMESPACE" -l app=echoo-api
    
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
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Pre-flight checks...${NC}"
    check_kubectl
    check_cluster
    
    echo -e "${BLUE}📦 Setting up namespace...${NC}"
    create_namespace
    
    echo -e "${BLUE}🚀 Deploying application...${NC}"
    apply_manifests
    
    echo -e "${BLUE}⏳ Waiting for deployment...${NC}"
    wait_for_deployment
    
    echo -e "${BLUE}📊 Showing status...${NC}"
    show_status
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo -e "   1. Wait for LoadBalancer to get an external IP"
    echo -e "   2. Update your DNS to point to the LoadBalancer"
    echo -e "   3. Test the API endpoints"
    echo -e "   4. Monitor with: kubectl logs -f deployment/echoo-api -n $NAMESPACE"
}

# Run main function
main "$@"