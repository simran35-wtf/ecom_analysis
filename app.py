import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# ---------------------------------------------------------
# Page Config (First calling page config)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ecommerce Sales Dashboard",
    page_icon="🛒",
    layout="wide"
)

sns.set_style("whitegrid")

# ---------------------------------------------------------
# Data Load + Clean (Load Dataset)
# ---------------------------------------------------------
DATA_PATH = "data.csv"  


@st.cache_data
def load_data(path):
    df = pd.read_csv(path,encoding="latin1")
    df = df.dropna(subset=["Description"])

    df["IsCancelled"] = df["InvoiceNo"].astype(str).str.startswith("C")

    df_clean = df[
        (~df["IsCancelled"]) &
        (df["Quantity"] > 0) &
        (df["UnitPrice"] > 0)
    ].copy()

    df_clean["InvoiceDate"] = pd.to_datetime(
        df_clean["InvoiceDate"], format="%m/%d/%Y %H:%M"
    )
    df_clean["TotalPrice"] = np.multiply(df_clean["Quantity"], df_clean["UnitPrice"])
    df_clean["Year"] = df_clean["InvoiceDate"].dt.year
    df_clean["Month"] = df_clean["InvoiceDate"].dt.month
    df_clean["Hour"] = df_clean["InvoiceDate"].dt.hour
    df_clean["DayOfWeek"] = df_clean["InvoiceDate"].dt.day_name()
    df_clean["YearMonth"] = df_clean["InvoiceDate"].dt.to_period("M").astype(str)

    return df_clean


df_clean = load_data(DATA_PATH)

# ---------------------------------------------------------
# Sidebar Filters 
# ---------------------------------------------------------
st.sidebar.header("Filters")

countries = sorted(df_clean["Country"].unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Country Option", options=countries, default=countries
)

min_date = df_clean["InvoiceDate"].min().date()
max_date = df_clean["InvoiceDate"].max().date()
date_range = st.sidebar.date_input(
    "Date Range", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)

# Filters apply karna
mask = df_clean["Country"].isin(selected_countries)
if len(date_range) == 2:
    start_date, end_date = date_range
    mask &= (df_clean["InvoiceDate"].dt.date >= start_date) & \
            (df_clean["InvoiceDate"].dt.date <= end_date)

filtered = df_clean[mask]

# ---------------------------------------------------------
# Title
# ---------------------------------------------------------
st.title("Ecommerce Sales Dashboard")
st.markdown("Interactive view of revenue, products, customers aur trends.")

# ---------------------------------------------------------
# KPI Cards (top metrics row)
# ---------------------------------------------------------
total_revenue = filtered["TotalPrice"].sum()
total_orders = filtered["InvoiceNo"].nunique()
total_customers = filtered["CustomerID"].nunique()
avg_order_value = filtered.groupby("InvoiceNo")["TotalPrice"].sum().mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"£{total_revenue:,.0f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Total Customers", f"{total_customers:,}")
col4.metric("Avg Order Value", f"£{avg_order_value:,.2f}")

st.markdown("---")

# ---------------------------------------------------------
# Row 1: Monthly Trend + Top Countries
# ---------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Monthly Revenue Trend")
    monthly_sales = filtered.groupby("YearMonth")["TotalPrice"].sum()
    fig, ax = plt.subplots(figsize=(6, 4))
    monthly_sales.plot(kind="line", marker="o", color="royalblue", ax=ax)
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("Revenue (£)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

with row1_col2:
    st.subheader("Top 10 Countries by Revenue")
    country_revenue = (
        filtered.groupby("Country")["TotalPrice"].sum()
        .sort_values(ascending=False).head(10)
    )
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=country_revenue.values, y=country_revenue.index,
                hue=country_revenue.index, palette="crest", legend=False, ax=ax)
    ax.set_xlabel("Revenue (£)")
    st.pyplot(fig)

# ---------------------------------------------------------
# Row 2: Top Products + Order Value Distribution
# ---------------------------------------------------------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Top 10 Products by Revenue")
    top_products = (
        filtered.groupby("Description")["TotalPrice"].sum()
        .sort_values(ascending=False).head(10)
    )
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=top_products.values, y=top_products.index,
                hue=top_products.index, palette="viridis", legend=False, ax=ax)
    ax.set_xlabel("Revenue (£)")
    st.pyplot(fig)

with row2_col2:
    st.subheader("📊 Order Value Distribution")
    order_values = filtered.groupby("InvoiceNo")["TotalPrice"].sum().values
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(order_values, bins=50, kde=True, color="teal", ax=ax)
    ax.set_xlim(0, 1000)
    ax.set_xlabel("Order Value (£)")
    st.pyplot(fig)

# ---------------------------------------------------------
# Row 3: Sales by Day of Week + Hour
# ---------------------------------------------------------
row3_col1, row3_col2 = st.columns(2)

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]

with row3_col1:
    st.subheader("📅 Revenue by Day of Week")
    sales_by_day = filtered.groupby("DayOfWeek")["TotalPrice"].sum().reindex(day_order)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=sales_by_day.index, y=sales_by_day.values,
                hue=sales_by_day.index, palette="coolwarm", legend=False, ax=ax)
    plt.xticks(rotation=45)
    ax.set_ylabel("Revenue (£)")
    st.pyplot(fig)

with row3_col2:
    st.subheader("🕒 Revenue by Hour of Day")
    sales_by_hour = filtered.groupby("Hour")["TotalPrice"].sum()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.lineplot(x=sales_by_hour.index, y=sales_by_hour.values,
                 marker="o", color="darkorange", ax=ax)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Revenue (£)")
    st.pyplot(fig)

# ---------------------------------------------------------
# Row 4: Top Customers Table
# ---------------------------------------------------------
st.subheader("👤 Top 10 Customers by Spend")
customer_summary = filtered.groupby("CustomerID").agg(
    TotalSpent=("TotalPrice", "sum"),
    NumOrders=("InvoiceNo", "nunique"),
    AvgOrderValue=("TotalPrice", "mean"),
    LastPurchase=("InvoiceDate", "max")
).sort_values("TotalSpent", ascending=False).head(10)

st.dataframe(customer_summary, use_container_width=True)

# ---------------------------------------------------------
# Raw Data (optional expandable section)
# ---------------------------------------------------------
with st.expander("Raw Filtered Data Insight"):
    st.dataframe(filtered.head(500), use_container_width=True)