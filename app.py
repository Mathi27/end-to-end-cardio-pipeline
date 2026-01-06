import pandas as pd
import joblib
import os
import mlflow.sklearn
from flask import Flask, request, jsonify, render_template
import glob
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import time
from datetime import datetime

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- PROMETHEUS METRICS ---
REQUEST_COUNT = Counter(
    'flask_app_request_count', 
    'Total Request Count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'flask_app_request_latency_seconds', 
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

PREDICTION_COUNT = Counter(
    'heart_api_predictions_total',
    'Total number of prediction requests',
    ['status', 'risk_level']
)

PREDICTION_LATENCY = Histogram(
    'heart_api_prediction_latency_seconds',
    'Prediction processing latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2]
)

ACTIVE_REQUESTS = Gauge(
    'heart_api_active_requests',
    'Number of active requests being processed'
)

MODEL_LOAD_STATUS = Gauge(
    'heart_api_model_load_status',
    'Model load status (1=loaded, 0=not loaded)'
)

HEALTH_STATUS = Gauge(
    'heart_api_health_status',
    'API health status (1=healthy, 0=unhealthy)'
)

# --- CONFIGURATION ---
app = Flask(__name__, template_folder='templates')

# --- MODEL LOADING LOGIC ---
def load_model():
    logger.info("🔄 Initializing Model Loading...")
    current_dir = os.getcwd()
    mlruns_dir = os.path.join(current_dir, 'mlruns')
    
    # Search specifically for MLflow models
    search_pattern = os.path.join(mlruns_dir, "**", "MLmodel")
    found_files = glob.glob(search_pattern, recursive=True)
    
    if not found_files:
        logger.warning("⚠️ Warning: No model found in 'mlruns'. API will run but predictions will fail.")
        MODEL_LOAD_STATUS.set(0)
        return None

    model_path = os.path.dirname(found_files[0])
    logger.info(f"✅ Found model artifact at: {model_path}")
    
    try:
        loaded_model = mlflow.sklearn.load_model(model_path)
        logger.info("🧠 Model loaded successfully!")
        MODEL_LOAD_STATUS.set(1)
        return loaded_model
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        MODEL_LOAD_STATUS.set(0)
        return None

model = load_model()

# --- ROUTES ---

@app.before_request
def start_timer():
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()

@app.after_request
def log_request(response):
    latency = time.time() - request.start_time
    ACTIVE_REQUESTS.dec()
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        http_status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    
    logger.info(
        f"{datetime.now().isoformat()} - "
        f"Method: {request.method} "
        f"Path: {request.path} "
        f"Status: {response.status_code} "
        f"Latency: {latency:.4f}s"
    )
    return response

@app.route('/')
def index():
    """Serves the Frontend Dashboard"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    if model:
        HEALTH_STATUS.set(1)
        return jsonify({
            "status": "healthy", 
            "model_loaded": True,
            "timestamp": datetime.now().isoformat()
        }), 200
    else:
        HEALTH_STATUS.set(0)
        return jsonify({
            "status": "unhealthy", 
            "error": "Model not loaded",
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route('/predict', methods=['POST'])
def predict():
    """Prediction endpoint with metrics tracking"""
    start_time = time.time()
    
    if not model:
        PREDICTION_COUNT.labels(status='failed', risk_level='unknown').inc()
        return jsonify({"error": "Model is not available"}), 503

    try:
        data = request.get_json()
        
        # DataFrame Conversion
        if isinstance(data, dict):
            input_df = pd.DataFrame([data])
        elif isinstance(data, list):
            input_df = pd.DataFrame(data)
        else:
            PREDICTION_COUNT.labels(status='failed', risk_level='unknown').inc()
            return jsonify({"error": "Invalid format"}), 400

        # Prediction
        prediction = model.predict(input_df)
        probability = model.predict_proba(input_df)[:, 1]
        
        # Calculate prediction latency
        prediction_latency = time.time() - start_time
        PREDICTION_LATENCY.observe(prediction_latency)

        results = []
        for pred, prob in zip(prediction, probability):
            risk_level = "high" if pred == 1 else "low"
            PREDICTION_COUNT.labels(status='success', risk_level=risk_level).inc()
            
            results.append({
                "prediction": int(pred),
                "risk_score": float(prob),
                "confidence": f"{prob:.2%}",
                "status": "HIGH RISK" if pred == 1 else "Healthy",
                "risk_level": risk_level,
                "prediction_latency": f"{prediction_latency:.4f}s",
                "timestamp": datetime.now().isoformat()
            })

        response = results[0] if len(results) == 1 else results
        return jsonify(response)

    except Exception as e:
        PREDICTION_COUNT.labels(status='failed', risk_level='unknown').inc()
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Metrics dashboard page"""
    metrics_data = {
        "model_loaded": MODEL_LOAD_STATUS._value.get(),
        "active_requests": ACTIVE_REQUESTS._value.get(),
        "health_status": HEALTH_STATUS._value.get()
    }
    return render_template('dashboard.html', metrics=metrics_data)

if __name__ == '__main__':
    # Add Prometheus WSGI middleware to Flask
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })
    
    logger.info("🚀 Starting Heart Disease API with Prometheus metrics...")
    logger.info("📊 Metrics available at: http://localhost:5000/metrics")
    logger.info("📈 Dashboard available at: http://localhost:5000/dashboard")
    logger.info("🏥 Health check at: http://localhost:5000/health")
    
    app.run(host='0.0.0.0', port=5000, debug=False)