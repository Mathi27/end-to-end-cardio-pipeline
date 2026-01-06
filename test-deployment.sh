#!/bin/bash

echo "=== Testing Deployment ==="

# Get minikube IP
MINIKUBE_IP=$(minikube ip)

echo "1. Testing API health..."
curl http://$MINIKUBE_IP:30007/health

echo -e "\n\n2. Testing metrics endpoint..."
curl http://$MINIKUBE_IP:30007/metrics | head -20

echo -e "\n\n3. Making a prediction..."
curl -X POST http://$MINIKUBE_IP:30007/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "sex": 1,
    "cp": 0,
    "trestbps": 120,
    "chol": 250,
    "fbs": 0,
    "restecg": 0,
    "thalach": 150,
    "exang": 0,
    "oldpeak": 1.0,
    "slope": 0,
    "ca": 1,
    "thal": 1
  }'

echo -e "\n\n4. Checking Prometheus targets..."
curl http://$MINIKUBE_IP:30090/targets | grep -A5 -B5 "heart-disease-api"

echo -e "\n=== Test Complete ==="