#!/bin/bash

echo "=== Grafana Diagnostic ==="

# 1. Check if Grafana is running
echo "1. Checking Grafana pod..."
kubectl get pods -n monitoring -l app=grafana

# 2. Check Grafana logs
echo -e "\n2. Checking Grafana logs..."
GRAFANA_POD=$(kubectl get pods -n monitoring -l app=grafana -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n monitoring $GRAFANA_POD --tail=20

# 3. Check service
echo -e "\n3. Checking Grafana service..."
kubectl get svc -n monitoring grafana-service

# 4. Try to access directly in the pod
echo -e "\n4. Testing Grafana inside pod..."
kubectl exec -n monitoring $GRAFANA_POD -- curl -s http://localhost:3000 | grep -i "grafana\|title"

# 5. Check if it's a port issue
echo -e "\n5. Checking all NodePort services..."
minikube service list