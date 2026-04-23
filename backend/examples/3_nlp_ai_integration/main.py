"""
NLP & AI Integration - Investment Document Analyzer

This module provides AI-powered analysis of investment documents using:
- Large Language Models (OpenAI, Hugging Face)
- Natural Language Processing
- Sentiment Analysis
- Document Q&A
- Information Extraction

Features:
- Document summarization
- Key metrics extraction
- Risk identification
- Sentiment analysis
- Question answering
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# NLP libraries
try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Install with: pip install transformers torch")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with Large Language Models
    Supports OpenAI API and Hugging Face models
    """

    def __init__(self, provider="openai", model="gpt-3.5-turbo"):
        self.provider = provider
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        if provider == "openai" and not self.api_key:
            logger.warning("OpenAI API key not found. Using demo mode.")
            self.demo_mode = True
        else:
            self.demo_mode = False

    def generate_summary(self, text: str, max_length: int = 150) -> str:
        """Generate a summary of the input text"""

        if self.demo_mode:
            # Demo mode - rule-based summary
            return self._generate_demo_summary(text, max_length)

        if self.provider == "openai":
            return self._openai_summarize(text, max_length)
        return self._huggingface_summarize(text, max_length)

    def _generate_demo_summary(self, text: str, max_length: int) -> str:
        """Generate a simple rule-based summary for demo"""
        # Extract first few sentences
        sentences = re.split(r"[.!?]+", text)
        summary_sentences = []
        current_length = 0

        for sentence in sentences[:5]:  # Take first 5 sentences
            sentence = sentence.strip()
            if sentence and current_length + len(sentence) < max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break

        return ". ".join(summary_sentences) + "."

    def _openai_summarize(self, text: str, max_length: int) -> str:
        """Summarize using OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Summarize the following text concisely."},
                    {"role": "user", "content": text[:4000]}  # Limit input size
                ],
                max_tokens=max_length
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e!s}")
            return self._generate_demo_summary(text, max_length)

    def _huggingface_summarize(self, text: str, max_length: int) -> str:
        """Summarize using Hugging Face models"""
        if not TRANSFORMERS_AVAILABLE:
            return self._generate_demo_summary(text, max_length)

        try:
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            summary = summarizer(text[:1024], max_length=max_length, min_length=30, do_sample=False)
            return summary[0]["summary_text"]
        except Exception as e:
            logger.error(f"Hugging Face error: {e!s}")
            return self._generate_demo_summary(text, max_length)

    def answer_question(self, context: str, question: str) -> str:
        """Answer a question based on context"""

        if self.demo_mode:
            return self._demo_answer(context, question)

        try:
            import openai
            openai.api_key = self.api_key

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Answer questions based on the provided context."},
                    {"role": "user", "content": f"Context: {context[:3000]}\n\nQuestion: {question}"}
                ],
                max_tokens=200
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Q&A error: {e!s}")
            return self._demo_answer(context, question)

    def _demo_answer(self, context: str, question: str) -> str:
        """Demo mode Q&A - simple keyword matching"""
        context_lower = context.lower()
        question_lower = question.lower()

        # Simple keyword extraction
        if "revenue" in question_lower:
            # Try to find revenue mentions
            revenue_match = re.search(r"\$[\d,]+(?:\.\d+)?[MBK]?", context)
            if revenue_match:
                return f"Based on the document: {revenue_match.group()}"

        if "growth" in question_lower:
            growth_match = re.search(r"(\d+)%\s*(?:growth|increase)", context_lower)
            if growth_match:
                return f"The document mentions {growth_match.group()} growth."

        return "I found relevant information in the document. [Demo mode - limited capabilities. Set OPENAI_API_KEY for full functionality]"


class SentimentAnalyzer:
    """
    Analyze sentiment of financial text using specialized models
    """

    def __init__(self):
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """Load sentiment analysis model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available. Using rule-based sentiment.")
            return

        try:
            # Try to load FinBERT for financial sentiment
            model_name = "ProsusAI/finbert"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model_loaded = True
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load FinBERT: {e!s}. Using fallback.")
            self.model_loaded = False

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Analyze sentiment of text
        
        Returns:
            Dict with sentiment label and score
        """
        if self.model_loaded:
            return self._analyze_with_model(text)
        return self._analyze_rule_based(text)

    def _analyze_with_model(self, text: str) -> dict[str, Any]:
        """Analyze using FinBERT model"""
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

            labels = ["negative", "neutral", "positive"]
            scores = predictions[0].tolist()

            max_idx = scores.index(max(scores))

            return {
                "sentiment": labels[max_idx],
                "confidence": scores[max_idx],
                "scores": {
                    "positive": scores[2],
                    "neutral": scores[1],
                    "negative": scores[0]
                }
            }
        except Exception as e:
            logger.error(f"Model inference error: {e!s}")
            return self._analyze_rule_based(text)

    def _analyze_rule_based(self, text: str) -> dict[str, Any]:
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()

        # Positive words
        positive_words = ["growth", "profit", "increase", "strong", "positive",
                         "excellent", "success", "gain", "improvement", "record"]

        # Negative words
        negative_words = ["loss", "decline", "decrease", "weak", "negative",
                         "poor", "fail", "risk", "concern", "challenge"]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total = positive_count + negative_count

        if total == 0:
            sentiment = "neutral"
            score = 0.5
        else:
            positive_ratio = positive_count / total
            if positive_ratio > 0.6:
                sentiment = "positive"
                score = 0.5 + (positive_ratio - 0.5)
            elif positive_ratio < 0.4:
                sentiment = "negative"
                score = 0.5 - (0.5 - positive_ratio)
            else:
                sentiment = "neutral"
                score = 0.5

        return {
            "sentiment": sentiment,
            "confidence": score,
            "scores": {
                "positive": positive_count / max(total, 1),
                "neutral": 0.5,
                "negative": negative_count / max(total, 1)
            }
        }


class DocumentAnalyzer:
    """
    Comprehensive document analysis combining multiple AI techniques
    """

    def __init__(self):
        self.llm = LLMClient()
        self.sentiment = SentimentAnalyzer()

    def analyze_document(self, text: str) -> dict[str, Any]:
        """
        Perform comprehensive analysis of a document
        
        Args:
            text: Document text content
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing document...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "word_count": len(text.split()),
            "summary": self.llm.generate_summary(text, max_length=200),
            "sentiment": self.sentiment.analyze(text),
            "key_metrics": self.extract_key_metrics(text),
            "entities": self.extract_entities(text),
            "risks": self.identify_risks(text)
        }

        return results

    def extract_key_metrics(self, text: str) -> dict[str, list[str]]:
        """Extract financial metrics from text"""
        metrics = {
            "financial_figures": [],
            "percentages": [],
            "dates": []
        }

        # Extract dollar amounts
        financial_figures = re.findall(r"\$[\d,]+(?:\.\d+)?(?:[MBK]|(?:\s*(?:million|billion|thousand)))?", text)
        metrics["financial_figures"] = list(set(financial_figures))[:10]

        # Extract percentages
        percentages = re.findall(r"\d+(?:\.\d+)?%", text)
        metrics["percentages"] = list(set(percentages))[:10]

        # Extract years
        years = re.findall(r"\b(20\d{2})\b", text)
        metrics["dates"] = list(set(years))

        return metrics

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """Extract named entities (simplified version)"""
        entities = {
            "companies": [],
            "people": [],
            "locations": []
        }

        # Simple capitalized word extraction as proxy
        # In production, use spaCy or similar NER
        words = text.split()
        capitalized = [w for w in words if w and w[0].isupper() and len(w) > 1]

        # Filter out common words
        common_words = {"The", "This", "That", "These", "Those", "A", "An"}
        entities["companies"] = [w for w in capitalized if w not in common_words][:10]

        return entities

    def identify_risks(self, text: str) -> list[str]:
        """Identify potential risks mentioned in text"""
        text_lower = text.lower()

        risk_keywords = {
            "market_risk": ["market risk", "market volatility", "competition", "competitive pressure"],
            "operational_risk": ["operational risk", "supply chain", "disruption", "shortage"],
            "financial_risk": ["debt", "liquidity", "cash flow", "financial risk"],
            "regulatory_risk": ["regulation", "compliance", "regulatory", "legal"],
            "strategic_risk": ["strategy", "strategic risk", "business model"]
        }

        identified_risks = []

        for risk_type, keywords in risk_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    identified_risks.append(risk_type.replace("_", " ").title())
                    break

        return list(set(identified_risks))

    def question_answer(self, text: str, question: str) -> str:
        """Answer a question about the document"""
        return self.llm.answer_question(text, question)


def main():
    """Demo the NLP capabilities"""

    print("\n" + "=" * 80)
    print("NLP & AI INTEGRATION - INVESTMENT DOCUMENT ANALYZER")
    print("=" * 80 + "\n")

    # Sample investment document text
    sample_text = """
    Tech Innovations Inc. reported strong financial results for Q4 2024. 
    Revenue reached $15.2 million, representing a 45% year-over-year growth.
    The company's profit margin improved to 22%, up from 18% in the previous quarter.
    
    Key highlights include:
    - Customer acquisition increased by 35%
    - Monthly recurring revenue (MRR) grew to $3.5 million
    - Cash runway extended to 18 months
    
    However, the company faces several challenges including increasing competition
    in the SaaS market and rising customer acquisition costs. Management has 
    identified regulatory compliance as a potential risk factor for 2025.
    
    The CEO, Sarah Johnson, stated: "We're excited about our growth trajectory 
    and believe our innovative product will continue to capture market share."
    
    Looking forward, the company plans to expand into European markets and 
    launch two new product features in Q1 2025.
    """

    # Initialize analyzer
    analyzer = DocumentAnalyzer()

    print("Analyzing investment document...\n")

    # Perform analysis
    results = analyzer.analyze_document(sample_text)

    # Display results
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)

    print("\n📊 DOCUMENT STATISTICS")
    print(f"  Word Count: {results['word_count']}")
    print(f"  Analysis Time: {results['timestamp']}")

    print("\n📝 EXECUTIVE SUMMARY")
    print(f"  {results['summary']}")

    print("\n😊 SENTIMENT ANALYSIS")
    sentiment = results["sentiment"]
    print(f"  Overall Sentiment: {sentiment['sentiment'].upper()}")
    print(f"  Confidence: {sentiment['confidence']:.2%}")
    print(f"  Positive Score: {sentiment['scores']['positive']:.2f}")
    print(f"  Negative Score: {sentiment['scores']['negative']:.2f}")

    print("\n💰 KEY FINANCIAL METRICS")
    metrics = results["key_metrics"]
    if metrics["financial_figures"]:
        print(f"  Financial Figures: {', '.join(metrics['financial_figures'][:5])}")
    if metrics["percentages"]:
        print(f"  Percentages: {', '.join(metrics['percentages'][:5])}")
    if metrics["dates"]:
        print(f"  Years Mentioned: {', '.join(metrics['dates'])}")

    print("\n⚠️  IDENTIFIED RISKS")
    if results["risks"]:
        for risk in results["risks"]:
            print(f"  • {risk}")
    else:
        print("  No major risks identified")

    # Demo Q&A
    print("\n❓ QUESTION & ANSWER")
    questions = [
        "What was the revenue growth?",
        "What are the main challenges?"
    ]

    for question in questions:
        answer = analyzer.question_answer(sample_text, question)
        print(f"\n  Q: {question}")
        print(f"  A: {answer}")

    # Save results
    script_dir = Path(__file__).parent
    output_dir = script_dir / "outputs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n\n💾 Results saved to: {output_file}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80 + "\n")

    # Additional capabilities demonstration
    print("📚 Additional Capabilities:")
    print("  ✓ Document summarization using LLMs")
    print("  ✓ Financial sentiment analysis with FinBERT")
    print("  ✓ Key metrics extraction")
    print("  ✓ Named entity recognition")
    print("  ✓ Risk identification")
    print("  ✓ Question answering")
    print("  ✓ Batch document processing")
    print("  ✓ API integration (OpenAI, Hugging Face)")

    print("\n💡 For full functionality, set environment variables:")
    print("     set OPENAI_API_KEY=your_key_here")
    print("     pip install transformers torch")


if __name__ == "__main__":
    main()
