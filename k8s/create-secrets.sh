#!/bin/bash

# Create Kubernetes secrets from .env file
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-dev}
SECRET_NAME=${SECRET_NAME:-echoo-secrets}
ENV_FILE=${ENV_FILE:-../.env}

echo -e "${BLUE}🔐 Creating Kubernetes secrets from .env file...${NC}"

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}❌ .env file not found at: $ENV_FILE${NC}"
    echo -e "${YELLOW}💡 Make sure .env file exists in the project root${NC}"
    exit 1
fi

# Check if namespace exists, create if it doesn't
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}📦 Creating namespace: $NAMESPACE${NC}"
    kubectl create namespace "$NAMESPACE"
else
    echo -e "${GREEN}✅ Namespace $NAMESPACE already exists${NC}"
fi

# Delete existing secret if it exists
if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}🗑️  Deleting existing secret: $SECRET_NAME${NC}"
    kubectl delete secret "$SECRET_NAME" -n "$NAMESPACE"
fi

echo -e "${BLUE}📝 Reading environment variables from $ENV_FILE...${NC}"

# Create the secret from .env file
kubectl create secret generic "$SECRET_NAME" \
    --from-env-file="$ENV_FILE" \
    --namespace="$NAMESPACE"

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Secret $SECRET_NAME created successfully in namespace $NAMESPACE${NC}"
    
    # Show the secret (without values)
    echo -e "${BLUE}📊 Secret contents:${NC}"
    kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o yaml | grep -E '(name:|data:)' | head -10
else
    echo -e "${RED}❌ Failed to create secret${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Secrets setup completed!${NC}"
echo -e "${YELLOW}💡 Secret name: $SECRET_NAME${NC}"
echo -e "${YELLOW}💡 Namespace: $NAMESPACE${NC}"