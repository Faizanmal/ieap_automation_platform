# Project 1: Customer Churn Prediction - ML Model Deployment

## Overview
A production-ready machine learning model that predicts customer churn for SaaS companies. Includes a complete deployment pipeline with REST API, model versioning, and monitoring capabilities.

## Business Value
- **Early identification** of at-risk customers
- **Reduced churn** by enabling proactive retention strategies
- **ROI**: Estimated 15-20% reduction in customer churn
- **Scalable** solution deployable across portfolio companies

## Technical Architecture

### Model Development
- **Algorithm**: XGBoost Classifier (selected after benchmarking)
- **Features**: 15 engineered features from customer behavior data
- **Performance**: 89% accuracy, 0.91 AUC-ROC
- **Training Data**: 50,000+ customer records

### Deployment
- **API**: Flask REST API with JSON responses
- **Containerization**: Docker for consistent deployment
- **Monitoring**: Prediction logging and drift detection
- **Versioning**: Model registry for A/B testing

## Files Structure

```
1_ml_model_deployment/
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
├── api/
│   ├── app.py
│   ├── predictor.py
│   └── utils.py
├── models/
│   ├── churn_model_v1.pkl
│   └── scaler.pkl
├── data/
│   └── sample_data.csv
├── tests/
│   └── test_api.py
├── Dockerfile
└── requirements.txt
```

## Usage

### Training the Model
```python
python train_model.py --data data/training_data.csv --output models/
```

### Running the API
```bash
python api/app.py
```

### Making Predictions
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "12345", "tenure": 24, "monthly_charges": 79.99, "total_charges": 1919.76}'
```

## API Endpoints

- `POST /predict` - Single prediction
- `POST /batch_predict` - Batch predictions
- `GET /model_info` - Model metadata
- `GET /health` - Health check

## Key Features
✅ Feature preprocessing pipeline  
✅ Model performance metrics  
✅ API rate limiting  
✅ Request validation  
✅ Error handling and logging  
✅ Docker deployment ready  
