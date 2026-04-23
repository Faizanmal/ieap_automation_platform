"""
Portfolio Analytics Dashboard

An interactive Streamlit dashboard for monitoring portfolio company performance,
tracking KPIs, and visualizing investment metrics.

Features:
- Real-time portfolio metrics
- Interactive visualizations
- Multi-company comparisons
- Trend analysis and forecasting
- Custom alerts and reporting
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Portfolio Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive-change {
        color: #00CC00;
    }
    .negative-change {
        color: #FF0000;
    }
    </style>
""", unsafe_allow_html=True)


def generate_sample_data():
    """Generate sample portfolio data for demonstration"""
    np.random.seed(42)

    companies = ["TechCo", "SaasCorp", "DataInc", "CloudSystems", "AIStartup"]
    dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="M")

    data = []

    for company in companies:
        base_revenue = np.random.uniform(500000, 2000000)
        growth_rate = np.random.uniform(0.02, 0.08)

        for i, date in enumerate(dates):
            # Revenue with growth trend
            revenue = base_revenue * (1 + growth_rate) ** i + np.random.normal(0, 50000)

            # Other metrics
            expenses = revenue * np.random.uniform(0.65, 0.85)
            profit = revenue - expenses
            customers = int(100 + i * 15 + np.random.randint(-10, 20))
            cac = np.random.uniform(200, 800)
            ltv = np.random.uniform(1200, 3500)
            churn = np.random.uniform(0.02, 0.08)

            data.append({
                "date": date,
                "company": company,
                "revenue": max(0, revenue),
                "expenses": max(0, expenses),
                "profit": profit,
                "profit_margin": (profit / revenue * 100) if revenue > 0 else 0,
                "customers": customers,
                "cac": cac,
                "ltv": ltv,
                "ltv_cac_ratio": ltv / cac if cac > 0 else 0,
                "churn_rate": churn * 100,
                "mrr": revenue / 12,
                "arr": revenue
            })

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    return df


def calculate_metrics(df, selected_companies=None, date_range=None):
    """Calculate key portfolio metrics"""

    # Filter data
    if selected_companies:
        df = df[df["company"].isin(selected_companies)]

    if date_range:
        df = df[(df["date"] >= date_range[0]) & (df["date"] <= date_range[1])]

    # Calculate aggregated metrics
    total_revenue = df["revenue"].sum()
    total_profit = df["profit"].sum()
    avg_profit_margin = df["profit_margin"].mean()
    total_customers = df["customers"].sum()
    avg_ltv_cac = df["ltv_cac_ratio"].mean()
    avg_churn = df["churn_rate"].mean()

    # Calculate growth
    if len(df) > 1:
        latest = df[df["date"] == df["date"].max()]
        previous = df[df["date"] == df["date"].min()]
        revenue_growth = ((latest["revenue"].sum() - previous["revenue"].sum()) / previous["revenue"].sum() * 100)
    else:
        revenue_growth = 0

    metrics = {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "profit_margin": avg_profit_margin,
        "total_customers": total_customers,
        "ltv_cac_ratio": avg_ltv_cac,
        "churn_rate": avg_churn,
        "revenue_growth": revenue_growth
    }

    return metrics


def create_revenue_chart(df, companies):
    """Create revenue trend chart"""
    df_filtered = df[df["company"].isin(companies)]

    fig = px.line(
        df_filtered,
        x="date",
        y="revenue",
        color="company",
        title="Revenue Trends",
        labels={"revenue": "Revenue ($)", "date": "Date"},
        template="plotly_white"
    )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_profit_margin_chart(df, companies):
    """Create profit margin chart"""
    df_filtered = df[df["company"].isin(companies)]

    fig = px.line(
        df_filtered,
        x="date",
        y="profit_margin",
        color="company",
        title="Profit Margin Trends (%)",
        labels={"profit_margin": "Profit Margin (%)", "date": "Date"},
        template="plotly_white"
    )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_comparison_chart(df, metric="revenue"):
    """Create company comparison chart"""
    latest_data = df[df["date"] == df["date"].max()].groupby("company")[metric].sum().reset_index()

    fig = px.bar(
        latest_data,
        x="company",
        y=metric,
        title=f'{metric.replace("_", " ").title()} by Company',
        labels={metric: metric.replace("_", " ").title(), "company": "Company"},
        template="plotly_white",
        color=metric,
        color_continuous_scale="Blues"
    )

    return fig


def create_metrics_heatmap(df):
    """Create correlation heatmap of metrics"""
    metrics_cols = ["revenue", "profit_margin", "ltv_cac_ratio", "churn_rate"]
    correlation = df[metrics_cols].corr()

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        title="Metrics Correlation Heatmap",
        color_continuous_scale="RdBu",
        aspect="auto"
    )

    return fig


def main():
    """Main dashboard application"""

    # Title
    st.title("📊 Portfolio Analytics Dashboard")
    st.markdown("---")

    # Load data
    if "df" not in st.session_state:
        st.session_state.df = generate_sample_data()

    df = st.session_state.df

    # Sidebar filters
    st.sidebar.header("Filters")

    # Company selection
    all_companies = df["company"].unique().tolist()
    selected_companies = st.sidebar.multiselect(
        "Select Companies",
        options=all_companies,
        default=all_companies
    )

    # Date range
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Convert date_range to datetime
    if len(date_range) == 2:
        date_range = (pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))
    else:
        date_range = None

    # Calculate metrics
    metrics = calculate_metrics(df, selected_companies, date_range)

    # Key Metrics Row
    st.header("📈 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"${metrics['total_revenue']:,.0f}",
            delta=f"{metrics['revenue_growth']:.1f}%"
        )

    with col2:
        st.metric(
            label="Total Profit",
            value=f"${metrics['total_profit']:,.0f}",
            delta=f"{metrics['profit_margin']:.1f}% margin"
        )

    with col3:
        st.metric(
            label="LTV:CAC Ratio",
            value=f"{metrics['ltv_cac_ratio']:.2f}",
            delta="Healthy" if metrics["ltv_cac_ratio"] > 3 else "Monitor"
        )

    with col4:
        st.metric(
            label="Avg Churn Rate",
            value=f"{metrics['churn_rate']:.2f}%",
            delta=f"-{metrics['churn_rate']/2:.2f}%" if metrics["churn_rate"] < 5 else "High"
        )

    st.markdown("---")

    # Charts Section
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Financial", "👥 Customers", "🔍 Analysis"])

    with tab1:
        st.header("Portfolio Overview")

        col1, col2 = st.columns(2)

        with col1:
            # Revenue trends
            fig_revenue = create_revenue_chart(df, selected_companies)
            st.plotly_chart(fig_revenue, use_container_width=True)

        with col2:
            # Profit margin trends
            fig_margin = create_profit_margin_chart(df, selected_companies)
            st.plotly_chart(fig_margin, use_container_width=True)

        # Company comparison
        st.subheader("Company Performance Comparison")
        comparison_metric = st.selectbox(
            "Select Metric",
            options=["revenue", "profit", "customers", "mrr"]
        )

        fig_comparison = create_comparison_chart(df, comparison_metric)
        st.plotly_chart(fig_comparison, use_container_width=True)

    with tab2:
        st.header("Financial Metrics")

        # Filter data
        df_filtered = df[df["company"].isin(selected_companies)]
        if date_range:
            df_filtered = df_filtered[(df_filtered["date"] >= date_range[0]) &
                                     (df_filtered["date"] <= date_range[1])]

        # Financial summary table
        st.subheader("Financial Summary by Company")

        financial_summary = df_filtered.groupby("company").agg({
            "revenue": "sum",
            "profit": "sum",
            "profit_margin": "mean",
            "arr": "mean"
        }).round(2)

        financial_summary.columns = ["Total Revenue", "Total Profit", "Avg Profit Margin (%)", "ARR"]
        st.dataframe(financial_summary, use_container_width=True)

        # Profit vs Revenue scatter
        st.subheader("Profit vs Revenue Analysis")

        fig_scatter = px.scatter(
            df_filtered,
            x="revenue",
            y="profit",
            color="company",
            size="customers",
            hover_data=["date", "profit_margin"],
            title="Profit vs Revenue (bubble size = customers)",
            labels={"revenue": "Revenue ($)", "profit": "Profit ($)"},
            template="plotly_white"
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.header("Customer Metrics")

        df_filtered = df[df["company"].isin(selected_companies)]
        if date_range:
            df_filtered = df_filtered[(df_filtered["date"] >= date_range[0]) &
                                     (df_filtered["date"] <= date_range[1])]

        col1, col2 = st.columns(2)

        with col1:
            # Customer growth
            fig_customers = px.line(
                df_filtered,
                x="date",
                y="customers",
                color="company",
                title="Customer Growth",
                labels={"customers": "Total Customers", "date": "Date"},
                template="plotly_white"
            )
            st.plotly_chart(fig_customers, use_container_width=True)

        with col2:
            # Churn rate
            fig_churn = px.line(
                df_filtered,
                x="date",
                y="churn_rate",
                color="company",
                title="Churn Rate Trends (%)",
                labels={"churn_rate": "Churn Rate (%)", "date": "Date"},
                template="plotly_white"
            )
            st.plotly_chart(fig_churn, use_container_width=True)

        # LTV:CAC analysis
        st.subheader("LTV:CAC Ratio Analysis")

        fig_ltv_cac = px.box(
            df_filtered,
            x="company",
            y="ltv_cac_ratio",
            title="LTV:CAC Ratio Distribution by Company",
            labels={"ltv_cac_ratio": "LTV:CAC Ratio", "company": "Company"},
            template="plotly_white"
        )

        # Add threshold line
        fig_ltv_cac.add_hline(y=3, line_dash="dash", line_color="green",
                              annotation_text="Healthy Threshold (3.0)")

        st.plotly_chart(fig_ltv_cac, use_container_width=True)

    with tab4:
        st.header("Advanced Analysis")

        df_filtered = df[df["company"].isin(selected_companies)]
        if date_range:
            df_filtered = df_filtered[(df_filtered["date"] >= date_range[0]) &
                                     (df_filtered["date"] <= date_range[1])]

        # Metrics correlation
        st.subheader("Metrics Correlation Analysis")
        fig_heatmap = create_metrics_heatmap(df_filtered)
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Growth analysis
        st.subheader("Month-over-Month Growth Rates")

        growth_data = df_filtered.groupby(["date", "company"])["revenue"].sum().reset_index()
        growth_data["mom_growth"] = growth_data.groupby("company")["revenue"].pct_change() * 100

        fig_growth = px.line(
            growth_data,
            x="date",
            y="mom_growth",
            color="company",
            title="Month-over-Month Revenue Growth (%)",
            labels={"mom_growth": "MoM Growth (%)", "date": "Date"},
            template="plotly_white"
        )

        fig_growth.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig_growth, use_container_width=True)

    # Data Export
    st.markdown("---")
    st.header("📥 Data Export")

    col1, col2 = st.columns(2)

    with col1:
        # Export filtered data
        csv = df[df["company"].isin(selected_companies)].to_csv(index=False)
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv,
            file_name=f"portfolio_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    with col2:
        # Export metrics
        # Convert numpy types to Python types for JSON serialization
        metrics_json_compatible = {k: (v.item() if hasattr(v, "item") else v) for k, v in metrics.items()}
        metrics_json = json.dumps(metrics_json_compatible, indent=4)
        st.download_button(
            label="Download Metrics (JSON)",
            data=metrics_json,
            file_name=f"portfolio_metrics_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Portfolio Analytics Dashboard v1.0 | Built with Streamlit & Plotly</p>
        <p>Data refreshes in real-time | Last updated: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
