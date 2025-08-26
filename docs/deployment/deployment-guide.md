# Deployment Guide

[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://github.com/mhtalci/ansible_fqcn_converter)

Comprehensive deployment guide for the FQCN Converter in various environments.

## Deployment Overview

The FQCN Converter supports multiple deployment patterns:

- **Standalone Installation**: Direct pip installation
- **Container Deployment**: Docker and Kubernetes
- **Enterprise Deployment**: Scalable, monitored deployments
- **CI/CD Integration**: Automated pipeline integration

## Quick Deployment

### Standalone Installation

```bash
# Production installation
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Verify installation
fqcn-converter --version

# Test functionality
fqcn-converter convert --help
```

### Docker Deployment

```bash
# Build container
docker build -t fqcn-converter:latest .

# Run container
docker run -v /path/to/ansible:/workspace fqcn-converter:latest \
  fqcn-converter convert /workspace
```

## Environment Requirements

### System Requirements

| Component | Minimum | Recommended | Enterprise |
|-----------|---------|-------------|------------|
| **CPU** | 1 core | 2+ cores | 4+ cores |
| **Memory** | 512MB | 1GB | 2GB+ |
| **Storage** | 100MB | 1GB | 10GB+ |
| **Python** | 3.8+ | 3.11+ | 3.11+ |

### Network Requirements

- **Outbound HTTPS**: For GitHub installation
- **Internal Access**: For enterprise features
- **Monitoring Ports**: For metrics collection

## Production Deployment

### Container-Based Deployment

```dockerfile
# Production Dockerfile
FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r fqcn && useradd -r -g fqcn fqcn

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install FQCN Converter
RUN pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Copy configuration
COPY config/ /app/config/

# Set permissions
RUN chown -R fqcn:fqcn /app
USER fqcn

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD fqcn-converter --version || exit 1

# Default command
ENTRYPOINT ["fqcn-converter"]
CMD ["--help"]
```##
# Kubernetes Deployment

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fqcn-converter
  labels:
    name: fqcn-converter

---
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fqcn-config
  namespace: fqcn-converter
data:
  enterprise_config.yml: |
    enterprise:
      organization: "Your Organization"
      compliance_level: "strict"
      audit_logging: true
    
    mappings:
      package: "ansible.builtin.package"
      service: "ansible.builtin.service"
    
    performance:
      max_workers: 4
      memory_limit_mb: 500

---
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fqcn-converter
  namespace: fqcn-converter
  labels:
    app: fqcn-converter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fqcn-converter
  template:
    metadata:
      labels:
        app: fqcn-converter
    spec:
      containers:
      - name: fqcn-converter
        image: fqcn-converter:latest
        ports:
        - containerPort: 8080
        env:
        - name: FQCN_CONFIG_PATH
          value: "/config/enterprise_config.yml"
        - name: FQCN_LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: config-volume
          mountPath: /config
        - name: workspace
          mountPath: /workspace
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - fqcn-converter
            - --version
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - fqcn-converter
            - --version
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: fqcn-config
      - name: workspace
        persistentVolumeClaim:
          claimName: fqcn-workspace-pvc

---
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fqcn-converter-service
  namespace: fqcn-converter
spec:
  selector:
    app: fqcn-converter
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```### Doc
ker Compose Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  fqcn-converter:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fqcn-converter
    environment:
      - FQCN_CONFIG_PATH=/config/enterprise_config.yml
      - FQCN_LOG_LEVEL=INFO
      - FQCN_AUDIT_ENABLED=true
    volumes:
      - ./config:/config:ro
      - ./workspace:/workspace
      - ./logs:/var/log/fqcn
    networks:
      - fqcn-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "fqcn-converter", "--version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  fqcn-web:
    build:
      context: .
      dockerfile: Dockerfile.web
    container_name: fqcn-web
    ports:
      - "8080:8080"
    environment:
      - FQCN_CONVERTER_URL=http://fqcn-converter:8080
    depends_on:
      - fqcn-converter
    networks:
      - fqcn-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: fqcn-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - fqcn-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: fqcn-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - fqcn-network
    restart: unless-stopped

networks:
  fqcn-network:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

## Enterprise Deployment

### High Availability Setup

```yaml
# kubernetes/ha-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fqcn-converter-ha
  namespace: fqcn-converter
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
  selector:
    matchLabels:
      app: fqcn-converter
      tier: production
  template:
    metadata:
      labels:
        app: fqcn-converter
        tier: production
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - fqcn-converter
              topologyKey: kubernetes.io/hostname
      containers:
      - name: fqcn-converter
        image: fqcn-converter:latest
        ports:
        - containerPort: 8080
        env:
        - name: FQCN_CONFIG_PATH
          value: "/config/enterprise_config.yml"
        - name: FQCN_WORKERS
          value: "8"
        - name: FQCN_MEMORY_LIMIT
          value: "1000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: config-volume
          mountPath: /config
        - name: shared-storage
          mountPath: /workspace
      volumes:
      - name: config-volume
        configMap:
          name: fqcn-enterprise-config
      - name: shared-storage
        persistentVolumeClaim:
          claimName: fqcn-shared-pvc

---
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fqcn-converter-hpa
  namespace: fqcn-converter
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fqcn-converter-ha
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```#
## Load Balancer Configuration

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fqcn-converter-ingress
  namespace: fqcn-converter
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - fqcn.company.com
    secretName: fqcn-tls-secret
  rules:
  - host: fqcn.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fqcn-converter-service
            port:
              number: 80
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "fqcn_rules.yml"

scrape_configs:
  - job_name: 'fqcn-converter'
    static_configs:
      - targets: ['fqcn-converter:8080']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - fqcn-converter
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "FQCN Converter Metrics",
    "tags": ["fqcn", "ansible"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Conversion Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(fqcn_conversions_total[5m])",
            "legendFormat": "Conversions/sec"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "ops"
          }
        }
      },
      {
        "id": 2,
        "title": "Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(fqcn_conversions_successful[5m]) / rate(fqcn_conversions_total[5m]) * 100",
            "legendFormat": "Success %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100
          }
        }
      },
      {
        "id": 3,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "fqcn_memory_usage_bytes",
            "legendFormat": "Memory Usage"
          }
        ],
        "yAxes": [
          {
            "unit": "bytes"
          }
        ]
      },
      {
        "id": 4,
        "title": "Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(fqcn_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(fqcn_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "unit": "s"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## Security Configuration

### Network Security

```yaml
# kubernetes/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fqcn-converter-netpol
  namespace: fqcn-converter
spec:
  podSelector:
    matchLabels:
      app: fqcn-converter
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: fqcn-web
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS outbound
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

### RBAC Configuration

```yaml
# kubernetes/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fqcn-converter-sa
  namespace: fqcn-converter

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: fqcn-converter-role
  namespace: fqcn-converter
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: fqcn-converter-rolebinding
  namespace: fqcn-converter
subjects:
- kind: ServiceAccount
  name: fqcn-converter-sa
  namespace: fqcn-converter
roleRef:
  kind: Role
  name: fqcn-converter-role
  apiGroup: rbac.authorization.k8s.io
```## CI
/CD Integration

### GitHub Actions Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy FQCN Converter

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    
    steps:
    - name: Deploy to Staging
      run: |
        # Update Kubernetes deployment
        kubectl set image deployment/fqcn-converter-staging \
          fqcn-converter=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:main \
          --namespace=fqcn-staging
        
        # Wait for rollout
        kubectl rollout status deployment/fqcn-converter-staging \
          --namespace=fqcn-staging --timeout=300s

  deploy-production:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    environment: production
    
    steps:
    - name: Deploy to Production
      run: |
        # Update production deployment
        kubectl set image deployment/fqcn-converter-ha \
          fqcn-converter=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }} \
          --namespace=fqcn-converter
        
        # Wait for rollout
        kubectl rollout status deployment/fqcn-converter-ha \
          --namespace=fqcn-converter --timeout=600s
        
        # Run smoke tests
        kubectl run smoke-test --rm -i --restart=Never \
          --image=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }} \
          --namespace=fqcn-converter \
          -- fqcn-converter --version
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'fqcn-converter'
        KUBECONFIG = credentials('kubeconfig')
    }
    
    stages {
        stage('Build') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}")
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}").inside {
                        sh 'fqcn-converter --version'
                        sh 'python -m pytest tests/'
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    sh """
                        kubectl set image deployment/fqcn-converter-staging \\
                            fqcn-converter=${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} \\
                            --namespace=fqcn-staging
                        
                        kubectl rollout status deployment/fqcn-converter-staging \\
                            --namespace=fqcn-staging --timeout=300s
                    """
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                script {
                    sh """
                        kubectl set image deployment/fqcn-converter-ha \\
                            fqcn-converter=${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} \\
                            --namespace=fqcn-converter
                        
                        kubectl rollout status deployment/fqcn-converter-ha \\
                            --namespace=fqcn-converter --timeout=600s
                    """
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            slackSend(
                channel: '#deployments',
                color: 'good',
                message: "✅ FQCN Converter deployed successfully - Build ${BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                channel: '#deployments',
                color: 'danger',
                message: "❌ FQCN Converter deployment failed - Build ${BUILD_NUMBER}"
            )
        }
    }
}
```

## Backup and Recovery

### Data Backup Strategy

```bash
#!/bin/bash
# backup-fqcn-data.sh

BACKUP_DIR="/backup/fqcn-converter"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Backup configuration
kubectl get configmaps -n fqcn-converter -o yaml > "${BACKUP_PATH}/configmaps.yaml"
kubectl get secrets -n fqcn-converter -o yaml > "${BACKUP_PATH}/secrets.yaml"

# Backup persistent volumes
kubectl get pvc -n fqcn-converter -o yaml > "${BACKUP_PATH}/pvc.yaml"

# Backup application state
rsync -av /var/lib/fqcn-converter/ "${BACKUP_PATH}/app-data/"

# Create archive
tar -czf "${BACKUP_DIR}/fqcn-backup-${TIMESTAMP}.tar.gz" -C "${BACKUP_DIR}" "backup_${TIMESTAMP}"

# Clean up old backups (keep last 30 days)
find "${BACKUP_DIR}" -name "fqcn-backup-*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_DIR}/fqcn-backup-${TIMESTAMP}.tar.gz"
```

### Disaster Recovery

```bash
#!/bin/bash
# restore-fqcn-data.sh

BACKUP_FILE="$1"
RESTORE_DIR="/tmp/fqcn-restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Extract backup
mkdir -p "${RESTORE_DIR}"
tar -xzf "${BACKUP_FILE}" -C "${RESTORE_DIR}"

# Restore Kubernetes resources
kubectl apply -f "${RESTORE_DIR}"/*/configmaps.yaml
kubectl apply -f "${RESTORE_DIR}"/*/secrets.yaml
kubectl apply -f "${RESTORE_DIR}"/*/pvc.yaml

# Restore application data
rsync -av "${RESTORE_DIR}"/*/app-data/ /var/lib/fqcn-converter/

# Restart deployment
kubectl rollout restart deployment/fqcn-converter-ha -n fqcn-converter

echo "Restore completed from: ${BACKUP_FILE}"
```

## Troubleshooting

### Common Deployment Issues

1. **Container Won't Start**
   ```bash
   # Check logs
   kubectl logs deployment/fqcn-converter -n fqcn-converter
   
   # Check events
   kubectl get events -n fqcn-converter --sort-by='.lastTimestamp'
   ```

2. **Resource Limits**
   ```bash
   # Check resource usage
   kubectl top pods -n fqcn-converter
   
   # Adjust limits
   kubectl patch deployment fqcn-converter -n fqcn-converter -p '{"spec":{"template":{"spec":{"containers":[{"name":"fqcn-converter","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
   ```

3. **Network Issues**
   ```bash
   # Test connectivity
   kubectl exec -it deployment/fqcn-converter -n fqcn-converter -- nslookup kubernetes.default
   
   # Check network policies
   kubectl get networkpolicies -n fqcn-converter
   ```

### Performance Tuning

```yaml
# kubernetes/performance-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fqcn-performance-config
  namespace: fqcn-converter
data:
  performance.yml: |
    performance:
      max_workers: 8
      memory_limit_mb: 1000
      timeout_seconds: 300
      cache_enabled: true
      batch_size: 100
    
    optimization:
      parallel_processing: true
      memory_efficient_mode: true
      fast_yaml_loading: true
```

## Conclusion

This deployment guide covers:

- **Multiple deployment patterns** for different environments
- **Container orchestration** with Kubernetes and Docker Compose
- **Enterprise features** including HA, monitoring, and security
- **CI/CD integration** for automated deployments
- **Backup and recovery** procedures
- **Troubleshooting** common issues

For additional deployment support or custom configurations, please refer to our [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions) or contact our support team.