# Disaster Recovery Runbook

## Overview
This document outlines procedures for disaster recovery and business continuity for the Resume Screening System.

## Recovery Objectives

### RTO (Recovery Time Objective)
- **Critical Services**: 1 hour
- **Non-Critical Services**: 4 hours

### RPO (Recovery Point Objective)
- **Database**: 15 minutes (point-in-time recovery)
- **Application Data**: 1 hour

## Pre-Disaster Preparation

### Regular Backups
1. **Database Backups**: Automated daily backups with 30-day retention
2. **Application Code**: Version controlled in Git
3. **Configuration**: Stored in Kubernetes ConfigMaps and Secrets
4. **Infrastructure**: Infrastructure as Code (Kubernetes manifests)

### Backup Verification
- Weekly restore tests
- Monthly full disaster recovery drill

## Disaster Scenarios

### Scenario 1: Complete Cluster Failure

**Symptoms:**
- All pods unreachable
- Kubernetes API unresponsive
- No services accessible

**Recovery Steps:**
1. **Assess Situation** (5 minutes)
   - Check cluster status
   - Verify backup availability
   - Identify last known good state

2. **Restore Infrastructure** (30 minutes)
   ```bash
   # Restore Kubernetes cluster
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/secrets.yaml
   ```

3. **Restore Database** (20 minutes)
   ```bash
   # Restore from latest backup
   ./scripts/database/restore.sh /backups/postgres/backup_latest.dump.gz
   ```

4. **Deploy Applications** (10 minutes)
   ```bash
   kubectl apply -f k8s/backend-deployment.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   kubectl apply -f k8s/celery-deployment.yaml
   ```

5. **Verify Services** (5 minutes)
   - Check health endpoints
   - Verify database connectivity
   - Test API endpoints

**Total Recovery Time**: ~70 minutes

### Scenario 2: Database Corruption

**Symptoms:**
- Database queries failing
- Connection errors
- Data inconsistency

**Recovery Steps:**
1. **Stop Affected Services** (2 minutes)
   ```bash
   kubectl scale deployment backend --replicas=0
   kubectl scale deployment celery-worker --replicas=0
   ```

2. **Identify Corruption** (10 minutes)
   ```bash
   # Run database diagnostics
   ./scripts/database/optimize.sh
   ```

3. **Restore from Backup** (15 minutes)
   ```bash
   # Point-in-time recovery
   ./scripts/database/restore.sh /backups/postgres/backup_latest.dump.gz
   ```

4. **Restart Services** (5 minutes)
   ```bash
   kubectl scale deployment backend --replicas=3
   kubectl scale deployment celery-worker --replicas=2
   ```

5. **Verify Data Integrity** (10 minutes)
   - Run data validation queries
   - Check application logs
   - Verify API responses

**Total Recovery Time**: ~42 minutes

### Scenario 3: Application Code Corruption

**Symptoms:**
- Application crashes
- Runtime errors
- Service unavailability

**Recovery Steps:**
1. **Rollback to Previous Version** (5 minutes)
   ```bash
   kubectl rollout undo deployment/backend
   kubectl rollout undo deployment/frontend
   ```

2. **Verify Rollback** (5 minutes)
   - Check pod status
   - Verify health endpoints
   - Test critical functionality

**Total Recovery Time**: ~10 minutes

### Scenario 4: Security Breach

**Symptoms:**
- Unauthorized access
- Data exfiltration
- Malicious activity

**Recovery Steps:**
1. **Immediate Response** (5 minutes)
   - Isolate affected services
   - Revoke compromised credentials
   - Enable additional logging

2. **Containment** (15 minutes)
   ```bash
   # Scale down affected services
   kubectl scale deployment backend --replicas=0
   
   # Update secrets
   kubectl delete secret resume-screening-secrets
   kubectl create secret generic resume-screening-secrets --from-file=secrets.yaml
   ```

3. **Investigation** (30 minutes)
   - Review logs
   - Identify attack vector
   - Assess data exposure

4. **Remediation** (20 minutes)
   - Patch vulnerabilities
   - Update security policies
   - Restore from clean backup if needed

5. **Restore Services** (10 minutes)
   ```bash
   kubectl scale deployment backend --replicas=3
   ```

**Total Recovery Time**: ~80 minutes

## Backup Procedures

### Database Backup
- **Frequency**: Daily at 2 AM UTC
- **Retention**: 30 days local, 90 days in S3
- **Location**: `/backups/postgres` and S3 bucket

### Application Backup
- **Code**: Git repository (automatic)
- **Configuration**: Kubernetes manifests (version controlled)
- **Secrets**: External secret management (Vault)

## Restoration Procedures

### Database Restoration
```bash
# Full restore
./scripts/database/restore.sh /backups/postgres/backup_YYYYMMDD_HHMMSS.dump.gz

# Point-in-time recovery (if enabled)
pg_restore --time="2024-01-01 12:00:00" backup.dump
```

### Application Restoration
```bash
# Restore from Git
git checkout <commit-hash>
kubectl apply -f k8s/
```

## Communication Plan

### Internal Team
- **Primary Contact**: DevOps Lead
- **Secondary Contact**: Backend Lead
- **Escalation**: CTO

### External Stakeholders
- **Status Page**: https://status.resumescreening.com
- **Email Notifications**: Automated via monitoring system

## Testing and Validation

### Monthly DR Drill
1. Simulate disaster scenario
2. Execute recovery procedures
3. Measure recovery times
4. Document lessons learned
5. Update runbook

### Quarterly Full Test
1. Complete system restore
2. End-to-end functionality test
3. Performance validation
4. Security audit

## Post-Recovery Actions

1. **Documentation**
   - Record incident details
   - Update runbook with lessons learned
   - Review and improve procedures

2. **Monitoring**
   - Enhanced monitoring for 48 hours
   - Review logs for anomalies
   - Verify backup integrity

3. **Communication**
   - Notify stakeholders of resolution
   - Post-mortem meeting
   - Action items and follow-up

## Contact Information

- **On-Call Engineer**: [Contact Info]
- **DevOps Team**: [Contact Info]
- **Emergency Hotline**: [Phone Number]

## Appendix

### Backup Locations
- **S3 Bucket**: `s3://resume-screening-backups`
- **Local Storage**: `/backups` on backup server
- **Git Repository**: `https://github.com/org/resume-screening`

### Recovery Scripts
- Database backup: `scripts/database/backup.sh`
- Database restore: `scripts/database/restore.sh`
- Database optimize: `scripts/database/optimize.sh`

