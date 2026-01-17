#!/bin/bash

# Deployment Validation Script
# Validates deployment on staging/production environment

set -e

echo "=========================================="
echo "Deployment Validation Script"
echo "=========================================="
echo ""

# Configuration
NAMESPACE="${NAMESPACE:-resume-screening}"
TIMEOUT=300

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
check_pod_status() {
    local pod_name=$1
    local status=$(kubectl get pod $pod_name -n $NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
    
    if [ "$status" = "Running" ]; then
        echo -e "${GREEN}✅${NC} $pod_name: Running"
        return 0
    else
        echo -e "${RED}❌${NC} $pod_name: $status"
        return 1
    fi
}

check_service_endpoint() {
    local service_name=$1
    local port=$2
    local path=${3:-/health}
    
    local endpoint=$(kubectl get svc $service_name -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    
    if [ -z "$endpoint" ]; then
        endpoint="localhost"
    fi
    
    if curl -f -s "http://$endpoint:$port$path" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $service_name endpoint: Accessible"
        return 0
    else
        echo -e "${RED}❌${NC} $service_name endpoint: Not accessible"
        return 1
    fi
}

# Validation Steps
echo "Step 1: Checking Namespace..."
if kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Namespace exists"
else
    echo -e "${RED}❌${NC} Namespace not found"
    exit 1
fi

echo ""
echo "Step 2: Checking Pod Status..."
PODS=("backend" "frontend" "celery-worker" "celery-beat" "postgres" "redis")
ALL_PODS_OK=true

for pod in "${PODS[@]}"; do
    # Get pod name (handles multiple replicas)
    pod_name=$(kubectl get pods -n $NAMESPACE -l app=$pod -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$pod_name" ]; then
        if ! check_pod_status "$pod_name"; then
            ALL_PODS_OK=false
        fi
    else
        echo -e "${RED}❌${NC} $pod: Pod not found"
        ALL_PODS_OK=false
    fi
done

if [ "$ALL_PODS_OK" = false ]; then
    echo -e "${RED}❌${NC} Some pods are not running"
    exit 1
fi

echo ""
echo "Step 3: Checking Service Endpoints..."
check_service_endpoint "backend-service" 80 "/health"
check_service_endpoint "frontend-service" 80 "/health"

echo ""
echo "Step 4: Checking Database Connection..."
DB_POD=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$DB_POD" ]; then
    if kubectl exec -n $NAMESPACE $DB_POD -- pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} Database is ready"
    else
        echo -e "${RED}❌${NC} Database is not ready"
        exit 1
    fi
else
    echo -e "${RED}❌${NC} Database pod not found"
    exit 1
fi

echo ""
echo "Step 5: Checking Redis Connection..."
REDIS_POD=$(kubectl get pods -n $NAMESPACE -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$REDIS_POD" ]; then
    if kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} Redis is ready"
    else
        echo -e "${RED}❌${NC} Redis is not ready"
        exit 1
    fi
else
    echo -e "${RED}❌${NC} Redis pod not found"
    exit 1
fi

echo ""
echo "Step 6: Checking Health Endpoints..."
BACKEND_URL=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[?(@.metadata.name=="resume-screening-ingress")].spec.rules[0].host}' 2>/dev/null || echo "localhost:8000")

if curl -f -s "http://$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Backend health check: PASS"
else
    echo -e "${RED}❌${NC} Backend health check: FAIL"
    exit 1
fi

echo ""
echo "Step 7: Checking Monitoring..."
if kubectl get pods -n monitoring > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Monitoring stack deployed"
else
    echo -e "${YELLOW}⚠️${NC}  Monitoring stack not found (optional)"
fi

echo ""
echo "Step 8: Checking Resource Usage..."
echo "CPU and Memory usage:"
kubectl top pods -n $NAMESPACE 2>/dev/null || echo "Metrics not available"

echo ""
echo "Step 9: Checking Persistent Volumes..."
PVCS=$(kubectl get pvc -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
if [ -n "$PVCS" ]; then
    for pvc in $PVCS; do
        status=$(kubectl get pvc $pvc -n $NAMESPACE -o jsonpath='{.status.phase}')
        if [ "$status" = "Bound" ]; then
            echo -e "${GREEN}✅${NC} PVC $pvc: Bound"
        else
            echo -e "${RED}❌${NC} PVC $pvc: $status"
        fi
    done
else
    echo -e "${YELLOW}⚠️${NC}  No PVCs found"
fi

echo ""
echo "Step 10: Checking Ingress..."
INGRESS=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$INGRESS" ]; then
    echo -e "${GREEN}✅${NC} Ingress configured: $INGRESS"
    kubectl get ingress $INGRESS -n $NAMESPACE
else
    echo -e "${YELLOW}⚠️${NC}  Ingress not configured"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment Validation Complete${NC}"
echo "=========================================="

