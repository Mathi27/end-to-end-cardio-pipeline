import pytest
import pandas as pd
import numpy as np
import os
import glob
import mlflow.sklearn
from sklearn.pipeline import Pipeline

# --- FIXTURE: Load the Model Once ---
@pytest.fixture(scope="module")
def model_pipeline():
    # 1. Setup Path (The Fix: Go up one level from 'tests')
    # Get the directory where THIS file (test_model.py) is located
    test_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the project root
    project_root = os.path.dirname(test_dir)
    mlruns_dir = os.path.join(project_root, 'mlruns')
    
    # 2. Find MLmodel file (Deep Search)
    print(f"🔍 Scanning {mlruns_dir} for models...")
    search_pattern = os.path.join(mlruns_dir, "**", "MLmodel")
    found_files = glob.glob(search_pattern, recursive=True)
    
    if not found_files:
        pytest.fail(f"❌ No model found in {mlruns_dir}. Did you download 'mlruns' correctly?")
        
    model_path = os.path.dirname(found_files[0])
    
    # 3. Load
    try:
        model = mlflow.sklearn.load_model(model_path)
        return model
    except Exception as e:
        pytest.fail(f"❌ Failed to load model: {e}")

# --- TEST 1: Check Input Format ---
def test_input_pipeline(model_pipeline):
    """Ensure the pipeline can handle raw data format"""
    # Create a dummy patient (Healthy case)
    input_data = pd.DataFrame([{
        'age': 45, 
        'sex': 0,       # Female
        'cp': 2, 
        'trestbps': 120, 
        'chol': 200, 
        'fbs': 0, 
        'restecg': 0, 
        'thalach': 160, 
        'exang': 0, 
        'oldpeak': 0.0, 
        'slope': 2, 
        'thal': 3
    }])
    
    # Predict
    try:
        prediction = model_pipeline.predict(input_data)
        assert len(prediction) == 1
    except Exception as e:
        pytest.fail(f"Pipeline crashed on valid input: {e}")

# --- TEST 2: Check Output Range ---
def test_prediction_logic(model_pipeline):
    """Ensure risk probability is between 0 and 1"""
    input_data = pd.DataFrame([{
        'age': 60, 'sex': 1, 'cp': 4, 'trestbps': 140, 'chol': 250, 
        'fbs': 1, 'restecg': 1, 'thalach': 130, 'exang': 1, 
        'oldpeak': 1.5, 'slope': 2, 'thal': 7
    }])
    
    prob = model_pipeline.predict_proba(input_data)[0][1]
    
    assert 0.0 <= prob <= 1.0, f"Probability {prob} is out of bounds!"
    assert isinstance(prob, (float, np.float64, np.float32))

# --- TEST 3: Model Type Check ---
def test_pipeline_structure(model_pipeline):
    """Ensure the loaded object is actually a Pipeline"""
    assert isinstance(model_pipeline, Pipeline)