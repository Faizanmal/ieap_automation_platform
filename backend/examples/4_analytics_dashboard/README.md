# Project 4: Portfolio Analytics Dashboard

## Overview
An interactive analytics dashboard for monitoring portfolio company performance, tracking KPIs, and visualizing investment metrics. Built with Streamlit for rapid deployment and intuitive user experience.

## Business Value
- **Real-time insights** into portfolio performance
- **Interactive visualizations** for data exploration
- **KPI tracking** across multiple companies
- **Trend analysis** and forecasting
- **Data-driven decision** support

## Features

### 1. Performance Metrics
- Revenue and profit tracking
- Growth rate calculations
- Margin analysis
- Customer metrics (LTV, CAC, Churn)
- Operational KPIs

### 2. Visualizations
- **Time series charts**: Revenue, profit, growth trends
- **Comparison charts**: Company performance benchmarking
- **Distribution plots**: Metric distributions
- **Correlation heatmaps**: Metric relationships
- **Geographic maps**: Regional performance
- **Custom dashboards**: User-configurable views

### 3. Analytics Capabilities
- **Trend analysis**: Identify patterns and trajectories
- **Forecasting**: Predictive analytics for future performance
- **Anomaly detection**: Flag unusual patterns
- **Cohort analysis**: Track customer cohorts
- **Segment analysis**: Performance by category/region

### 4. Interactive Features
- **Filters**: Date range, company, category selection
- **Drill-down**: Click to explore details
- **Export**: Download data and reports
- **Alerts**: Configurable threshold alerts
- **Real-time updates**: Auto-refresh capabilities

## Dashboard Sections

### Overview Dashboard
- Portfolio summary metrics
- Top performers
- Recent alerts
- Quick insights

### Financial Dashboard
- Revenue trends
- Profit margins
- Cash flow analysis
- Burn rate tracking

### Operations Dashboard
- Customer acquisition
- Churn analysis
- User engagement
- Product metrics

### Comparative Dashboard
- Company benchmarking
- Industry comparisons
- Historical trends
- Performance rankings

## Technical Stack

- **Framework**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Altair, Matplotlib
- **Analytics**: SciPy, Statsmodels
- **Database**: SQLite (demo), PostgreSQL (production)

## Files Structure

```
4_analytics_dashboard/
├── dashboard/
│   ├── app.py                 # Main Streamlit app
│   ├── pages/
│   │   ├── overview.py        # Overview page
│   │   ├── financial.py       # Financial metrics
│   │   ├── operations.py      # Operational metrics
│   │   └── comparative.py     # Comparisons
│   ├── components/
│   │   ├── charts.py          # Chart components
│   │   ├── metrics.py         # Metric cards
│   │   └── filters.py         # Filter components
│   └── utils/
│       ├── data_loader.py     # Data loading
│       └── calculations.py    # Metric calculations
├── data/
│   ├── sample_data.csv        # Sample portfolio data
│   └── schema.sql             # Database schema
└── README.md
```

## Usage

### Run Dashboard
```bash
cd 4_analytics_dashboard
streamlit run dashboard/app.py
```

Access at `http://localhost:8501`

### Features Demo
- Upload custom data
- Select date ranges
- Filter by company
- Export visualizations
- Configure alerts

## Sample Metrics Tracked

### Financial Metrics
- Revenue (MRR, ARR)
- Gross Profit & Margin
- Operating Expenses
- EBITDA
- Cash & Runway

### Growth Metrics
- Revenue Growth Rate
- Customer Growth Rate
- Market Share
- Expansion Rate

### Customer Metrics
- Customer Acquisition Cost (CAC)
- Customer Lifetime Value (LTV)
- LTV:CAC Ratio
- Churn Rate
- Net Revenue Retention (NRR)

### Efficiency Metrics
- Burn Multiple
- Magic Number
- Payback Period
- Rule of 40

## Data Integration

Supports multiple data sources:
- CSV/Excel uploads
- Database connections (PostgreSQL, MySQL)
- API integrations
- Real-time data feeds

## Customization

Edit `config.yaml` to:
- Add custom metrics
- Configure chart types
- Set alert thresholds
- Customize branding

## Key Features
✅ Interactive charts with drill-down  
✅ Real-time data updates  
✅ Multi-company comparison  
✅ Custom metric calculations  
✅ Export to PDF/Excel  
✅ Mobile-responsive design  
✅ User authentication (optional)  
✅ Scheduled report generation  
