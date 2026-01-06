#!/bin/bash

echo "=== Deploying Heart Disease Prediction API ==="

# 1. Build Docker image
echo "Building Docker image..."
docker build -t cardio-app:latest .

# 2. Load image to Minikube
echo "Loading image to Minikube..."
minikube image load cardio-app:latest

# 3. Deploy application
echo "Deploying application..."
kubectl apply -f k8s-deployment.yaml

# 4. Deploy monitoring stack
echo "Deploying monitoring stack..."
kubectl apply -f monitoring-stack.yaml

# 5. Wait for deployment
echo "Waiting for pods to be ready..."
sleep 30

# 6. Check status
echo "=== Deployment Status ==="
kubectl get pods -o wide
kubectl get svc

echo -e "\n=== Access URLs ==="
MINIKUBE_IP=$(minikube ip)
echo "Application: http://$MINIKUBE_IP:30007"
echo "Grafana: http://$MINIKUBE_IP:30300 (admin/admin123)"
echo "Prometheus: http://$MINIKUBE_IP:30090"