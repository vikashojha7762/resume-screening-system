# Operations Documentation

Complete guide for operating and maintaining the Resume Screening System in production.

## Table of Contents

- [Production Deployment](#production-deployment)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling and Performance](#scaling-and-performance)
- [Security and Compliance](#security-and-compliance)
- [Disaster Recovery](#disaster-recovery)

## Production Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access
- SSL certificates (cert-manager)
- Ingress controller

### Deployment Steps

1. **Create Namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Create Secrets**
   ```bash
   kubectl create secret generic resume-screening-secrets \
     --from-file=k8s/secrets.yaml \
     -n resume-screening
   ```

3. **Deploy ConfigMaps**
   ```bash
   kubectl apply -f k8s/configmap.yaml
   ```

4. **Deploy Database**
   ```bash
   kubectl apply -f k8s/postgres-deployment.yaml
   kubectl apply -f k8s/redis-deployment.yaml
   ```

5. **Deploy Applications**
   ```bash
   kubectl apply -f k8s/backend-deployment.yaml
   kubectl apply -f k8s/celery-deployment.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   ```

6. **Deploy Ingress**
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

7. **Verify Deployment**
   ```bash
   kubectl get pods -n resume-screening
   kubectl get services -n resume-screening
   ```

### Rolling Updates

```bash
# Update backend image
kubectl set image deployment/backend \
  backend=resume-screening/backend:v1.1.0 \
  -n resume-screening

# Monitor rollout
kubectl rollout status deployment/backend -n resume-screening

# Rollback if needed
kubectl rollout undo deployment/backend -n resume-screening
```

## Monitoring and Alerting

### Prometheus Metrics

Access metrics at: `http://prometheus.monitoring.svc.cluster.local`

**Key Metrics:**
- `http_requests_total` - Request count
- `http_request_duration_seconds` - Response times
- `container_cpu_usage_seconds_total` - CPU usage
- `container_memory_usage_bytes` - Memory usage

### Grafana Dashboards

Access at: `http://grafana.monitoring.svc.cluster.local`

**Dashboards:**
- System Overview
- API Performance
- Database Metrics
- Celery Queue Status

### Alerting Rules

Alerts configured for:
- High error rate (>5% 5xx errors)
- High response time (p95 > 2s)
- Pod crash looping
- High memory/CPU usage (>90%)
- Database connection failures
- Redis connection failures

### Log Aggregation

**ELK Stack:**
- Elasticsearch: Log storage
- Logstash: Log processing
- Kibana: Log visualization

**Access:** `http://kibana.monitoring.svc.cluster.local`

## Backup and Recovery

### Automated Backups

**Database Backups:**
- Frequency: Daily at 2 AM UTC
- Retention: 30 days local, 90 days S3
- Location: `/backups/postgres` and S3

**Backup Script:**
```bash
./scripts/database/backup.sh
```

### Manual Backup

```bash
# Database backup
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --format=custom \
  --file=backup_$(date +%Y%m%d_%H%M%S).dump

# Compress
gzip backup_*.dump
```

### Restore Procedure

```bash
# Restore from backup
./scripts/database/restore.sh backup_20240101_020000.dump.gz
```

See [Disaster Recovery Runbook](../../scripts/disaster-recovery-runbook.md) for detailed procedures.

## Scaling and Performance

### Horizontal Pod Autoscaling

**Backend:**
- Min replicas: 3
- Max replicas: 10
- CPU threshold: 70%
- Memory threshold: 80%

**Celery Workers:**
- Min replicas: 2
- Max replicas: 5
- CPU threshold: 70%

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment/backend --replicas=5 -n resume-screening

# Scale celery workers
kubectl scale deployment/celery-worker --replicas=3 -n resume-screening
```

### Performance Tuning

**Database:**
- Connection pooling: 20-50 connections
- Query optimization: Use indexes
- Regular VACUUM and ANALYZE

**Redis:**
- Memory limit: 2GB
- Eviction policy: allkeys-lru
- Persistence: AOF enabled

**Application:**
- Worker concurrency: 4 per pod
- Request timeout: 30s
- Max upload size: 10MB

## Security and Compliance

### SSL/TLS

- Certificates managed by cert-manager
- Automatic renewal
- TLS 1.3 enforced

### Network Policies

Pod-to-pod communication restricted:
- Backend → PostgreSQL only
- Backend → Redis only
- Frontend → Backend only

### Secret Management

- Kubernetes secrets for sensitive data
- External secret management (Vault) ready
- Secrets rotated regularly

### Compliance

- **GDPR:** Data anonymization, right to deletion
- **CCPA:** Privacy controls, data access
- **SOC 2:** Security controls in place

## Disaster Recovery

### Recovery Objectives

- **RTO:** 1-4 hours
- **RPO:** 15 minutes - 1 hour

### Recovery Procedures

See [Disaster Recovery Runbook](../../scripts/disaster-recovery-runbook.md) for:
- Complete cluster failure
- Database corruption
- Application issues
- Security breaches

### Backup Verification

- Weekly restore tests
- Monthly full DR drill
- Quarterly comprehensive test

## Maintenance Windows

### Scheduled Maintenance

- **Weekly:** Database optimization
- **Monthly:** Security updates
- **Quarterly:** Full system review

### Maintenance Procedures

1. **Notify Users**
2. **Enable Maintenance Mode**
3. **Perform Updates**
4. **Verify Functionality**
5. **Disable Maintenance Mode**
6. **Notify Completion**

## Troubleshooting

### Common Issues

**Pods Not Starting:**
```bash
kubectl describe pod <pod-name> -n resume-screening
kubectl logs <pod-name> -n resume-screening
```

**Database Connection Issues:**
```bash
kubectl exec -it postgres-0 -n resume-screening -- psql -U postgres
```

**High Memory Usage:**
```bash
# Check memory usage
kubectl top pods -n resume-screening

# Restart if needed
kubectl rollout restart deployment/backend -n resume-screening
```

## See Also

- [Deployment Guide](./deployment.md)
- [Monitoring Guide](./monitoring.md)
- [Security Guide](./security.md)
- [Disaster Recovery](../../scripts/disaster-recovery-runbook.md)

