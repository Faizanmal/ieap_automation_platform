"""
Customer Churn Prediction - Model Training Script

This script trains an XGBoost model to predict customer churn with the following features:
- Feature engineering from customer behavior data
- Hyperparameter optimization using GridSearchCV
- Model evaluation with multiple metrics
- Model persistence for deployment
"""

import json
import os
import warnings
from datetime import datetime

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xgboost as xgb
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class ChurnModelTrainer:
    """
    Train and evaluate a customer churn prediction model
    """

    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        self.metrics = {}

    def create_features(self, df):
        """
        Engineer features from raw customer data
        
        Args:
            df: DataFrame with customer information
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()

        # Calculate customer lifetime value
        df["customer_lifetime_value"] = df["tenure"] * df["monthly_charges"]

        # Calculate charge ratio
        df["charge_ratio"] = df["monthly_charges"] / (df["total_charges"] + 1)

        # Tenure categories
        df["tenure_category"] = pd.cut(df["tenure"],
                                       bins=[0, 12, 24, 48, 72],
                                       labels=["0-1yr", "1-2yr", "2-4yr", "4yr+"])
        df["tenure_category"] = df["tenure_category"].astype(str)

        # High value customer flag
        df["is_high_value"] = (df["monthly_charges"] > df["monthly_charges"].quantile(0.75)).astype(int)

        # Service usage score
        service_cols = ["online_security", "online_backup", "device_protection",
                       "tech_support", "streaming_tv", "streaming_movies"]
        if all(col in df.columns for col in service_cols):
            df["service_usage_score"] = df[service_cols].apply(
                lambda x: sum(1 for val in x if val == "Yes"), axis=1
            )

        return df

    def preprocess_data(self, df, fit=True):
        """
        Preprocess data: encode categorical variables and scale features
        
        Args:
            df: Input DataFrame
            fit: Whether to fit encoders/scalers (True for training data)
            
        Returns:
            Preprocessed DataFrame
        """
        df = df.copy()

        # Handle categorical variables
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns

        for col in categorical_cols:
            if col == "churn":  # Target variable
                continue

            if fit:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            elif col in self.label_encoders:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))

        return df

    def train(self, X_train, y_train, optimize=True):
        """
        Train XGBoost model with optional hyperparameter optimization
        
        Args:
            X_train: Training features
            y_train: Training labels
            optimize: Whether to perform hyperparameter tuning
        """
        if optimize:
            print("Performing hyperparameter optimization...")
            param_grid = {
                "max_depth": [3, 5, 7],
                "learning_rate": [0.01, 0.1, 0.2],
                "n_estimators": [100, 200, 300],
                "min_child_weight": [1, 3, 5],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0]
            }

            xgb_model = xgb.XGBClassifier(
                random_state=self.random_state,
                eval_metric="logloss"
            )

            grid_search = GridSearchCV(
                xgb_model,
                param_grid,
                cv=5,
                scoring="roc_auc",
                n_jobs=-1,
                verbose=1
            )

            grid_search.fit(X_train, y_train)
            self.model = grid_search.best_estimator_
            print(f"Best parameters: {grid_search.best_params_}")

        else:
            print("Training with default parameters...")
            self.model = xgb.XGBClassifier(
                max_depth=5,
                learning_rate=0.1,
                n_estimators=200,
                random_state=self.random_state,
                eval_metric="logloss"
            )
            self.model.fit(X_train, y_train)

        # Store feature names
        self.feature_names = X_train.columns.tolist()

    def evaluate(self, X_test, y_test, save_plots=True):
        """
        Evaluate model performance and generate metrics
        
        Args:
            X_test: Test features
            y_test: Test labels
            save_plots: Whether to save visualization plots
            
        Returns:
            Dictionary of metrics
        """
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        # Calculate metrics
        self.metrics = {
            "accuracy": self.model.score(X_test, y_test),
            "roc_auc": roc_auc_score(y_test, y_pred_proba),
            "classification_report": classification_report(y_test, y_pred, output_dict=True)
        }

        print("\n=== Model Performance ===")
        print(f"Accuracy: {self.metrics['accuracy']:.4f}")
        print(f"ROC-AUC: {self.metrics['roc_auc']:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        if save_plots:
            import os
            os.makedirs("models", exist_ok=True)
            self._plot_confusion_matrix(y_test, y_pred)
            self._plot_roc_curve(y_test, y_pred_proba)
            self._plot_feature_importance()

        return self.metrics

    def _plot_confusion_matrix(self, y_true, y_pred):
        """Plot confusion matrix"""
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(y_true, y_pred)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
        plt.title("Confusion Matrix")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.savefig(os.path.join(SCRIPT_DIR, "models", "confusion_matrix.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Confusion matrix saved to models/confusion_matrix.png")

    def _plot_roc_curve(self, y_true, y_pred_proba):
        """Plot ROC curve"""
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {roc_auc_score(y_true, y_pred_proba):.3f})")
        plt.plot([0, 1], [0, 1], "k--", label="Random Classifier")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(SCRIPT_DIR, "models", "roc_curve.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("ROC curve saved to models/roc_curve.png")

    def _plot_feature_importance(self):
        """Plot feature importance"""
        importance_df = pd.DataFrame({
            "feature": self.feature_names,
            "importance": self.model.feature_importances_
        }).sort_values("importance", ascending=False).head(15)

        plt.figure(figsize=(10, 8))
        sns.barplot(data=importance_df, x="importance", y="feature")
        plt.title("Top 15 Feature Importances")
        plt.xlabel("Importance Score")
        plt.tight_layout()
        plt.savefig(os.path.join(SCRIPT_DIR, "models", "feature_importance.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Feature importance plot saved to models/feature_importance.png")

    def save_model(self, model_path="models/churn_model.pkl"):
        """Save trained model and preprocessing objects"""
        import os
        full_model_path = os.path.join(SCRIPT_DIR, model_path)
        os.makedirs(os.path.dirname(full_model_path), exist_ok=True)

        model_artifacts = {
            "model": self.model,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "feature_names": self.feature_names,
            "metrics": self.metrics,
            "trained_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        joblib.dump(model_artifacts, full_model_path)
        print(f"\nModel saved to {model_path}")

        # Save metrics to JSON
        metrics_path = os.path.join(SCRIPT_DIR, "models", "metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(self.metrics, f, indent=4)
        print("Metrics saved to models/metrics.json")


def generate_sample_data(n_samples=5000):
    """
    Generate synthetic customer data for demonstration
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with synthetic customer data
    """
    np.random.seed(42)

    data = {
        "customer_id": [f"CUST_{i:05d}" for i in range(n_samples)],
        "tenure": np.random.randint(1, 72, n_samples),
        "monthly_charges": np.random.uniform(20, 120, n_samples),
        "total_charges": np.random.uniform(100, 8000, n_samples),
        "contract": np.random.choice(["Month-to-month", "One year", "Two year"], n_samples),
        "payment_method": np.random.choice(["Electronic check", "Mailed check", "Bank transfer", "Credit card"], n_samples),
        "internet_service": np.random.choice(["DSL", "Fiber optic", "No"], n_samples),
        "online_security": np.random.choice(["Yes", "No", "No internet service"], n_samples),
        "online_backup": np.random.choice(["Yes", "No", "No internet service"], n_samples),
        "device_protection": np.random.choice(["Yes", "No", "No internet service"], n_samples),
        "tech_support": np.random.choice(["Yes", "No", "No internet service"], n_samples),
        "streaming_tv": np.random.choice(["Yes", "No", "No internet service"], n_samples),
        "streaming_movies": np.random.choice(["Yes", "No", "No internet service"], n_samples),
    }

    df = pd.DataFrame(data)

    # Create churn target with some logic
    churn_prob = (
        (df["tenure"] < 12).astype(int) * 0.3 +
        (df["contract"] == "Month-to-month").astype(int) * 0.25 +
        (df["monthly_charges"] > 80).astype(int) * 0.2 +
        np.random.uniform(0, 0.25, n_samples)
    )

    df["churn"] = (churn_prob > 0.5).astype(int)

    return df


def main():
    """Main training pipeline"""
    print("=== Customer Churn Prediction Model Training ===\n")

    # Generate or load data
    print("Generating sample data...")
    df = generate_sample_data(n_samples=5000)
    df.to_csv(os.path.join(SCRIPT_DIR, "data", "sample_data.csv"), index=False)
    print(f"Data shape: {df.shape}")
    print(f"Churn rate: {df['churn'].mean():.2%}\n")

    # Initialize trainer
    trainer = ChurnModelTrainer()

    # Feature engineering
    print("Engineering features...")
    df = trainer.create_features(df)

    # Prepare data
    X = df.drop(["customer_id", "churn"], axis=1)
    y = df["churn"]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Preprocess
    print("Preprocessing data...")
    X_train = trainer.preprocess_data(X_train, fit=True)
    X_test = trainer.preprocess_data(X_test, fit=False)

    # Train model
    print("\nTraining model...")
    trainer.train(X_train, y_train, optimize=False)  # Set to True for hyperparameter tuning

    # Evaluate
    print("\nEvaluating model...")
    trainer.evaluate(X_test, y_test, save_plots=True)

    # Save model
    trainer.save_model("models/churn_model.pkl")

    print("\n=== Training Complete ===")


if __name__ == "__main__":
    main()
