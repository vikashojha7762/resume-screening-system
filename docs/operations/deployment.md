# Production Deployment Guide

Step-by-step guide for deploying the Resume Screening System to production.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured with cluster access
- Docker registry credentials
- SSL certificate management (cert-manager)
- Ingress controller (NGINX)
- Storage classes configured

## Pre-Deployment Checklist

- [ ] Kubernetes cluster ready
- [ ] Docker images built and pushed
- [ ] Secrets prepared
- [ ] ConfigMaps configured
- [ ] Database credentials ready
- [ ] Redis credentials ready
- [ ] SSL certificates configured
- [ ] DNS records configured
- [ ] Monitoring stack deployed
- [ ] Backup system configured

## Deployment Steps

### 1. Prepare Environment

```bash
# Set environment variables
export NAMESPACE=resume-screening
export REGISTRY=your-registry.io
export IMAGE_TAG=v1.0.0
```

### 2. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 3. Create Secrets

**Important:** Never commit secrets to git!

```bash
# Create secrets from file
kubectl create secret generic resume-screening-secrets \
  --from-file=k8s/secrets.yaml \
  -n resume-screening

# Or create manually
kubectl create secret generic resume-screening-secrets \
  --from-literal=DB_PASSWORD='your-password' \
  --from-literal=SECRET_KEY='your-secret-key' \
  -n resume-screening
```

### 4. Deploy ConfigMaps

```bash
kubectl apply -f k8s/configmap.yaml
```

### 5. Deploy Database

```bash
# Deploy PostgreSQL
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n resume-screening --timeout=300s

# Run migrations
kubectl exec -it postgres-0 -n resume-screening -- \
  psql -U postgres -d resume_screening -f /migrations/init.sql
```

### 6. Deploy Redis

```bash
kubectl apply -f k8s/redis-deployment.yaml

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis -n resume-screening --timeout=300s
```

### 7. Deploy Backend

```bash
# Update image tag in deployment
sed -i 's|image:.*|image: your-registry.io/backend:v1.0.0|' k8s/backend-deployment.yaml

# Deploy
kubectl apply -f k8s/backend-deployment.yaml

# Wait for rollout
kubectl rollout status deployment/backend -n resume-screening --timeout=5m
```

### 8. Deploy Celery

```bash
kubectl apply -f k8s/celery-deployment.yaml

# Wait for workers
kubectl rollout status deployment/celery-worker -n resume-screening
kubectl rollout status deployment/celery-beat -n resume-screening
```

### 9. Deploy Frontend

```bash
# Update image tag
sed -i 's|image:.*|image: your-registry.io/frontend:v1.0.0|' k8s/frontend-deployment.yaml

# Deploy
kubectl apply -f k8s/frontend-deployment.yaml

# Wait for rollout
kubectl rollout status deployment/frontend -n resume-screening
```

### 10. Deploy Ingress

```bash
kubectl apply -f k8s/ingress.yaml

# Verify ingress
kubectl get ingress -n resume-screening
```

### 11. Deploy Autoscaling

```bash
kubectl apply -f k8s/hpa.yaml
```

### 12. Deploy Network Policies

```bash
kubectl apply -f k8s/network-policy.yaml
```

### 13. Deploy Pod Disruption Budgets

```bash
kubectl apply -f k8s/pdb.yaml
```

## Verification

### Check Pod Status

```bash
kubectl get pods -n resume-screening
```

All pods should be in `Running` state.

### Check Services

```bash
kubectl get services -n resume-screening
```

### Test Endpoints

```bash
# Health check
curl https://api.resumescreening.com/health

# API endpoint
curl https://api.resumescreening.com/api/v1/health
```

### Check Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n resume-screening

# Celery logs
kubectl logs -f deployment/celery-worker -n resume-screening
```

## Post-Deployment

### 1. Verify Functionality

- [ ] Login works
- [ ] Job creation works
- [ ] Resume upload works
- [ ] Matching works
- [ ] Results display correctly

### 2. Monitor Metrics

- [ ] Check Prometheus metrics
- [ ] Review Grafana dashboards
- [ ] Verify no alerts firing

### 3. Test Performance

- [ ] API response times < 1s
- [ ] Database queries optimized
- [ ] No memory leaks
- [ ] CPU usage normal

### 4. Security Check

- [ ] SSL certificates valid
- [ ] Network policies enforced
- [ ] Secrets not exposed
- [ ] Authentication working

## Rollback Procedure

If deployment fails:

```bash
# Rollback backend
kubectl rollout undo deployment/backend -n resume-screening

# Rollback frontend
kubectl rollout undo deployment/frontend -n resume-screening

# Check previous revisions
kubectl rollout history deployment/backend -n resume-screening
```

## Updating Deployment

### Update Application

```bash
# Build new images
docker build -t your-registry.io/backend:v1.1.0 ./backend
docker push your-registry.io/backend:v1.1.0

# Update deployment
kubectl set image deployment/backend \
  backend=your-registry.io/backend:v1.1.0 \
  -n resume-screening

# Monitor rollout
kubectl rollout status deployment/backend -n resume-screening
```

### Update Configuration

```bash
# Update ConfigMap
kubectl apply -f k8s/configmap.yaml

# Restart pods to pick up changes
kubectl rollout restart deployment/backend -n resume-screening
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n resume-screening

# Check events
kubectl get events -n resume-screening --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n resume-screening
```

### Database Connection Issues

```bash
# Test connection
kubectl exec -it postgres-0 -n resume-screening -- \
  psql -U postgres -c "SELECT 1"

# Check service
kubectl get svc postgres-service -n resume-screening
```

### Image Pull Errors

```bash
# Check image pull secrets
kubectl get secrets -n resume-screening

# Create registry secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.io \
  --docker-username=your-username \
  --docker-password=your-password \
  -n resume-screening
```

## See Also

- [Operations README](./README.md)
- [Monitoring Guide](./monitoring.md)
- [Disaster Recovery](../../scripts/disaster-recovery-runbook.md)

