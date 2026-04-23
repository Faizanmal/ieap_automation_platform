"""
Financial Data Processing Automation Pipeline

This is the main orchestrator for the automated data processing pipeline.
It coordinates data extraction, processing, validation, and report generation.

Key Features:
- Multi-source data extraction (APIs, files, databases)
- Automated data cleaning and transformation
- Data quality validation
- Automated report generation
- Email notifications and alerts
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


# Configure logging
def setup_logging():
    """Configure logging for the pipeline"""
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


class DataExtractor:
    """Extract data from various sources"""

    def __init__(self, config: dict):
        self.config = config
        self.data = {}

    def extract_from_file(self, file_path: str) -> pd.DataFrame:
        """Extract data from CSV or Excel file"""
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")

            logger.info(f"Extracted {len(df)} records from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error extracting from file {file_path}: {e!s}")
            raise

    def extract_sample_data(self) -> pd.DataFrame:
        """Generate sample financial data for demonstration"""
        np.random.seed(42)

        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        n_days = len(dates)

        # Generate realistic financial data
        base_revenue = 100000
        trend = np.linspace(0, 20000, n_days)  # Growing trend
        seasonality = 10000 * np.sin(np.linspace(0, 4*np.pi, n_days))  # Seasonal pattern
        noise = np.random.normal(0, 5000, n_days)

        data = pd.DataFrame({
            "date": dates,
            "revenue": base_revenue + trend + seasonality + noise,
            "expenses": np.random.uniform(60000, 80000, n_days),
            "transactions": np.random.randint(500, 2000, n_days),
            "customers": np.random.randint(100, 500, n_days),
            "region": np.random.choice(["North", "South", "East", "West"], n_days),
            "product_category": np.random.choice(["Electronics", "Software", "Services"], n_days)
        })

        # Add some missing values to simulate real data
        data.loc[np.random.choice(data.index, 10), "revenue"] = np.nan
        data.loc[np.random.choice(data.index, 5), "expenses"] = np.nan

        logger.info(f"Generated {len(data)} sample financial records")
        return data

    def extract_all(self) -> dict[str, pd.DataFrame]:
        """Extract data from all configured sources"""
        logger.info("Starting data extraction...")

        # For demo, use sample data
        self.data["financial_data"] = self.extract_sample_data()

        return self.data


class DataProcessor:
    """Process and transform extracted data"""

    def __init__(self):
        self.processed_data = {}

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data by handling missing values and outliers"""
        df = df.copy()

        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if df[col].isnull().sum() > 0:
                # Fill with median
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                logger.info(f"Filled {df[col].isnull().sum()} missing values in {col}")

        # Remove outliers using IQR method
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outliers > 0:
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
                logger.info(f"Removed {outliers} outliers from {col}")

        return df

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data and create calculated fields"""
        df = df.copy()

        # Calculate profit
        df["profit"] = df["revenue"] - df["expenses"]

        # Calculate profit margin
        df["profit_margin"] = (df["profit"] / df["revenue"] * 100).round(2)

        # Calculate average transaction value
        df["avg_transaction_value"] = (df["revenue"] / df["transactions"]).round(2)

        # Calculate revenue per customer
        df["revenue_per_customer"] = (df["revenue"] / df["customers"]).round(2)

        # Add time-based features
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df["quarter"] = df["date"].dt.quarter
            df["day_of_week"] = df["date"].dt.day_name()
            df["week_of_year"] = df["date"].dt.isocalendar().week

        logger.info(f"Transformed data with {len(df.columns)} features")
        return df

    def aggregate_metrics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate aggregate metrics"""
        metrics = {
            "total_revenue": float(df["revenue"].sum()),
            "total_expenses": float(df["expenses"].sum()),
            "total_profit": float(df["profit"].sum()),
            "avg_daily_revenue": float(df["revenue"].mean()),
            "avg_profit_margin": float(df["profit_margin"].mean()),
            "total_transactions": int(df["transactions"].sum()),
            "total_customers": int(df["customers"].sum()),
            "max_daily_revenue": float(df["revenue"].max()),
            "min_daily_revenue": float(df["revenue"].min())
        }

        logger.info("Calculated aggregate metrics")
        return metrics

    def process(self, data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """Process all datasets"""
        logger.info("Starting data processing...")

        results = {}

        for name, df in data.items():
            logger.info(f"Processing {name}...")

            # Clean data
            df_clean = self.clean_data(df)

            # Transform data
            df_transformed = self.transform_data(df_clean)

            # Calculate metrics
            metrics = self.aggregate_metrics(df_transformed)

            results[name] = {
                "data": df_transformed,
                "metrics": metrics
            }

        self.processed_data = results
        return results


class DataValidator:
    """Validate data quality and integrity"""

    def __init__(self, config: dict):
        self.config = config
        self.validation_results = {}

    def validate_completeness(self, df: pd.DataFrame) -> dict[str, Any]:
        """Check data completeness"""
        total_rows = len(df)
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()

        completeness = {
            "total_rows": total_rows,
            "total_cells": total_cells,
            "missing_cells": int(missing_cells),
            "completeness_rate": float((total_cells - missing_cells) / total_cells * 100)
        }

        return completeness

    def validate_ranges(self, df: pd.DataFrame) -> list[str]:
        """Validate that values are within expected ranges"""
        issues = []

        # Revenue should be positive
        if "revenue" in df.columns:
            negative_revenue = (df["revenue"] < 0).sum()
            if negative_revenue > 0:
                issues.append(f"Found {negative_revenue} negative revenue values")

        # Profit margin should be reasonable
        if "profit_margin" in df.columns:
            extreme_margins = ((df["profit_margin"] < -100) | (df["profit_margin"] > 100)).sum()
            if extreme_margins > 0:
                issues.append(f"Found {extreme_margins} extreme profit margin values")

        return issues

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate processed data"""
        logger.info("Starting data validation...")

        results = {}

        for name, dataset in data.items():
            df = dataset["data"]

            validation = {
                "completeness": self.validate_completeness(df),
                "range_issues": self.validate_ranges(df),
                "row_count": len(df),
                "column_count": len(df.columns)
            }

            results[name] = validation

            # Log issues
            if validation["range_issues"]:
                logger.warning(f"Validation issues in {name}:")
                for issue in validation["range_issues"]:
                    logger.warning(f"  - {issue}")
            else:
                logger.info(f"Data validation passed for {name}")

        self.validation_results = results
        return results


class ReportGenerator:
    """Generate automated reports"""

    def __init__(self):
        script_dir = Path(__file__).parent
        self.output_dir = script_dir / "reports" / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary_report(self, data: dict[str, Any], metrics: dict[str, Any]) -> str:
        """Generate a text summary report"""
        report_lines = [
            "=" * 80,
            "FINANCIAL DATA PROCESSING REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "SUMMARY METRICS",
            "-" * 80,
            f"Total Revenue:        ${metrics['total_revenue']:,.2f}",
            f"Total Expenses:       ${metrics['total_expenses']:,.2f}",
            f"Total Profit:         ${metrics['total_profit']:,.2f}",
            f"Avg Daily Revenue:    ${metrics['avg_daily_revenue']:,.2f}",
            f"Avg Profit Margin:    {metrics['avg_profit_margin']:.2f}%",
            f"Total Transactions:   {metrics['total_transactions']:,}",
            f"Total Customers:      {metrics['total_customers']:,}",
            "",
            "REVENUE ANALYSIS",
            "-" * 80,
            f"Maximum Daily:        ${metrics['max_daily_revenue']:,.2f}",
            f"Minimum Daily:        ${metrics['min_daily_revenue']:,.2f}",
            f"Range:                ${metrics['max_daily_revenue'] - metrics['min_daily_revenue']:,.2f}",
            "",
            "=" * 80,
            "End of Report",
            "=" * 80
        ]

        report_text = "\n".join(report_lines)

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"summary_report_{timestamp}.txt"

        with open(report_path, "w") as f:
            f.write(report_text)

        logger.info(f"Summary report saved to {report_path}")
        return report_text

    def generate_csv_export(self, df: pd.DataFrame, filename: str) -> str:
        """Export processed data to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{filename}_{timestamp}.csv"

        df.to_csv(output_path, index=False)
        logger.info(f"CSV export saved to {output_path}")

        return str(output_path)

    def generate_json_metrics(self, metrics: dict[str, Any], filename: str) -> str:
        """Export metrics to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{filename}_{timestamp}.json"

        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=4)

        logger.info(f"Metrics JSON saved to {output_path}")
        return str(output_path)


class Pipeline:
    """Main pipeline orchestrator"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.extractor = DataExtractor(self.config)
        self.processor = DataProcessor()
        self.validator = DataValidator(self.config)
        self.reporter = ReportGenerator()

    def load_config(self, config_path: str) -> dict:
        """Load pipeline configuration"""
        # Default config for demo
        default_config = {
            "pipeline": {
                "name": "Financial Data Automation",
                "version": "1.0"
            },
            "data_sources": {
                "enabled": ["sample"]
            },
            "processing": {
                "clean_outliers": True,
                "handle_missing": True
            },
            "reporting": {
                "formats": ["txt", "csv", "json"]
            }
        }

        try:
            if Path(config_path).exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                return config
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}, using defaults: {e}")

        return default_config

    def run(self, mode="full"):
        """Run the pipeline"""
        logger.info(f"Starting pipeline in {mode} mode...")

        try:
            # Extract data
            if mode in ["full", "extract"]:
                raw_data = self.extractor.extract_all()
                logger.info("✓ Data extraction completed")

            # Process data
            if mode in ["full", "process"]:
                processed_data = self.processor.process(raw_data)
                logger.info("✓ Data processing completed")

            # Validate data
            if mode in ["full", "validate"]:
                validation_results = self.validator.validate(processed_data)
                logger.info("✓ Data validation completed")

            # Generate reports
            if mode in ["full", "report"]:
                for name, dataset in processed_data.items():
                    # Summary report
                    self.reporter.generate_summary_report(
                        dataset["data"],
                        dataset["metrics"]
                    )

                    # CSV export
                    self.reporter.generate_csv_export(
                        dataset["data"],
                        f"{name}_processed"
                    )

                    # Metrics JSON
                    self.reporter.generate_json_metrics(
                        dataset["metrics"],
                        f"{name}_metrics"
                    )

                logger.info("✓ Report generation completed")

            logger.info("=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e!s}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Financial Data Automation Pipeline")
    parser.add_argument("--mode", choices=["full", "extract", "process", "validate", "report"],
                       default="full", help="Pipeline execution mode")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("FINANCIAL DATA PROCESSING AUTOMATION PIPELINE")
    print("=" * 80 + "\n")

    # Create and run pipeline
    pipeline = Pipeline(config_path=args.config)
    pipeline.run(mode=args.mode)


if __name__ == "__main__":
    main()
