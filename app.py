import pandas as pd
import joblib
import os
import mlflow.sklearn
from flask import Flask, request, jsonify, render_template
import glob

# --- CONFIGURATION ---
# Ensure templates folder is recognized
app = Flask(__name__, template_folder='templates')

# --- MODEL LOADING LOGIC ---
def load_model():
    print("🔄 Initializing Model Loading...")
    current_dir = os.getcwd()
    mlruns_dir = os.path.join(current_dir, 'mlruns')
    
    # Search specifically for MLflow models
    search_pattern = os.path.join(mlruns_dir, "**", "MLmodel")
    found_files = glob.glob(search_pattern, recursive=True)
    
    if not found_files:
        print("⚠️  Warning: No model found in 'mlruns'. API will run but predictions will fail.")
        return None

    model_path = os.path.dirname(found_files[0])
    print(f"✅ Found model artifact at: {model_path}")
    
    try:
        loaded_model = mlflow.sklearn.load_model(model_path)
        print("🧠 Model loaded successfully!")
        return loaded_model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

model = load_model()

# --- ROUTES ---

@app.route('/', methods=['GET'])
def index():
    """
    Serves the Frontend Dashboard
    """
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    if model:
        return jsonify({"status": "healthy", "model_loaded": True}), 200
    else:
        return jsonify({"status": "unhealthy", "error": "Model not loaded"}), 503

@app.route('/predict', methods=['POST'])
def predict():
    if not model:
        return jsonify({"error": "Model is not available"}), 503

    try:
        data = request.get_json()
        
        # DataFrame Conversion
        if isinstance(data, dict):
            input_df = pd.DataFrame([data])
        elif isinstance(data, list):
            input_df = pd.DataFrame(data)
        else:
            return jsonify({"error": "Invalid format"}), 400

        # Prediction
        prediction = model.predict(input_df)
        probability = model.predict_proba(input_df)[:, 1]

        results = []
        for pred, prob in zip(prediction, probability):
            results.append({
                "prediction": int(pred),
                "risk_score": float(prob),
                "confidence": f"{prob:.2%}",
                "status": "HIGH RISK" if pred == 1 else "Healthy"
            })

        response = results[0] if len(results) == 1 else results
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)