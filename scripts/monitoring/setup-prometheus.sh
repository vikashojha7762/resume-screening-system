#!/bin/bash

# Prometheus and Grafana Setup Script

set -e

echo "Setting up monitoring stack..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Wait for CRDs to be ready
kubectl wait --for condition=established --timeout=60s crd/prometheuses.monitoring.coreos.com
kubectl wait --for condition=established --timeout=60s crd/servicemonitors.monitoring.coreos.com

# Deploy Prometheus
kubectl apply -f monitoring/prometheus-deployment.yaml

# Deploy Grafana
kubectl apply -f monitoring/grafana-deployment.yaml

# Create ServiceMonitors for application metrics
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-metrics
  namespace: resume-screening
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
EOF

echo "Monitoring stack deployed. Access Grafana at http://grafana.monitoring.svc.cluster.local"

