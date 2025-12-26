# BITS Group 120 | MLops

## Heart Disease Risk Prediction: End-to-End MLOps System

## Project Overview

This project implements a robust Machine Learning pipeline to predict the presence of heart disease in patients. Unlike standard experiments that rely solely on the Cleveland dataset (303 records), this solution aggregates and harmonizes data from four major international databases (Cleveland, Hungary, Switzerland, and Long Beach VA), resulting in a comprehensive dataset of 920 patients.

The final model, a tuned Logistic Regression classifier, achieves a ROC-AUC of 0.91 and Accuracy of 83.2% on a strictly held-out test set, successfully outperforming ensemble methods like Random Forest due to the linear nature of the risk factors.

## Project Structure
`
heart-disease-prediction/
│
├── data/
│   ├── 01_raw/                  # Raw data downloaded from UCI
│   ├── 02_processed/            # Cleaned & merged CSV (920 rows)
│   └── 03_model_input/          # Train/Test split CSVs (Leakage prevention)
│
├── notebooks/
│   ├── 01_data_acquisition.ipynb   # Downloads, merges, and cleans the 4 datasets
│   ├── 02_eda.ipynb                # Visualizations & Statistical Analysis
│   ├── 03_feature_engineering.ipynb# Stratified Splitting & Pipeline prep
│   └── 04_model_experiments.ipynb  # Training, Tuning, and Evaluation
│
├── models/
│   └── heart_disease_model.joblib  # Serialized model ready for deployment
│
├── reports/
│   └── figures/                 # Generated charts (Confusion Matrix, ROC, etc.)
│
└── README.md
`

## Key Results

We benchmarked a linear model against a non-linear ensemble method using Stratified 5-Fold Cross-Validation.

| Model | Test ROC-AUC | Test Accuracy | Verdict |
| :--- | :--- | :--- | :--- |
| **Logistic Regression** | **0.911** | **83.2%** | **🏆 Selected** (Better generalization) |
| Random Forest | 0.877 | 81.0% | Slightly overfit to noise |

*Business Insight:* The superior performance of the linear model suggests that heart disease risk factors (like Age, Max Heart Rate, and Cholesterol) have a strong additive relationship in this population

## Medical Insights & Interpretability

Our analysis confirmed critical cardiological markers, ensuring the model is "White Box" and interpretable by doctors:

Asymptomatic Chest Pain (cp=4): The single strongest predictor of disease presence.

Max Heart Rate (thalach): Shows a strong negative correlation. Patients unable to achieve high heart rates during stress tests are at significant risk.

ST Depression (oldpeak): A critical EKG marker indicating oxygen deprivation during exercise.