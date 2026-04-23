"""
SHAP Explainer

SHAP (SHapley Additive exPlanations) implementation.
"""

import logging
import uuid
from typing import Any

import numpy as np
import pandas as pd

from .explainer import (
    BaseExplainer,
    ExplanationType,
    FeatureContribution,
    PredictionExplanation,
)

logger = logging.getLogger(__name__)


class SHAPExplainer(BaseExplainer):
    """
    SHAP-based model explainer.
    
    Provides:
    - Local explanations (individual predictions)
    - Global feature importance
    - Interaction effects
    """

    def __init__(
        self,
        model: Any,
        background_data: pd.DataFrame | np.ndarray | None = None,
        algorithm: str = "auto"
    ):
        self.model = model
        self.background_data = background_data
        self.algorithm = algorithm
        self._explainer = None

        self._initialize_explainer()

    def _initialize_explainer(self):
        """Initialize SHAP explainer"""
        try:
            import shap

            if self.algorithm == "auto":
                # Auto-detect best explainer
                if hasattr(self.model, "predict_proba"):
                    # Tree-based or general model
                    try:
                        self._explainer = shap.TreeExplainer(self.model)
                        logger.info("Using SHAP TreeExplainer")
                    except Exception:
                        if self.background_data is not None:
                            self._explainer = shap.KernelExplainer(
                                self.model.predict_proba if hasattr(self.model, "predict_proba") else self.model.predict,
                                self.background_data
                            )
                            logger.info("Using SHAP KernelExplainer")
                elif self.background_data is not None:
                    self._explainer = shap.KernelExplainer(
                        self.model.predict,
                        self.background_data
                    )
                    logger.info("Using SHAP KernelExplainer")
            elif self.algorithm == "tree":
                self._explainer = shap.TreeExplainer(self.model)
            elif self.algorithm == "kernel":
                self._explainer = shap.KernelExplainer(
                    self.model.predict,
                    self.background_data
                )
            elif self.algorithm == "deep":
                self._explainer = shap.DeepExplainer(
                    self.model,
                    self.background_data
                )
        except ImportError:
            logger.error("SHAP not installed. Install with: pip install shap")
            raise
        except Exception as e:
            logger.warning(f"Could not initialize SHAP explainer: {e}")

    def explain_prediction(
        self,
        model: Any,
        instance: dict | pd.Series | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> PredictionExplanation:
        """Explain a single prediction using SHAP"""
        # Convert instance to numpy array
        if isinstance(instance, dict):
            instance_array = np.array([instance[f] for f in feature_names]).reshape(1, -1)
            instance_values = list(instance.values())
        elif isinstance(instance, pd.Series):
            instance_array = instance.values.reshape(1, -1)
            instance_values = instance.values.tolist()
        else:
            instance_array = instance.reshape(1, -1) if len(instance.shape) == 1 else instance
            instance_values = instance.flatten().tolist()

        try:

            if self._explainer is not None:
                shap_values = self._explainer.shap_values(instance_array)

                # Handle different SHAP value formats
                if isinstance(shap_values, list):
                    # Multi-class: take first class or specified class
                    shap_values = shap_values[kwargs.get("class_index", 1)]

                shap_values = shap_values.flatten()

                # Get expected value (base value)
                if hasattr(self._explainer, "expected_value"):
                    base_value = self._explainer.expected_value
                    if isinstance(base_value, (list, np.ndarray)):
                        base_value = base_value[kwargs.get("class_index", 1)]
                else:
                    base_value = 0.5
            else:
                # Fallback: use permutation importance
                shap_values = self._fallback_shap_values(model, instance_array, feature_names)
                base_value = 0.5

        except Exception as e:
            logger.warning(f"SHAP calculation failed, using fallback: {e}")
            shap_values = self._fallback_shap_values(model, instance_array, feature_names)
            base_value = 0.5

        # Get prediction
        if hasattr(model, "predict_proba"):
            prediction = model.predict_proba(instance_array)[0]
            if len(prediction) > 1:
                prediction_value = float(prediction[1])
            else:
                prediction_value = float(prediction[0])
        else:
            prediction_value = float(model.predict(instance_array)[0])

        # Create feature contributions
        contributions = []
        for i, (feature, value, shap_val) in enumerate(zip(feature_names, instance_values, shap_values, strict=False)):
            contributions.append(FeatureContribution(
                feature=feature,
                value=value,
                contribution=float(shap_val),
                direction="positive" if shap_val > 0 else "negative",
                importance_rank=0  # Will be set later
            ))

        # Sort and set ranks
        contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
        for rank, contrib in enumerate(contributions):
            contrib.importance_rank = rank + 1

        # Get top features
        top_positive = [c.feature for c in contributions if c.contribution > 0][:5]
        top_negative = [c.feature for c in contributions if c.contribution < 0][:5]

        return PredictionExplanation(
            prediction_id=str(uuid.uuid4()),
            model_id="",
            explanation_type=ExplanationType.SHAP,
            base_value=float(base_value),
            prediction_value=prediction_value,
            feature_contributions=contributions,
            top_positive_features=top_positive,
            top_negative_features=top_negative
        )

    def _fallback_shap_values(
        self,
        model: Any,
        instance: np.ndarray,
        feature_names: list[str]
    ) -> np.ndarray:
        """Fallback SHAP-like values using permutation"""
        # Simple permutation-based feature importance
        n_features = len(feature_names)
        base_pred = model.predict(instance)[0] if hasattr(model, "predict") else 0.5

        importance = np.zeros(n_features)

        for i in range(n_features):
            # Perturb feature
            perturbed = instance.copy()
            perturbed[0, i] = 0  # Simple perturbation

            try:
                perturbed_pred = model.predict(perturbed)[0]
                importance[i] = base_pred - perturbed_pred
            except Exception:
                importance[i] = 0

        return importance

    def explain_batch(
        self,
        model: Any,
        instances: pd.DataFrame | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> list[PredictionExplanation]:
        """Explain multiple predictions"""
        explanations = []

        if isinstance(instances, pd.DataFrame):
            for idx, row in instances.iterrows():
                exp = self.explain_prediction(model, row, feature_names, **kwargs)
                explanations.append(exp)
        else:
            for i in range(len(instances)):
                exp = self.explain_prediction(model, instances[i], feature_names, **kwargs)
                explanations.append(exp)

        return explanations

    def get_global_importance(
        self,
        model: Any,
        data: pd.DataFrame | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> dict[str, float]:
        """Get global feature importance using SHAP"""
        try:
            if self._explainer is not None:
                if isinstance(data, pd.DataFrame):
                    data_array = data.values
                else:
                    data_array = data

                # Sample if dataset is large
                if len(data_array) > 1000:
                    indices = np.random.choice(len(data_array), 1000, replace=False)
                    data_array = data_array[indices]

                shap_values = self._explainer.shap_values(data_array)

                if isinstance(shap_values, list):
                    shap_values = shap_values[kwargs.get("class_index", 1)]

                # Mean absolute SHAP value per feature
                importance = np.abs(shap_values).mean(axis=0)

                return {
                    feature: float(imp)
                    for feature, imp in zip(feature_names, importance, strict=False)
                }
        except Exception as e:
            logger.error(f"Failed to compute global SHAP importance: {e}")

        # Fallback
        return {feature: 1.0 / len(feature_names) for feature in feature_names}
