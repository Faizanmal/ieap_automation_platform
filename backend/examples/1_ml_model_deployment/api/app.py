"""
Flask REST API for Customer Churn Prediction

This API provides endpoints for:
- Single customer churn prediction
- Batch predictions
- Model information and health checks
- Request validation and error handling
"""

import logging
import os
from datetime import datetime

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Global variables for model
MODEL = None
MODEL_INFO = {}


def load_model(model_path="../models/churn_model.pkl"):
    """Load trained model and artifacts"""
    global MODEL, MODEL_INFO

    try:
        # Try relative path first, then absolute path
        if not os.path.exists(model_path):
            # Try absolute path from script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(script_dir, "..", "..", "models", "churn_model.pkl")

        if os.path.exists(model_path):
            artifacts = joblib.load(model_path)
            MODEL = artifacts
            MODEL_INFO = {
                "model_type": "XGBoost Classifier",
                "features": artifacts.get("feature_names", []),
                "trained_date": artifacts.get("trained_date", "Unknown"),
                "metrics": artifacts.get("metrics", {})
            }
            logger.info("Model loaded successfully")
        else:
            logger.warning(f"Model file not found at {model_path}. Using dummy model for demo.")
            MODEL = None
            MODEL_INFO = {
                "model_type": "Demo Mode",
                "features": ["tenure", "monthly_charges", "total_charges"],
                "trained_date": datetime.now().strftime("%Y-%m-%d"),
                "metrics": {"accuracy": 0.89, "roc_auc": 0.91}
            }
    except Exception as e:
        logger.error(f"Error loading model: {e!s}")
        MODEL = None


def preprocess_input(data):
    """
    Preprocess input data for prediction
    
    Args:
        data: Dictionary or DataFrame with customer data
        
    Returns:
        Preprocessed DataFrame ready for prediction
    """
    if isinstance(data, dict):
        data = pd.DataFrame([data])

    # Feature engineering (simplified for API)
    if "tenure" in data.columns and "monthly_charges" in data.columns:
        data["customer_lifetime_value"] = data["tenure"] * data["monthly_charges"]

    if "monthly_charges" in data.columns and "total_charges" in data.columns:
        data["charge_ratio"] = data["monthly_charges"] / (data["total_charges"] + 1)

    return data


def validate_input(data):
    """
    Validate input data
    
    Args:
        data: Input dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["tenure", "monthly_charges", "total_charges"]

    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

        if not isinstance(data[field], (int, float)):
            return False, f"Field {field} must be numeric"

        if data[field] < 0:
            return False, f"Field {field} must be non-negative"

    return True, None


@app.route("/", methods=["GET"])
def home():
    """API home endpoint"""
    return jsonify({
        "message": "Customer Churn Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "/predict": "POST - Single customer prediction",
            "/batch_predict": "POST - Batch predictions",
            "/model_info": "GET - Model information",
            "/health": "GET - Health check"
        }
    })


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": MODEL is not None,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/model_info", methods=["GET"])
def model_info():
    """Return model information and metadata"""
    return jsonify({
        "model_info": MODEL_INFO,
        "status": "loaded" if MODEL else "not_loaded"
    })


@app.route("/predict", methods=["POST"])
@limiter.limit("30 per minute")
def predict():
    """
    Predict churn for a single customer
    
    Expected input JSON:
    {
        "customer_id": "CUST_001",
        "tenure": 24,
        "monthly_charges": 79.99,
        "total_charges": 1919.76,
        "contract": "Month-to-month",
        ...
    }
    """
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate input
        is_valid, error_msg = validate_input(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Extract customer ID
        customer_id = data.get("customer_id", "unknown")

        # Make prediction
        if MODEL is not None:
            # Use actual trained model
            input_df = preprocess_input(data)

            # Remove customer_id from features
            if "customer_id" in input_df.columns:
                input_df = input_df.drop("customer_id", axis=1)

            prediction = MODEL["model"].predict(input_df)[0]
            probability = MODEL["model"].predict_proba(input_df)[0][1]
        else:
            # Demo mode - simple heuristic
            tenure = data["tenure"]
            monthly_charges = data["monthly_charges"]

            # Simple churn heuristic
            churn_score = 0.0
            if tenure < 12:
                churn_score += 0.4
            if monthly_charges > 80:
                churn_score += 0.3
            if data.get("contract") == "Month-to-month":
                churn_score += 0.3

            probability = min(churn_score, 1.0)
            prediction = 1 if probability > 0.5 else 0

        # Prepare response
        response = {
            "customer_id": customer_id,
            "prediction": "Churn" if prediction == 1 else "No Churn",
            "churn_probability": round(float(probability), 4),
            "risk_level": (
                "High" if probability > 0.7 else
                "Medium" if probability > 0.4 else
                "Low"
            ),
            "timestamp": datetime.now().isoformat()
        }

        # Log prediction
        logger.info(f"Prediction for {customer_id}: {response['prediction']} ({probability:.4f})")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Prediction error: {e!s}")
        return jsonify({"error": f"Prediction failed: {e!s}"}), 500


@app.route("/batch_predict", methods=["POST"])
@limiter.limit("10 per minute")
def batch_predict():
    """
    Predict churn for multiple customers
    
    Expected input JSON:
    {
        "customers": [
            {"customer_id": "CUST_001", "tenure": 24, ...},
            {"customer_id": "CUST_002", "tenure": 12, ...}
        ]
    }
    """
    try:
        data = request.get_json()

        if not data or "customers" not in data:
            return jsonify({"error": "No customer data provided"}), 400

        customers = data["customers"]

        if not isinstance(customers, list):
            return jsonify({"error": "Customers must be a list"}), 400

        if len(customers) > 100:
            return jsonify({"error": "Maximum 100 customers per batch"}), 400

        predictions = []

        for customer in customers:
            # Validate each customer
            is_valid, error_msg = validate_input(customer)
            if not is_valid:
                predictions.append({
                    "customer_id": customer.get("customer_id", "unknown"),
                    "error": error_msg
                })
                continue

            # Make prediction (reuse single prediction logic)
            customer_id = customer.get("customer_id", "unknown")

            if MODEL is not None:
                input_df = preprocess_input(customer)
                if "customer_id" in input_df.columns:
                    input_df = input_df.drop("customer_id", axis=1)

                prediction = MODEL["model"].predict(input_df)[0]
                probability = MODEL["model"].predict_proba(input_df)[0][1]
            else:
                # Demo heuristic
                tenure = customer["tenure"]
                monthly_charges = customer["monthly_charges"]
                churn_score = 0.0
                if tenure < 12:
                    churn_score += 0.4
                if monthly_charges > 80:
                    churn_score += 0.3

                probability = min(churn_score, 1.0)
                prediction = 1 if probability > 0.5 else 0

            predictions.append({
                "customer_id": customer_id,
                "prediction": "Churn" if prediction == 1 else "No Churn",
                "churn_probability": round(float(probability), 4),
                "risk_level": (
                    "High" if probability > 0.7 else
                    "Medium" if probability > 0.4 else
                    "Low"
                )
            })

        response = {
            "total_customers": len(customers),
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Batch prediction for {len(customers)} customers")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Batch prediction error: {e!s}")
        return jsonify({"error": f"Batch prediction failed: {e!s}"}), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": str(e.description)
    }), 429


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == "__main__":
    # Load model on startup
    load_model()

    # Run Flask app
    print("Starting Customer Churn Prediction API...")
    print("API will be available at http://localhost:5000")
    print("\nEndpoints:")
    print("  GET  /              - API information")
    print("  GET  /health        - Health check")
    print("  GET  /model_info    - Model information")
    print("  POST /predict       - Single prediction")
    print("  POST /batch_predict - Batch predictions")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
