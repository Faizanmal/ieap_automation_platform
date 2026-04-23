"""
Model Explainer

Unified interface for model explainability.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """Types of explanations"""
    SHAP = "shap"
    LIME = "lime"
    FEATURE_IMPORTANCE = "feature_importance"
    PARTIAL_DEPENDENCE = "partial_dependence"
    COUNTERFACTUAL = "counterfactual"


@dataclass
class FeatureContribution:
    """Individual feature contribution"""
    feature: str
    value: Any
    contribution: float
    direction: str  # "positive" or "negative"
    importance_rank: int
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "value": self.value,
            "contribution": round(self.contribution, 4),
            "direction": self.direction,
            "importance_rank": self.importance_rank,
            "description": self.description
        }


@dataclass
class PredictionExplanation:
    """Complete prediction explanation"""
    prediction_id: str
    model_id: str
    explanation_type: ExplanationType
    base_value: float
    prediction_value: float
    feature_contributions: list[FeatureContribution]
    top_positive_features: list[str] = field(default_factory=list)
    top_negative_features: list[str] = field(default_factory=list)
    confidence: float = 1.0
    computation_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_summary(self) -> str:
        """Get human-readable summary"""
        summary_parts = []

        if self.top_positive_features:
            summary_parts.append(
                f"Top factors increasing prediction: {', '.join(self.top_positive_features[:3])}"
            )

        if self.top_negative_features:
            summary_parts.append(
                f"Top factors decreasing prediction: {', '.join(self.top_negative_features[:3])}"
            )

        return " | ".join(summary_parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "model_id": self.model_id,
            "explanation_type": self.explanation_type.value,
            "base_value": round(self.base_value, 4),
            "prediction_value": round(self.prediction_value, 4),
            "feature_contributions": [fc.to_dict() for fc in self.feature_contributions],
            "top_positive_features": self.top_positive_features,
            "top_negative_features": self.top_negative_features,
            "confidence": round(self.confidence, 4),
            "computation_time_ms": round(self.computation_time_ms, 2),
            "summary": self.get_summary(),
            "timestamp": self.timestamp.isoformat()
        }


class BaseExplainer(ABC):
    """Abstract base class for explainers"""

    @abstractmethod
    def explain_prediction(
        self,
        model: Any,
        instance: dict | pd.Series | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> PredictionExplanation:
        """Explain a single prediction"""

    @abstractmethod
    def explain_batch(
        self,
        model: Any,
        instances: pd.DataFrame | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> list[PredictionExplanation]:
        """Explain multiple predictions"""

    @abstractmethod
    def get_global_importance(
        self,
        model: Any,
        data: pd.DataFrame | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> dict[str, float]:
        """Get global feature importance"""


class ModelExplainer:
    """
    Unified model explainability interface.
    
    Usage:
        explainer = ModelExplainer(model, feature_names=["f1", "f2", "f3"])
        
        # Explain single prediction
        explanation = explainer.explain(instance, method="shap")
        
        # Get global feature importance
        importance = explainer.get_feature_importance(data)
        
        # Generate explanation for API response
        api_response = explainer.explain_for_api(instance)
    """

    def __init__(
        self,
        model: Any,
        feature_names: list[str],
        model_id: str = "unknown",
        background_data: pd.DataFrame | np.ndarray | None = None,
        default_method: ExplanationType = ExplanationType.SHAP
    ):
        self.model = model
        self.feature_names = feature_names
        self.model_id = model_id
        self.background_data = background_data
        self.default_method = default_method

        self._explainers: dict[ExplanationType, BaseExplainer] = {}
        self._initialize_explainers()

    def _initialize_explainers(self):
        """Initialize available explainers"""
        # Import here to avoid circular imports and optional dependencies
        try:
            from .shap_explainer import SHAPExplainer
            self._explainers[ExplanationType.SHAP] = SHAPExplainer(
                self.model,
                self.background_data
            )
        except ImportError:
            logger.warning("SHAP not available")

        try:
            from .lime_explainer import LIMEExplainer
            self._explainers[ExplanationType.LIME] = LIMEExplainer(
                self.model,
                self.feature_names
            )
        except ImportError:
            logger.warning("LIME not available")

    def explain(
        self,
        instance: dict | pd.Series | np.ndarray,
        method: ExplanationType | None = None,
        prediction_id: str | None = None,
        **kwargs
    ) -> PredictionExplanation:
        """
        Explain a prediction.
        
        Args:
            instance: Input data for the prediction
            method: Explanation method to use (default: SHAP)
            prediction_id: Optional ID to associate with explanation
            **kwargs: Additional arguments for the explainer
        
        Returns:
            PredictionExplanation object
        """
        import time
        start_time = time.time()

        method = method or self.default_method

        if method not in self._explainers:
            raise ValueError(f"Explainer {method.value} not available")

        explainer = self._explainers[method]
        explanation = explainer.explain_prediction(
            self.model,
            instance,
            self.feature_names,
            **kwargs
        )

        explanation.prediction_id = prediction_id or f"pred_{id(instance)}"
        explanation.model_id = self.model_id
        explanation.computation_time_ms = (time.time() - start_time) * 1000

        return explanation

    def explain_batch(
        self,
        instances: pd.DataFrame | np.ndarray,
        method: ExplanationType | None = None,
        **kwargs
    ) -> list[PredictionExplanation]:
        """Explain multiple predictions"""
        method = method or self.default_method

        if method not in self._explainers:
            raise ValueError(f"Explainer {method.value} not available")

        explainer = self._explainers[method]
        return explainer.explain_batch(
            self.model,
            instances,
            self.feature_names,
            **kwargs
        )

    def get_feature_importance(
        self,
        data: pd.DataFrame | np.ndarray | None = None,
        method: ExplanationType | None = None,
        **kwargs
    ) -> dict[str, float]:
        """Get global feature importance"""
        data = data if data is not None else self.background_data

        if data is None:
            raise ValueError("No data provided for feature importance calculation")

        method = method or self.default_method

        if method not in self._explainers:
            raise ValueError(f"Explainer {method.value} not available")

        explainer = self._explainers[method]
        return explainer.get_global_importance(
            self.model,
            data,
            self.feature_names,
            **kwargs
        )

    def explain_for_api(
        self,
        instance: dict | pd.Series | np.ndarray,
        method: ExplanationType | None = None,
        include_visualization: bool = False
    ) -> dict[str, Any]:
        """
        Generate explanation formatted for API response.
        
        Returns a dictionary suitable for JSON serialization.
        """
        explanation = self.explain(instance, method)
        result = explanation.to_dict()

        if include_visualization:
            try:
                from .visualization import ExplanationVisualizer
                viz = ExplanationVisualizer()
                result["visualization"] = {
                    "waterfall_html": viz.generate_waterfall_html(explanation),
                    "bar_html": viz.generate_bar_chart_html(explanation)
                }
            except Exception as e:
                logger.warning(f"Failed to generate visualization: {e}")

        return result

    def compare_explanations(
        self,
        instance: dict | pd.Series | np.ndarray,
        methods: list[ExplanationType] | None = None
    ) -> dict[ExplanationType, PredictionExplanation]:
        """
        Compare explanations from different methods.
        
        Useful for validating explanations across methods.
        """
        methods = methods or list(self._explainers.keys())

        results = {}
        for method in methods:
            if method in self._explainers:
                try:
                    results[method] = self.explain(instance, method)
                except Exception as e:
                    logger.error(f"Failed to explain with {method.value}: {e}")

        return results


def get_feature_contribution_summary(
    contributions: list[FeatureContribution],
    top_n: int = 5
) -> dict[str, Any]:
    """
    Get a summary of feature contributions.
    
    Returns the top positive and negative contributors.
    """
    sorted_contributions = sorted(
        contributions,
        key=lambda x: abs(x.contribution),
        reverse=True
    )

    positive = [c for c in sorted_contributions if c.contribution > 0][:top_n]
    negative = [c for c in sorted_contributions if c.contribution < 0][:top_n]

    return {
        "top_positive": [
            {"feature": c.feature, "contribution": c.contribution}
            for c in positive
        ],
        "top_negative": [
            {"feature": c.feature, "contribution": c.contribution}
            for c in negative
        ],
        "total_positive_contribution": sum(c.contribution for c in positive),
        "total_negative_contribution": sum(c.contribution for c in negative)
    }
