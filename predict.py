import mlflow.sklearn
import pandas as pd
import os
import glob

# --- 1. SETUP TRACKING & FIND MODEL (The "Deep Search" Logic) ---
current_dir = os.getcwd()
mlruns_dir = os.path.join(current_dir, 'mlruns')

print(f"🔍 Scanning {mlruns_dir} for MLflow models...")

# Find any file named 'MLmodel' recursively
# This bypasses all folder structure issues
search_pattern = os.path.join(mlruns_dir, "**", "MLmodel")
found_files = glob.glob(search_pattern, recursive=True)

if not found_files:
    print("\n❌ CRITICAL ERROR: No 'MLmodel' file found in mlruns.")
    print("   Please check: Did you unzip 'mlruns_backup.zip' correctly?")
    print("   Inside 'mlruns', you should see numbered folders.")
    exit()

# The model path is the *folder* containing the 'MLmodel' file
model_path = os.path.dirname(found_files[0])
print(f"✅ Found model at: {model_path}")

# --- 2. LOAD MODEL ---
try:
    model = mlflow.sklearn.load_model(model_path)
    print("🧠 Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit()

# --- 3. DEFINE NEW PATIENT ---
new_patient = pd.DataFrame([{
    'age': 63, 
    'sex': 1, 
    'cp': 4, 
    'trestbps': 145, 
    'chol': 233, 
    'fbs': 1, 
    'restecg': 0, 
    'thalach': 150, 
    'exang': 0, 
    'oldpeak': 2.3, 
    'slope': 3, 
    'thal': 6
}])

print("-" * 30)
print("🩺 Analyzing Patient Data...")
print(new_patient)

# --- 4. PREDICT ---
prediction = model.predict(new_patient)[0]
probability = model.predict_proba(new_patient)[0][1]

print("-" * 30)
print(f"📊 Risk Probability: {probability:.2%}")

if prediction == 1:
    print("⚠️  Result: HIGH RISK DETECTED")
else:
    print("✅  Result: Patient is Healthy")