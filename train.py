import pandas as pd
import os
import mlflow
import mlflow.sklearn
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import urllib.request

# --- CONFIG ---
MLRUNS_DIR = 'mlruns'
os.makedirs(MLRUNS_DIR, exist_ok=True)

# Set MLflow to log locally
mlflow.set_tracking_uri(f"file://{os.path.abspath(MLRUNS_DIR)}")
mlflow.set_experiment("CI_CD_Training_Run")

# --- 1. DATA FAIL-SAFE (Download if missing) ---
# This ensures GitHub Actions has data without you committing CSVs
def get_data():
    print("📥 Acquiring Data...")
    URLS = {
        'processed.cleveland.data': 'https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data',
        'processed.hungarian.data': 'https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.hungarian.data'
    }
    COL_NAMES = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", 
                 "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"]
    
    dfs = []
    for name, url in URLS.items():
        try:
            filename = name.split('/')[-1]
            urllib.request.urlretrieve(url, filename)
            dfs.append(pd.read_csv(filename, names=COL_NAMES, na_values=["?", "-9.0", "-9"]))
        except:
            pass
            
    df = pd.concat(dfs, ignore_index=True)
    # Simple imputation for CI pipeline
    df = df.fillna(method='ffill').fillna(method='bfill')
    df['target'] = df['target'].apply(lambda x: 1 if x > 0 else 0)
    return df

# --- 2. TRAIN ---
def train():
    df = get_data()
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Pipeline
    numeric_features = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']
    categorical_features = ['sex', 'cp', 'fbs', 'restecg', 'exang', 'slope', 'thal']

    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(solver='liblinear'))
    ])

    print("🚀 Starting Training in CI Environment...")
    with mlflow.start_run(run_name="CI_Pipeline_Model"):
        pipeline.fit(X_train, y_train)
        acc = accuracy_score(y_test, pipeline.predict(X_test))
        
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(pipeline, "model")
        print(f"✅ Model Trained. Accuracy: {acc:.2%}")

if __name__ == "__main__":
    train()