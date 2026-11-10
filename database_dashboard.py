
import html
from collections import defaultdict

import streamlit as st
import plotly.graph_objects as go

from modules.database_queries import (
    get_dataset_list,
    get_sales_records,
    get_database_summary
)


st.set_page_config(
    page_title="SenX | Database Explorer",
    page_icon="📊",
    layout="wide"
)


def render_table(records):
    """Render records as HTML without using Pandas or PyArrow."""

    if not records:
        st.info("No records available.")
        return

    columns = list(records[0].keys())

    header = "".join(
        f"<th>{html.escape(str(column))}</th>"
        for column in columns
    )

    body = ""

    for record in records:
        cells = "".join(
            f"<td>{html.escape(str(record.get(column, '') or ''))}</td>"
            for column in columns
        )

        body += f"<tr>{cells}</tr>"

    table = f"""
    <div style="overflow-x:auto; max-height:500px; overflow-y:auto;">
        <table style="
            width:100%;
            border-collapse:collapse;
            font-size:13px;
        ">
            <thead>
                <tr style="background:#263445;color:white;">
                    {header}
                </tr>
            </thead>
            <tbody>{body}</tbody>
        </table>
    </div>
    """

    st.html(table)


st.title("SenX Database Explorer")
st.caption("Explore business datasets stored in MySQL.")

datasets = get_dataset_list()

if not datasets:
    st.warning("No completed datasets found in MySQL.")
    st.stop()

dataset_options = {
    f"{item['filename']} | ID: {item['id']}": item["id"]
    for item in datasets
}

selected_dataset = st.selectbox(
    "Select a dataset",
    options=list(dataset_options.keys())
)

dataset_id = dataset_options[selected_dataset]

summary = get_database_summary(dataset_id)

if not summary:
    st.warning("Could not retrieve dataset statistics.")
    st.stop()

# KPI section
st.subheader("Dataset Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Records", f"{summary['total_records']:,}")
col2.metric("Revenue", f"${summary['total_revenue']:,.2f}")
col3.metric("Profit", f"${summary['total_profit']:,.2f}")
col4.metric("Orders", f"{summary['total_orders']:,}")
col5.metric("Customers", f"{summary['total_customers']:,}")

# Retrieve records
with st.spinner("Retrieving records from MySQL..."):
    records = get_sales_records(dataset_id)

if not records:
    st.warning("This dataset has no sales records.")
    st.stop()

# Category analysis
st.divider()
st.subheader("Revenue by Category")

category_revenue = defaultdict(float)

for record in records:
    category = record.get("Category") or "Unknown"

    try:
        sales = float(record.get("Sales") or 0)
    except (ValueError, TypeError):
        sales = 0

    category_revenue[category] += sales

categories = sorted(
    category_revenue,
    key=lambda category: category_revenue[category],
    reverse=True
)

fig = go.Figure(
    data=[
        go.Bar(
            x=categories,
            y=[category_revenue[item] for item in categories],
            text=[
                f"${category_revenue[item]:,.0f}"
                for item in categories
            ],
            textposition="auto"
        )
    ]
)

fig.update_layout(
    title="Total Revenue by Product Category",
    xaxis_title="Category",
    yaxis_title="Revenue ($)",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# Data preview
st.divider()
st.subheader("Sales Records")

search = st.text_input(
    "Search by Order ID, Customer Name or Product Name"
)

filtered_records = records

if search.strip():
    keyword = search.strip().lower()

    filtered_records = [
        record for record in records
        if keyword in str(record.get("Order ID", "")).lower()
        or keyword in str(record.get("Customer Name", "")).lower()
        or keyword in str(record.get("Product Name", "")).lower()
    ]

st.caption(
    f"Showing {min(100, len(filtered_records)):,} "
    f"of {len(filtered_records):,} matching records."
)

render_table(filtered_records[:100])

# Download option
csv_columns = list(records[0].keys())

import csv
import io

output = io.StringIO()
writer = csv.DictWriter(output, fieldnames=csv_columns)
writer.writeheader()
writer.writerows(filtered_records)

st.download_button(
    label="Download Filtered Records as CSV",
    data=output.getvalue(),
    file_name="senx_database_export.csv",
    mime="text/csv"
)
