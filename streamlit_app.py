import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuration Constants
SALARY_RANGES = {
    "0-10000": {"min": 0, "max": 10000, "savings_target": 0.10},
    "10000-20000": {"min": 10000, "max": 20000, "savings_target": 0.15},
    "20000-30000": {"min": 20000, "max": 30000, "savings_target": 0.20},
    "30000-40000": {"min": 30000, "max": 40000, "savings_target": 0.25},
    "40000-50000": {"min": 40000, "max": 50000, "savings_target": 0.30},
    "50000+": {"min": 50000, "max": float('inf'), "savings_target": 0.35}
}

BUDGET_CATEGORIES = {
    "Groceries": 5000,
    "Utilities": 3000,
    "Rent/Mortgage": 15000,
    "Transportation": 2000,
    "Dining Out": 3000,
    "Entertainment": 2000,
    "Shopping": 4000,
    "Health": 5000,
    "Other": 3000
}

def calculate_budget_metrics(df, budget_categories):
    """Calculate budget-related metrics"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_df = df[
        (df['Date'].dt.month == current_month) &
        (df['Date'].dt.year == current_year)
    ]
    
    metrics = {
        'total_budget': sum(budget_categories.values()),
        'total_spent': monthly_df['Amount'].sum(),
        'category_metrics': {}
    }
    
    for category, budget in budget_categories.items():
        spent = monthly_df[monthly_df['Category'] == category]['Amount'].sum()
        metrics['category_metrics'][category] = {
            'budget': budget,
            'spent': spent,
            'remaining': budget - spent,
            'percentage': (spent / budget * 100) if budget > 0 else 0
        }
    
    return metrics

def create_savings_chart(salary_range, total_spent):
    """Create savings analysis chart"""
    range_info = SALARY_RANGES[salary_range]
    min_salary = range_info["min"]
    savings_target = range_info["savings_target"]
    
    recommended_savings = min_salary * savings_target
    actual_savings = max(0, min_salary - total_spent)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Recommended', 'Actual'],
        y=[recommended_savings, actual_savings],
        text=[f'₹{recommended_savings:,.0f}', f'₹{actual_savings:,.0f}'],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Monthly Savings Analysis',
        yaxis_title='Amount (₹)',
        showlegend=False
    )
    
    return fig

def get_savings_recommendations(salary_range, total_spent):
    """Generate savings recommendations"""
    range_info = SALARY_RANGES[salary_range]
    savings_target = range_info["savings_target"]
    min_salary = range_info["min"]
    
    recommendations = []
    if total_spent > (1 - savings_target) * min_salary:
        recommendations.append(f"⚠️ Your spending is higher than recommended. Try to save at least {savings_target*100}% of your income.")
    
    if salary_range in ["0-10000", "10000-20000"]:
        recommendations.extend([
            "🎯 Focus on essential expenses only",
            "🚶‍♂️ Use public transportation when possible",
            "🥘 Cook meals at home instead of eating out",
        ])
    elif salary_range in ["20000-30000", "30000-40000"]:
        recommendations.extend([
            "💰 Consider starting an emergency fund",
            "📱 Review and optimize monthly subscriptions",
            "🏦 Look into fixed deposits for savings",
        ])
    else:
        recommendations.extend([
            "📈 Consider investing in mutual funds",
            "🏠 Plan for long-term investments",
            "💳 Optimize credit card rewards",
        ])
    
    return recommendations

# Page Configuration
st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰", layout="wide")

# Initialize Session State
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Description'])
if 'currency_symbol' not in st.session_state:
    st.session_state.currency_symbol = '₹'
if 'salary_range' not in st.session_state:
    st.session_state.salary_range = "0-10000"
if 'monthly_salary' not in st.session_state:
    st.session_state.monthly_salary = 0

# Main App Title
st.title("💰 Personal Finance Tracker")
st.markdown("Track your expenses, analyze spending patterns, and get personalized savings recommendations.")

# Sidebar - Income Settings
with st.sidebar:
    st.header("💼 Income Settings")
    selected_salary_range = st.selectbox(
        "Select Monthly Salary Range",
        options=list(SALARY_RANGES.keys()),
        format_func=lambda x: f"₹{x}",
    )
    st.session_state.salary_range = selected_salary_range

    exact_salary = st.number_input(
        "Enter Exact Monthly Salary",
        min_value=SALARY_RANGES[selected_salary_range]["min"],
        max_value=SALARY_RANGES[selected_salary_range]["max"] if selected_salary_range != "50000+" else 1000000,
        value=SALARY_RANGES[selected_salary_range]["min"]
    )
    st.session_state.monthly_salary = exact_salary

# Expense Input Form
st.subheader("📝 Add New Expense")
with st.form("expense_form", clear_on_submit=True):
    cols = st.columns([1, 1, 1, 2])
    
    with cols[0]:
        date = st.date_input("Date", value=datetime.now())
    with cols[1]:
        category = st.selectbox("Category", options=list(BUDGET_CATEGORIES.keys()))
    with cols[2]:
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
    with cols[3]:
        description = st.text_input("Description (Optional)")
        
    submitted = st.form_submit_button("Add Expense")
    
    if submitted:
        new_expense = pd.DataFrame([{
            'Date': pd.to_datetime(date),
            'Category': category,
            'Amount': amount,
            'Description': description or "-"
        }])
        st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, new_expense], ignore_index=True)
        st.success("✅ Expense added successfully!")

# Calculate Budget Metrics
if not st.session_state.expenses_df.empty:
    budget_metrics = calculate_budget_metrics(st.session_state.expenses_df, BUDGET_CATEGORIES)
    
    # Overview Metrics
    st.subheader("📊 Monthly Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income", f"₹{st.session_state.monthly_salary:,.2f}")
    with col2:
        st.metric("Total Expenses", f"₹{budget_metrics['total_spent']:,.2f}")
    with col3:
        savings = max(0, st.session_state.monthly_salary - budget_metrics['total_spent'])
        st.metric("Total Savings", f"₹{savings:,.2f}")
    with col4:
        savings_rate = (savings / st.session_state.monthly_salary * 100) if st.session_state.monthly_salary > 0 else 0
        st.metric("Savings Rate", f"{savings_rate:.1f}%")

    # Savings Analysis
    st.subheader("💰 Savings Analysis")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        savings_fig = create_savings_chart(
            st.session_state.salary_range,
            budget_metrics['total_spent']
        )
        st.plotly_chart(savings_fig, use_container_width=True)
    
    with col2:
        st.subheader("📋 Savings Tips")
        recommendations = get_savings_recommendations(
            st.session_state.salary_range,
            budget_metrics['total_spent']
        )
        for rec in recommendations:
            st.write(rec)

    # Expense Analysis
    st.subheader("💳 Expense Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        # Category-wise spending
        category_spending = st.session_state.expenses_df.groupby('Category')['Amount'].sum()
        fig_category = px.pie(
            values=category_spending.values,
            names=category_spending.index,
            title="Spending by Category"
        )
        st.plotly_chart(fig_category, use_container_width=True)
    
    with col2:
        # Monthly trend
        monthly_spending = st.session_state.expenses_df.set_index('Date')['Amount'].resample('M').sum()
        fig_trend = px.line(
            monthly_spending,
            title="Monthly Spending Trend",
            labels={'value': 'Amount', 'Date': 'Month'}
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # Detailed Expenses Table
    st.subheader("📑 Expense Details")
    st.dataframe(
        st.session_state.expenses_df.sort_values('Date', ascending=False),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("👆 Start by adding your expenses using the form above!")
