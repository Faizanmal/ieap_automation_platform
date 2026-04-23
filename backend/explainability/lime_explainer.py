"""
LIME Explainer

LIME (Local Interpretable Model-agnostic Explanations) implementation.
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


class LIMEExplainer(BaseExplainer):
    """
    LIME-based model explainer.
    
    Provides local interpretable explanations for any black-box model.
    """

    def __init__(
        self,
        model: Any,
        feature_names: list[str],
        mode: str = "classification",  # "classification" or "regression"
        kernel_width: float = None,
        num_samples: int = 5000
    ):
        self.model = model
        self.feature_names = feature_names
        self.mode = mode
        self.kernel_width = kernel_width
        self.num_samples = num_samples
        self._explainer = None

        self._initialize_explainer()

    def _initialize_explainer(self):
        """Initialize LIME explainer"""
        try:
            import lime
            import lime.lime_tabular

            # We'll create the explainer when we have data
            logger.info("LIME explainer initialized")
        except ImportError:
            logger.error("LIME not installed. Install with: pip install lime")
            raise

    def explain_prediction(
        self,
        model: Any,
        instance: dict | pd.Series | np.ndarray,
        feature_names: list[str],
        training_data: np.ndarray | None = None,
        **kwargs
    ) -> PredictionExplanation:
        """Explain a single prediction using LIME"""
        try:
            import lime.lime_tabular

            # Convert instance to numpy array
            if isinstance(instance, dict):
                instance_array = np.array([instance[f] for f in feature_names])
                instance_values = list(instance.values())
            elif isinstance(instance, pd.Series):
                instance_array = instance.values
                instance_values = instance.values.tolist()
            else:
                instance_array = instance.flatten()
                instance_values = instance.flatten().tolist()

            # Create explainer with training data if available
            if training_data is not None:
                explainer = lime.lime_tabular.LimeTabularExplainer(
                    training_data=training_data,
                    feature_names=feature_names,
                    mode=self.mode,
                    kernel_width=self.kernel_width
                )
            else:
                # Create minimal explainer
                # Use instance as single sample for stats
                explainer = lime.lime_tabular.LimeTabularExplainer(
                    training_data=instance_array.reshape(1, -1),
                    feature_names=feature_names,
                    mode=self.mode
                )

            # Get prediction function
            if self.mode == "classification" and hasattr(model, "predict_proba"):
                predict_fn = model.predict_proba
            else:
                predict_fn = lambda x: model.predict(x).reshape(-1, 1)

            # Generate explanation
            exp = explainer.explain_instance(
                instance_array,
                predict_fn,
                num_features=len(feature_names),
                num_samples=self.num_samples
            )

            # Extract feature contributions
            contributions = []
            feature_weights = dict(exp.as_list())

            for i, feature in enumerate(feature_names):
                # LIME returns feature conditions, need to map to original features
                weight = 0.0
                for key, val in feature_weights.items():
                    if feature in key:
                        weight = val
                        break

                contributions.append(FeatureContribution(
                    feature=feature,
                    value=instance_values[i] if i < len(instance_values) else None,
                    contribution=float(weight),
                    direction="positive" if weight > 0 else "negative",
                    importance_rank=0
                ))

            # Sort and set ranks
            contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
            for rank, contrib in enumerate(contributions):
                contrib.importance_rank = rank + 1

            # Get prediction
            if hasattr(model, "predict_proba"):
                prediction = model.predict_proba(instance_array.reshape(1, -1))[0]
                prediction_value = float(prediction[1]) if len(prediction) > 1 else float(prediction[0])
            else:
                prediction_value = float(model.predict(instance_array.reshape(1, -1))[0])

            # Top features
            top_positive = [c.feature for c in contributions if c.contribution > 0][:5]
            top_negative = [c.feature for c in contributions if c.contribution < 0][:5]

            return PredictionExplanation(
                prediction_id=str(uuid.uuid4()),
                model_id="",
                explanation_type=ExplanationType.LIME,
                base_value=0.5,  # LIME doesn't have explicit base value
                prediction_value=prediction_value,
                feature_contributions=contributions,
                top_positive_features=top_positive,
                top_negative_features=top_negative,
                metadata={"local_score": exp.score if hasattr(exp, "score") else None}
            )

        except Exception as e:
            logger.error(f"LIME explanation failed: {e}")
            # Return empty explanation
            return PredictionExplanation(
                prediction_id=str(uuid.uuid4()),
                model_id="",
                explanation_type=ExplanationType.LIME,
                base_value=0.5,
                prediction_value=0.5,
                feature_contributions=[],
                metadata={"error": str(e)}
            )

    def explain_batch(
        self,
        model: Any,
        instances: pd.DataFrame | np.ndarray,
        feature_names: list[str],
        **kwargs
    ) -> list[PredictionExplanation]:
        """Explain multiple predictions"""
        explanations = []

        # Use instances as training data
        if isinstance(instances, pd.DataFrame):
            training_data = instances.values
        else:
            training_data = instances

        for i in range(len(instances)):
            if isinstance(instances, pd.DataFrame):
                instance = instances.iloc[i]
            else:
                instance = instances[i]

            exp = self.explain_prediction(
                model, instance, feature_names,
                training_data=training_data,
                **kwargs
            )
            explanations.append(exp)

        return explanations

    def get_global_importance(
        self,
        model: Any,
        data: pd.DataFrame | np.ndarray,
        feature_names: list[str],
        sample_size: int = 100,
        **kwargs
    ) -> dict[str, float]:
        """Get global feature importance by aggregating local explanations"""
        if isinstance(data, pd.DataFrame):
            data_array = data.values
        else:
            data_array = data

        # Sample data if large
        if len(data_array) > sample_size:
            indices = np.random.choice(len(data_array), sample_size, replace=False)
            data_array = data_array[indices]

        # Aggregate feature importance from local explanations
        importance_sums = dict.fromkeys(feature_names, 0.0)

        for i in range(len(data_array)):
            try:
                exp = self.explain_prediction(
                    model, data_array[i], feature_names,
                    training_data=data_array
                )

                for contrib in exp.feature_contributions:
                    importance_sums[contrib.feature] += abs(contrib.contribution)
            except Exception as e:
                logger.warning(f"Failed to explain instance {i}: {e}")

        # Average
        n_samples = len(data_array)
        return {
            feature: importance / n_samples
            for feature, importance in importance_sums.items()
        }
