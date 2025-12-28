# 1. Base Image: Use a lightweight Python image
FROM python:3.10-slim

# 2. Set Working Directory
WORKDIR /app

# 3. Copy Requirements first (Leverage Docker Cache)
COPY requirements.txt .

# 4. Install Dependencies
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt
# Ensure Flask is installed (explicitly, just in case it's missing from requirements)
RUN pip install flask

# 5. Copy Application Code & Model
# This copies everything (including mlruns) from your local folder to /app
COPY . .

# 6. Expose Port 5000 (The default Flask port)
EXPOSE 5000

# 7. Define Environment Variable for MLflow
# Ensures the app knows where to look for the 'mlruns' folder inside the container
ENV MLFLOW_TRACKING_URI=file:///app/mlruns

# 8. Run the Application
# We use 'python app.py' to start the server
CMD ["python", "app.py"]
 