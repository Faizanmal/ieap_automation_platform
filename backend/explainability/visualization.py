"""
Explanation Visualization

Generate visualizations for model explanations.
"""

import logging
from typing import Any

from .explainer import PredictionExplanation

logger = logging.getLogger(__name__)


class ExplanationVisualizer:
    """
    Generate visualizations for model explanations.
    
    Supports:
    - Waterfall charts
    - Bar charts
    - Force plots
    - Summary plots
    """

    def __init__(self, theme: str = "light"):
        self.theme = theme
        self.colors = {
            "positive": "#ff6b6b" if theme == "light" else "#ff8787",
            "negative": "#4ecdc4" if theme == "light" else "#63e6be",
            "neutral": "#95a5a6",
            "background": "#ffffff" if theme == "light" else "#1a1a2e",
            "text": "#2c3e50" if theme == "light" else "#e9ecef"
        }

    def generate_waterfall_html(
        self,
        explanation: PredictionExplanation,
        max_features: int = 10,
        width: int = 600,
        height: int = 400
    ) -> str:
        """Generate HTML waterfall chart"""
        contributions = sorted(
            explanation.feature_contributions,
            key=lambda x: abs(x.contribution),
            reverse=True
        )[:max_features]

        # Generate HTML/CSS for waterfall chart
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: {width}px; padding: 20px;">
            <h3 style="color: {self.colors['text']}; margin-bottom: 20px;">
                Prediction Explanation
            </h3>
            <div style="margin-bottom: 10px; color: {self.colors['text']};">
                Base Value: {explanation.base_value:.4f} → 
                Prediction: {explanation.prediction_value:.4f}
            </div>
            <div style="background: {self.colors['background']}; padding: 10px; border-radius: 8px;">
        """

        for contrib in contributions:
            bar_color = self.colors["positive"] if contrib.contribution > 0 else self.colors["negative"]
            bar_width = min(abs(contrib.contribution) * 200, 300)
            direction = "→" if contrib.contribution > 0 else "←"

            html += f"""
                <div style="display: flex; align-items: center; margin: 8px 0;">
                    <div style="width: 150px; text-align: right; padding-right: 10px; 
                                color: {self.colors['text']}; font-size: 12px;">
                        {contrib.feature}
                    </div>
                    <div style="flex: 1; display: flex; align-items: center;">
                        <div style="height: 24px; width: {bar_width}px; 
                                    background: {bar_color}; border-radius: 4px;
                                    display: flex; align-items: center; justify-content: center;">
                            <span style="color: white; font-size: 11px;">
                                {direction} {abs(contrib.contribution):.3f}
                            </span>
                        </div>
                    </div>
                </div>
            """

        html += """
            </div>
            <div style="margin-top: 15px; font-size: 12px; color: #7f8c8d;">
                <span style="display: inline-block; width: 12px; height: 12px; 
                             background: #ff6b6b; margin-right: 5px;"></span> 
                Increases prediction
                <span style="display: inline-block; width: 12px; height: 12px; 
                             background: #4ecdc4; margin-left: 15px; margin-right: 5px;"></span>
                Decreases prediction
            </div>
        </div>
        """

        return html

    def generate_bar_chart_html(
        self,
        explanation: PredictionExplanation,
        max_features: int = 10,
        width: int = 600,
        height: int = 400
    ) -> str:
        """Generate HTML horizontal bar chart"""
        contributions = sorted(
            explanation.feature_contributions,
            key=lambda x: abs(x.contribution),
            reverse=True
        )[:max_features]

        max_val = max(abs(c.contribution) for c in contributions) if contributions else 1

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: {width}px; padding: 20px;">
            <h3 style="color: {self.colors['text']}; margin-bottom: 20px;">
                Feature Importance
            </h3>
            <div style="background: {self.colors['background']}; padding: 15px; border-radius: 8px;">
        """

        for contrib in contributions:
            bar_color = self.colors["positive"] if contrib.contribution > 0 else self.colors["negative"]
            bar_width = (abs(contrib.contribution) / max_val) * 100

            html += f"""
                <div style="display: flex; align-items: center; margin: 10px 0;">
                    <div style="width: 120px; text-align: right; padding-right: 10px; 
                                color: {self.colors['text']}; font-size: 12px; 
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {contrib.feature}
                    </div>
                    <div style="flex: 1; background: #ecf0f1; height: 20px; border-radius: 3px;">
                        <div style="height: 100%; width: {bar_width}%; background: {bar_color}; 
                                    border-radius: 3px; transition: width 0.3s ease;">
                        </div>
                    </div>
                    <div style="width: 60px; text-align: right; padding-left: 10px; 
                                color: {self.colors['text']}; font-size: 11px;">
                        {contrib.contribution:+.3f}
                    </div>
                </div>
            """

        html += """
            </div>
        </div>
        """

        return html

    def generate_summary_text(
        self,
        explanation: PredictionExplanation,
        max_features: int = 3
    ) -> str:
        """Generate text summary of explanation"""
        positive = [c for c in explanation.feature_contributions if c.contribution > 0]
        negative = [c for c in explanation.feature_contributions if c.contribution < 0]

        positive.sort(key=lambda x: x.contribution, reverse=True)
        negative.sort(key=lambda x: x.contribution)

        summary_parts = []

        if positive:
            top_positive = positive[:max_features]
            pos_features = ", ".join(f"'{c.feature}'" for c in top_positive)
            summary_parts.append(f"The prediction was increased by {pos_features}")

        if negative:
            top_negative = negative[:max_features]
            neg_features = ", ".join(f"'{c.feature}'" for c in top_negative)
            summary_parts.append(f"The prediction was decreased by {neg_features}")

        return ". ".join(summary_parts) + "."

    def to_plotly_figure(
        self,
        explanation: PredictionExplanation,
        chart_type: str = "bar",
        max_features: int = 10
    ) -> dict[str, Any]:
        """
        Generate Plotly figure data.
        
        Returns a dict that can be passed to plotly.io.from_json()
        """
        contributions = sorted(
            explanation.feature_contributions,
            key=lambda x: abs(x.contribution),
            reverse=True
        )[:max_features]

        features = [c.feature for c in reversed(contributions)]
        values = [c.contribution for c in reversed(contributions)]
        colors = [
            self.colors["positive"] if v > 0 else self.colors["negative"]
            for v in values
        ]

        if chart_type == "bar":
            figure = {
                "data": [{
                    "type": "bar",
                    "x": values,
                    "y": features,
                    "orientation": "h",
                    "marker": {"color": colors}
                }],
                "layout": {
                    "title": "Feature Contributions",
                    "xaxis": {"title": "Contribution"},
                    "yaxis": {"title": "Feature"},
                    "margin": {"l": 150}
                }
            }
        elif chart_type == "waterfall":
            figure = {
                "data": [{
                    "type": "waterfall",
                    "x": features,
                    "y": values,
                    "connector": {"line": {"color": "#7f8c8d"}}
                }],
                "layout": {
                    "title": "Waterfall Explanation",
                    "yaxis": {"title": "Contribution"}
                }
            }
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")

        return figure
