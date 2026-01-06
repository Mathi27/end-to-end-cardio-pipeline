#!/bin/bash

echo "=== Complete Monitoring Fix ==="

# 1. Stop everything
kubectl delete -n monitoring --all --wait=false
kubectl delete namespace monitoring --wait=false
sleep 10

# 2. Start fresh with minikube docker
eval $(minikube docker-env 2>/dev/null || true)

# 3. Create namespace
kubectl create namespace monitoring

# 4. Deploy minimal Prometheus
kubectl apply -n monitoring -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.37.0  # Even older version
        args: ["--config.file=/etc/prometheus/prometheus.yml"]
        ports: [{containerPort: 9090}]
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global: {scrape_interval: 15s}
    scrape_configs:
    - job_name: 'prometheus'
      static_configs: [{targets: ['localhost:9090']}]
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
spec:
  type: NodePort
  selector: {app: prometheus}
  ports: [{port: 9090, targetPort: 9090, nodePort: 30090}]
EOF

sleep 15

# 5. Deploy minimal Grafana
kubectl apply -n monitoring -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:9.3.2  # Very stable older version
        ports: [{containerPort: 3000}]
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin123"
        resources:
          requests: {memory: "64Mi", cpu: "50m"}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
spec:
  type: NodePort
  selector: {app: grafana}
  ports: [{port: 3000, targetPort: 3000, nodePort: 30300}]
EOF

echo "Waiting 30 seconds..."
sleep 30

echo -e "\n✅ Done! Check status:"
kubectl get pods -n monitoring
echo -e "\nAccess:"
echo "Grafana: http://$(minikube ip):30300 (admin/admin123)"
echo "Prometheus: http://$(minikube ip):30090"