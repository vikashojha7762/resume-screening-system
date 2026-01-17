# Monitoring and Alerting Guide

Complete guide to monitoring the Resume Screening System.

## Monitoring Stack

### Components

- **Prometheus:** Metrics collection
- **Grafana:** Visualization
- **Alertmanager:** Alert routing
- **ELK Stack:** Log aggregation

## Key Metrics

### Application Metrics

- **Request Rate:** Requests per second
- **Error Rate:** Percentage of errors
- **Response Time:** p50, p95, p99
- **Throughput:** Successful requests

### Infrastructure Metrics

- **CPU Usage:** Per pod/container
- **Memory Usage:** Per pod/container
- **Disk Usage:** Per volume
- **Network:** Bandwidth usage

### Business Metrics

- **Resumes Processed:** Per hour/day
- **Matches Generated:** Per job
- **User Activity:** Active users
- **Processing Time:** Average processing duration

## Dashboards

### System Overview

**Metrics:**
- Pod status
- Resource usage
- Request rates
- Error rates

**Refresh:** 30 seconds

### API Performance

**Metrics:**
- Endpoint response times
- Request counts
- Error breakdown
- Throughput

### Database Metrics

**Metrics:**
- Connection pool
- Query performance
- Replication lag
- Disk usage

### Celery Queue

**Metrics:**
- Queue length
- Task completion rate
- Worker status
- Processing time

## Alerting Rules

### Critical Alerts

- **Service Down:** Immediate notification
- **High Error Rate:** > 10% errors
- **Database Down:** Immediate
- **Disk Full:** > 90% usage

### Warning Alerts

- **High Response Time:** p95 > 2s
- **High Memory:** > 80% usage
- **Queue Backup:** > 1000 tasks
- **Low Disk Space:** > 80% usage

## Alert Configuration

### Alert Channels

- **Email:** For all alerts
- **Slack:** For critical alerts
- **PagerDuty:** For on-call
- **SMS:** For emergencies

### Alert Routing

```yaml
routes:
  - match:
      severity: critical
    receiver: on-call-team
  - match:
      severity: warning
    receiver: dev-team
```

## Log Management

### Log Levels

- **ERROR:** Critical errors
- **WARNING:** Warnings
- **INFO:** General information
- **DEBUG:** Debug information

### Log Aggregation

**ELK Stack:**
- Elasticsearch: Storage
- Logstash: Processing
- Kibana: Visualization

### Log Retention

- **Application Logs:** 30 days
- **Access Logs:** 90 days
- **Error Logs:** 180 days
- **Audit Logs:** 1 year

## Performance Monitoring

### Response Time Targets

- **API Endpoints:** p95 < 1s
- **Database Queries:** < 100ms
- **Resume Processing:** < 5min
- **Matching:** < 5min per 100 resumes

### Resource Targets

- **CPU Usage:** < 70% average
- **Memory Usage:** < 80% average
- **Disk Usage:** < 80% average
- **Network:** Monitor for spikes

## Troubleshooting

### High Error Rate

1. Check error logs
2. Review recent changes
3. Check dependent services
4. Scale if needed

### High Response Time

1. Check database performance
2. Review slow queries
3. Check queue length
4. Optimize if needed

### Resource Exhaustion

1. Check resource usage
2. Scale horizontally
3. Optimize application
4. Review resource limits

## See Also

- [Operations README](./README.md)
- [Deployment Guide](./deployment.md)

