import html
import csv
import io
from modules.database_service import import_cleaned_dataset
from modules.database_queries import (
    get_dataset_list,
    get_sales_records,
    delete_dataset
)
from modules.report_generator import (
    generate_pdf_report,
    generate_excel_report
)
from modules.customer_analysis import analyze_customers
from modules.forecasting import forecast_sales
from pathlib import Path
import plotly.graph_objects as go

from modules.analytics import analyze_sales
from modules.data_cleaner import clean_dataset, save_cleaned_csv
from modules.data_loader import (
    load_csv,
    load_excel,
    load_uploaded_dataset,
    profile_dataset
)
import streamlit as st

def load_selected_mysql_dataset():
    """Load the selected completed dataset from MySQL."""

    datasets = get_dataset_list()

    if not datasets:
        st.warning(
            "No completed datasets found in MySQL. "
            "Please import a dataset first."
        )
        return []

    dataset_options = {
        f"{item['filename']} | Dataset ID: {item['id']}": item["id"]
        for item in datasets
    }

    selected_label = st.selectbox(
        "Select MySQL Dataset",
        options=list(dataset_options.keys()),
        key="senx_mysql_dataset_selector"
    )

    dataset_id = dataset_options[selected_label]

    rows = get_sales_records(dataset_id)

    st.success(
        f"Loaded {len(rows):,} records directly from MySQL."
    )

    return rows
# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SenX | Business Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_table(data):
    """
    Display dictionaries as an HTML table.
    Avoids Streamlit's dataframe/PyArrow rendering.
    """

    if not data:
        st.info("No records available.")
        return

    columns = list(data[0].keys())

    table_html = """
    <div style="
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    ">
    <table style="
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        white-space: nowrap;
    ">
    <thead>
    <tr>
    """

    for column in columns:
        table_html += f"""
        <th style="
            background-color: #172554;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
        ">{html.escape(str(column))}</th>
        """

    table_html += "</tr></thead><tbody>"

    for row in data:

        table_html += "<tr>"

        for column in columns:

            value = row.get(column)

            if value is None:
                value = "—"

            table_html += f"""
            <td style="
                padding: 10px;
                border-bottom: 1px solid #e5e7eb;
                color: #334155;
            ">{html.escape(str(value))}</td>
            """

        table_html += "</tr>"

    table_html += "</tbody></table></div>"

    st.html(table_html)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
    .main {
        background-color: #f7f8fc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .hero {
        background: linear-gradient(120deg, #172554, #1e40af);
        padding: 30px;
        border-radius: 14px;
        color: white;
        margin-bottom: 25px;
    }

    .hero h1 {
        color: white;
        font-size: 34px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #dbeafe;
        font-size: 15px;
    }

    .section-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 15px;
    }

    .section-card h3 {
        color: #172554;
    }

    .status {
        color: #64748b;
        font-size: 13px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 18px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("📊 SenX")
st.sidebar.caption("Business Intelligence Platform")

st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Data Upload",
        "Data Cleaning",
        "Sales Analytics",
        "Customer Analytics",
        "Forecasting",
        "Dataset Management",
        "Reports"
    ]
)

st.sidebar.divider()

st.sidebar.markdown("### Project Status")
st.sidebar.info(
    "Production-ready analytics features under development."
)

st.sidebar.caption("SenX v1.0.0")


# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------


if page == "Dashboard":

    st.title("SenX Business Intelligence Dashboard")

    st.write(
        "Monitor your business performance using live data "
        "stored in your MySQL database."
    )

    try:
        # Load selected dataset from MySQL
        rows = load_selected_mysql_dataset()

        if not rows:
            st.stop()

        # Calculate business analytics
        result = analyze_sales(rows)
        summary = result["summary"]

        st.divider()

        st.subheader("Executive Overview")

        # First row of KPIs
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Revenue",
                f"{summary['total_revenue']:,.2f}"
            )

        with col2:
            st.metric(
                "Total Profit",
                f"{summary['total_profit']:,.2f}"
            )

        with col3:
            st.metric(
                "Total Orders",
                f"{summary['total_orders']:,}"
            )

        with col4:
            st.metric(
                "Total Customers",
                f"{summary['total_customers']:,}"
            )

        st.divider()

        st.subheader("Additional Business Metrics")

        # Second row of KPIs
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Average Order Value",
                f"{summary['average_order_value']:,.2f}"
            )

        with col2:
            st.metric(
                "Profit Margin",
                f"{summary['profit_margin']:.2f}%"
            )

        with col3:
            st.metric(
                "Quantity Sold",
                f"{summary['total_quantity']:,.0f}"
            )

        with col4:
            st.metric(
                "Total Records",
                f"{summary['total_records']:,}"
            )

        st.divider()

        st.subheader("Dataset Information")

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            st.info(
                f"Successfully loaded {len(rows):,} records "
                "from MySQL."
            )

        with info_col2:
            st.success("Database analytics are active.")

    except Exception as error:
        st.error(f"Dashboard loading failed: {error}")

# --------------------------------------------------
# DATA UPLOAD PAGE
# --------------------------------------------------


elif page == "Data Upload":

    st.title("📂 Data Management")
    st.write(
        "Upload business data and inspect its quality "
        "before performing analytics."
    )

    st.divider()

    # Choose dataset source
    data_source = st.radio(
        "Select data source",
        ["Upload your own dataset", "Use SenX sample dataset"],
        horizontal=True
    )

    uploaded_file = None
    dataset_name = None

    if data_source == "Upload your own dataset":

        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv", "xlsx", "xlsm"]
        )

        if uploaded_file is not None:
            dataset_name = uploaded_file.name

    else:
        dataset_path = "data/raw/superstore.csv"

        st.info(
            "Using the included Sample Superstore dataset."
        )

        dataset_name = "superstore.csv"

    # Process selected dataset
    if uploaded_file is not None or data_source == "Use SenX sample dataset":

        try:

            source = (
                uploaded_file
                if uploaded_file is not None
                else dataset_path
            )

            with st.spinner("Analyzing your dataset..."):

                headers, rows = load_uploaded_dataset(source)
                report = profile_dataset(headers, rows)

            st.success("Dataset successfully analyzed!")

            st.divider()

            # Dataset information
            st.subheader("Dataset Overview")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total Records",
                f"{report['total_rows']:,}"
            )

            col2.metric(
                "Total Columns",
                report["total_columns"]
            )

            col3.metric(
                "Duplicate Rows",
                report["duplicate_rows"]
            )

            total_missing = sum(
                report["missing_values"].values()
            )

            col4.metric(
                "Missing Values",
                f"{total_missing:,}"
            )

            st.caption(f"Dataset: {dataset_name}")

            st.divider()

            # Dataset preview
            st.subheader("Dataset Preview")

            st.write(
                f"Showing the first {min(10, len(rows))} records."
            )

            render_table(rows[:10])

            st.divider()

            # Missing values analysis
            st.subheader("Data Quality Analysis")

            missing_rows = [
                {
                    "Column": column,
                    "Missing Values": count,
                    "Missing Percentage": round(
                        (count / report["total_rows"]) * 100, 2
                    ) if report["total_rows"] else 0
                }
                for column, count in report["missing_values"].items()
            ]

            st.markdown("#### Missing Values by Column")

            render_table(missing_rows)

            if total_missing == 0:
                st.success("No missing values detected.")
            else:
                st.warning(
                    f"Found {total_missing} missing values. "
                    "Cleaning will be implemented in the next phase."
                )

            if report["duplicate_rows"] == 0:
                st.success("No duplicate rows detected.")
            else:
                st.warning(
                    f"Found {report['duplicate_rows']} duplicate rows."
                )

            st.divider()

            # Numeric statistics
            st.subheader("Numeric Column Statistics")

            numeric_summary = report["numeric_summary"]

            if numeric_summary:

                statistics_rows = []

                for column, stats in numeric_summary.items():

                    statistics_rows.append({
                        "Column": column,
                        "Count": stats["count"],
                        "Sum": stats["sum"],
                        "Average": stats["average"],
                        "Minimum": stats["minimum"],
                        "Maximum": stats["maximum"]
                    })

                render_table(statistics_rows)

            else:
                st.info("No numeric columns detected.")

            st.divider()

            # Download data quality report
            st.subheader("Export Data Quality Report")

            report_buffer = io.StringIO()

            writer = csv.writer(report_buffer)

            writer.writerow(["Section", "Metric", "Value"])

            writer.writerow([
                "Overview",
                "Total Records",
                report["total_rows"]
            ])

            writer.writerow([
                "Overview",
                "Total Columns",
                report["total_columns"]
            ])

            writer.writerow([
                "Overview",
                "Duplicate Rows",
                report["duplicate_rows"]
            ])

            writer.writerow([
                "Overview",
                "Total Missing Values",
                total_missing
            ])

            for column, count in report["missing_values"].items():

                writer.writerow([
                    "Missing Values",
                    column,
                    count
                ])

            for column, stats in numeric_summary.items():

                for metric, value in stats.items():

                    writer.writerow([
                        "Numeric Statistics",
                        f"{column} - {metric}",
                        value
                    ])

            st.download_button(
                label="📥 Download Data Quality Report",
                data=report_buffer.getvalue().encode("utf-8-sig"),
                file_name="senx_data_quality_report.csv",
                mime="text/csv"
            )

        except FileNotFoundError:

            st.error(
                "Sample dataset not found. "
                "Check data/raw/superstore.csv."
            )

        except Exception as error:

            st.error(f"Dataset processing failed: {error}")

    else:

        st.info("Upload a CSV file to begin data analysis.")

# --------------------------------------------------
# DATA CLEANING PAGE
# --------------------------------------------------

elif page == "Data Cleaning":

    st.title("🧹 Data Cleaning")
    st.write(
        "Prepare reliable business data by removing "
        "duplicates and validating values."
    )

    st.divider()

    data_source = st.radio(
        "Choose dataset",
        [
            "Use SenX sample dataset",
            "Upload a CSV file"
        ],
        horizontal=True
    )

    uploaded_file = None

    if data_source == "Use SenX sample dataset":

        st.info("Selected: Sample Superstore dataset")

        source = "data/raw/superstore.csv"

    else:

        uploaded_file = st.file_uploader(
            "Upload CSV dataset",
            type=["csv"],
            key="cleaning_uploader"
        )

        source = uploaded_file

    remove_duplicates = st.checkbox(
        "Remove exact duplicate rows",
        value=True
    )

    st.caption(
        "Missing values are preserved. Invalid numeric and date "
        "values are converted to missing values and reported."
    )

    if st.button("🚀 Run Cleaning Pipeline", type="primary"):

        if source is None:

            st.warning("Please upload a CSV file first.")

        else:

            try:

                with st.spinner("Cleaning dataset..."):

                    headers, original_rows = load_csv(source)

                    cleaned_rows, cleaning_report = clean_dataset(
                        headers,
                        original_rows,
                        remove_duplicates=remove_duplicates
                    )

                    output_path = save_cleaned_csv(
                        headers,
                        cleaned_rows,
                        "data/processed/superstore_cleaned.csv"
                    )

                    st.session_state["senx_clean_headers"] = headers
                    st.session_state["senx_clean_rows"] = cleaned_rows
                    st.session_state["senx_clean_report"] = cleaning_report

                st.success("Data cleaning completed successfully!")

            except Exception as error:

                st.error(f"Cleaning failed: {error}")

    # Display results
    if "senx_clean_report" in st.session_state:

        report = st.session_state["senx_clean_report"]
        cleaned_rows = st.session_state["senx_clean_rows"]
        headers = st.session_state["senx_clean_headers"]

        st.divider()

        st.subheader("Cleaning Results")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Original Records",
            f"{report['original_rows']:,}"
        )

        col2.metric(
            "Cleaned Records",
            f"{report['cleaned_rows']:,}"
        )

        col3.metric(
            "Duplicates Removed",
            f"{report['duplicates_removed']:,}"
        )

        col4.metric(
            "Missing Values Remaining",
            f"{report['total_missing_after']:,}",
            delta=(
                report['total_missing_before']
                - report['total_missing_after']
            )
        )

        st.divider()

        st.subheader("Before vs After")

        comparison = [
            {
                "Metric": "Total Records",
                "Before Cleaning": report["original_rows"],
                "After Cleaning": report["cleaned_rows"]
            },
            {
                "Metric": "Missing Values",
                "Before Cleaning": report["total_missing_before"],
                "After Cleaning": report["total_missing_after"]
            },
            {
                "Metric": "Duplicate Rows",
                "Before Cleaning": report["duplicates_removed"],
                "After Cleaning": 0
            }
        ]

        render_table(comparison)

        st.divider()

        st.subheader("Missing Values by Column")

        missing_comparison = []

        for column in headers:

            missing_comparison.append({
                "Column": column,
                "Before Cleaning": report["missing_before"][column],
                "After Cleaning": report["missing_after"][column]
            })

        render_table(missing_comparison)

        st.divider()

        st.subheader("Invalid Values")

        invalid_rows = [
            {
                "Column": column,
                "Invalid Values": count
            }
            for column, count in report["invalid_values"].items()
        ]

        if invalid_rows:
            render_table(invalid_rows)
        else:
            st.success("No invalid numeric or date values detected.")

        st.divider()

        st.subheader("Cleaned Dataset Preview")

        render_table(cleaned_rows[:10])

        st.divider()

        st.subheader("Download Cleaned Dataset")

        csv_buffer = io.StringIO()

        writer = csv.DictWriter(
            csv_buffer,
            fieldnames=headers
        )

        writer.writeheader()
        writer.writerows(cleaned_rows)

        st.download_button(
            label="📥 Download Cleaned Dataset",
            data=csv_buffer.getvalue().encode("utf-8-sig"),
            file_name="superstore_cleaned.csv",
            mime="text/csv"
        )

        st.caption(
            "A copy is also saved in data/processed/. "
            "The original raw dataset remains unchanged."
        )
        
        st.divider()

        st.subheader("Import Cleaned Dataset into MySQL")

        st.write(
            "Save the cleaned dataset in your SenX database "
            "so that it becomes available across all analytics pages."
        )

        if st.button(
            "Import Cleaned Dataset to MySQL",
            type="primary",
            key="senx_import_cleaned_dataset"
        ):

            with st.spinner("Importing dataset into MySQL..."):

                import_result = import_cleaned_dataset(
                    headers=headers,
                    rows=cleaned_rows,
                    filename=(
                        uploaded_file.name
                        if uploaded_file is not None
                        else "superstore_cleaned.csv"
                    )
                )

            if import_result["success"]:

                st.success(import_result["message"])

                st.write(
                    f"Dataset ID: {import_result['dataset_id']}"
                )

                st.write(
                    f"Records imported: "
                    f"{import_result['records_imported']:,}"
                )

            elif import_result.get("duplicate"):

                st.info(import_result["message"])

                st.write(
                    f"Existing Dataset ID: "
                    f"{import_result['dataset_id']}"
                )

            else:

                st.error(import_result["message"])



# --------------------------------------------------
# SALES ANALYTICS PAGE
# --------------------------------------------------

elif page == "Sales Analytics":

    st.title("📈 Sales Analytics")

    st.write(
        "Understand business performance through "
        "revenue, profitability, product and regional analysis."
    )

    st.divider()

    try:

        # Load selected dataset directly from MySQL
        rows = load_selected_mysql_dataset()

        if not rows:
            st.stop()

        # Calculate analytics
        result = analyze_sales(rows)

        summary = result["summary"]

        st.success(
            f"Analytics generated from {len(rows):,} cleaned records."
        )

        # --------------------------------------------------
        # EXECUTIVE KPIs
        # --------------------------------------------------

        st.subheader("Executive Performance")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Revenue",
            f"₹{summary['total_revenue']:,.2f}"
        )

        col2.metric(
            "Total Profit",
            f"₹{summary['total_profit']:,.2f}"
        )

        col3.metric(
            "Total Orders",
            f"{summary['total_orders']:,}"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Customers",
            f"{summary['total_customers']:,}"
        )

        col2.metric(
            "Average Order Value",
            f"₹{summary['average_order_value']:,.2f}"
        )

        col3.metric(
            "Profit Margin",
            f"{summary['profit_margin']:.2f}%"
        )

        st.divider()

        # --------------------------------------------------
        # MONTHLY REVENUE
        # --------------------------------------------------

        st.subheader("Monthly Revenue Trend")

        monthly_data = result["monthly_revenue"]

        if monthly_data:

            monthly_figure = go.Figure()

            monthly_figure.add_trace(
                go.Scatter(
                    x=[item["month"] for item in monthly_data],
                    y=[item["revenue"] for item in monthly_data],
                    mode="lines+markers",
                    name="Revenue",
                    line=dict(width=3)
                )
            )

            monthly_figure.update_layout(
                xaxis_title="Month",
                yaxis_title="Revenue (₹)",
                hovermode="x unified",
                template="plotly_white"
            )

            st.plotly_chart(
                monthly_figure,
                use_container_width=True
            )

        else:

            st.info("No valid order dates available.")

        st.divider()

        # --------------------------------------------------
        # CATEGORY ANALYSIS
        # --------------------------------------------------

        st.subheader("Category Performance")

        categories = result["categories"]

        if categories:

            category_figure = go.Figure()

            category_figure.add_trace(
                go.Bar(
                    x=[item["name"] for item in categories],
                    y=[item["sales"] for item in categories],
                    name="Revenue"
                )
            )

            category_figure.update_layout(
                xaxis_title="Category",
                yaxis_title="Revenue (₹)",
                template="plotly_white"
            )

            st.plotly_chart(
                category_figure,
                use_container_width=True
            )

            category_table = [
                {
                    "Category": item["name"],
                    "Revenue": item["sales"],
                    "Profit": item["profit"],
                    "Quantity Sold": item["quantity"]
                }
                for item in categories
            ]

            render_table(category_table)

        st.divider()

        # --------------------------------------------------
        # REGIONAL ANALYSIS
        # --------------------------------------------------

        st.subheader("Regional Sales Performance")

        regions = result["regions"]

        if regions:

            region_figure = go.Figure()

            region_figure.add_trace(
                go.Bar(
                    x=[item["name"] for item in regions],
                    y=[item["sales"] for item in regions],
                    name="Regional Revenue"
                )
            )

            region_figure.update_layout(
                xaxis_title="Region",
                yaxis_title="Revenue (₹)",
                template="plotly_white"
            )

            st.plotly_chart(
                region_figure,
                use_container_width=True
            )

            region_table = [
                {
                    "Region": item["name"],
                    "Revenue": item["sales"],
                    "Profit": item["profit"]
                }
                for item in regions
            ]

            render_table(region_table)

        st.divider()

        # --------------------------------------------------
        # TOP PRODUCTS
        # --------------------------------------------------

        st.subheader("Top 10 Products by Revenue")

        top_products = result["products"][:10]

        if top_products:

            product_figure = go.Figure()

            product_figure.add_trace(
                go.Bar(
                    x=[item["sales"] for item in top_products],
                    y=[item["name"] for item in top_products],
                    orientation="h",
                    name="Product Revenue"
                )
            )

            product_figure.update_layout(
                xaxis_title="Revenue (₹)",
                yaxis_title="Product",
                yaxis=dict(autorange="reversed"),
                height=500,
                template="plotly_white"
            )

            st.plotly_chart(
                product_figure,
                use_container_width=True
            )

        st.divider()

        # --------------------------------------------------
        # BUSINESS INSIGHTS
        # --------------------------------------------------

        st.subheader("Business Insights")

        if categories:

            best_category = categories[0]

            st.info(
                f"Highest-revenue category: "
                f"{best_category['name']} "
                f"(₹{best_category['sales']:,.2f})."
            )

        if regions:

            best_region = regions[0]

            st.info(
                f"Highest-revenue region: "
                f"{best_region['name']} "
                f"(₹{best_region['sales']:,.2f})."
            )

        if top_products:

            best_product = top_products[0]

            st.info(
                f"Highest-revenue product: "
                f"{best_product['name']} "
                f"(₹{best_product['sales']:,.2f})."
            )

        st.caption(
            "Insights are calculated from the loaded dataset. "
            "They are descriptive, not predictive."
        )

    except FileNotFoundError:

        st.error(
            "Dataset not found. Please place superstore.csv "
            "inside data/raw/."
        )

    except Exception as error:

        st.error(f"Sales analytics failed: {error}")


# --------------------------------------------------
# CUSTOMER ANALYTICS PAGE
# --------------------------------------------------

elif page == "Customer Analytics":

    st.title("👥 Customer Intelligence")

    st.write(
        "Analyze customer purchasing behavior, "
        "identify valuable customers and understand retention opportunities."
    )

    st.divider()

    try:

        # Load selected dataset directly from MySQL
        rows = load_selected_mysql_dataset()

        if not rows:
            st.stop()

        # CLV assumption
        lifespan = st.slider(
            "Expected customer lifespan (years)",
            min_value=1,
            max_value=10,
            value=3,
            help="Used only for the illustrative CLV estimate."
        )

        result = analyze_customers(
            rows,
            expected_lifespan_years=lifespan
        )

        summary = result["summary"]

        st.success(
            f"Analyzed {summary['total_customers']:,} customers."
        )

        # --------------------------------------------------
        # CUSTOMER KPIs
        # --------------------------------------------------

        st.subheader("Customer Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Customers",
            f"{summary['total_customers']:,}"
        )

        col2.metric(
            "Repeat Customers",
            f"{summary['repeat_customers']:,}"
        )

        col3.metric(
            "Repeat Purchase Rate",
            f"{summary['repeat_customer_percentage']:.2f}%"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average Customer Spend",
            f"₹{summary['average_customer_spend']:,.2f}"
        )

        col2.metric(
            "Customer Revenue",
            f"₹{summary['total_customer_revenue']:,.2f}"
        )

        col3.metric(
            "Observation Period",
            f"{summary['observation_days']:,} days"
        )

        st.caption(
            f"Latest transaction date: {summary['reference_date']}"
        )

        st.divider()

        # --------------------------------------------------
        # RFM EXPLANATION
        # --------------------------------------------------

        st.subheader("RFM Customer Segmentation")

        st.markdown("""
        | Metric | Meaning | Better score |
        |---|---|---|
        | Recency | Days since last purchase | Higher = more recent |
        | Frequency | Number of distinct orders | Higher = more orders |
        | Monetary | Total historical spending | Higher = more spending |
        """)

        st.info(
            "Each customer receives three scores from 1 to 5. "
            "For Recency, fewer days since the last purchase "
            "produce a higher score."
        )

        # --------------------------------------------------
        # SEGMENT DISTRIBUTION
        # --------------------------------------------------

        st.subheader("Customer Segment Distribution")

        segments = result["segments"]

        if segments:

            col1, col2 = st.columns(2)

            with col1:

                segment_figure = go.Figure(
                    data=[
                        go.Pie(
                            labels=[
                                item["segment"]
                                for item in segments
                            ],
                            values=[
                                item["customers"]
                                for item in segments
                            ],
                            hole=0.45
                        )
                    ]
                )

                segment_figure.update_layout(
                    title="Customers by Segment",
                    template="plotly_white"
                )

                st.plotly_chart(
                    segment_figure,
                    use_container_width=True
                )

            with col2:

                revenue_figure = go.Figure()

                revenue_figure.add_trace(
                    go.Bar(
                        x=[
                            item["segment"]
                            for item in segments
                        ],
                        y=[
                            item["revenue"]
                            for item in segments
                        ],
                        name="Revenue"
                    )
                )

                revenue_figure.update_layout(
                    title="Revenue by Customer Segment",
                    xaxis_title="Segment",
                    yaxis_title="Revenue (₹)",
                    template="plotly_white"
                )

                st.plotly_chart(
                    revenue_figure,
                    use_container_width=True
                )

            render_table(segments)

        st.divider()

        # --------------------------------------------------
        # CUSTOMER SEGMENT FILTER
        # --------------------------------------------------

        st.subheader("Customer Explorer")

        customers = result["customers"]

        available_segments = [
            "All Segments"
        ] + sorted({
            customer["segment"]
            for customer in customers
        })

        selected_segment = st.selectbox(
            "Filter by customer segment",
            available_segments
        )

        if selected_segment == "All Segments":

            filtered_customers = customers

        else:

            filtered_customers = [
                customer
                for customer in customers
                if customer["segment"] == selected_segment
            ]

        customer_table = [
            {
                "Customer ID": customer["customer_id"],
                "Customer Name": customer["customer_name"],
                "Recency (Days)": customer["recency_days"],
                "Frequency": customer["frequency"],
                "Monetary (₹)": customer["monetary"],
                "RFM Score": customer["rfm_score"],
                "Segment": customer["segment"]
            }
            for customer in filtered_customers[:50]
        ]

        st.caption(
            f"Showing {min(50, len(filtered_customers))} "
            f"of {len(filtered_customers)} matching customers."
        )

        render_table(customer_table)

        st.divider()

        # --------------------------------------------------
        # CUSTOMER VALUE ANALYSIS
        # --------------------------------------------------

        st.subheader("Estimated Customer Lifetime Value")

        st.caption(
            "This is a simple historical-spending projection, "
            "not a predictive machine-learning model."
        )

        clv_customers = sorted(
            customers,
            key=lambda customer: customer["estimated_clv"],
            reverse=True
        )

        top_clv = [
            {
                "Customer ID": customer["customer_id"],
                "Customer Name": customer["customer_name"],
                "Historical Spend (₹)": customer["monetary"],
                "Estimated Annual Spend (₹)": customer[
                    "estimated_annual_spending"
                ],
                "Estimated CLV (₹)": customer["estimated_clv"]
            }
            for customer in clv_customers[:10]
        ]

        render_table(top_clv)

        # --------------------------------------------------
        # DOWNLOAD CUSTOMER REPORT
        # --------------------------------------------------

        st.divider()

        st.subheader("Download Customer Analytics")

        customer_csv = io.StringIO()

        customer_fields = [
            "customer_id",
            "customer_name",
            "recency_days",
            "frequency",
            "monetary",
            "average_order_value",
            "rfm_score",
            "segment",
            "estimated_annual_spending",
            "estimated_clv"
        ]

        writer = csv.DictWriter(
            customer_csv,
            fieldnames=customer_fields
        )

        writer.writeheader()

        for customer in customers:
            writer.writerow({
                field: customer.get(field)
                for field in customer_fields
            })

        st.download_button(
            label="📥 Download Customer Analytics CSV",
            data=customer_csv.getvalue().encode("utf-8-sig"),
            file_name="senx_customer_analytics.csv",
            mime="text/csv"
        )

    except Exception as error:

        st.error(f"Customer analytics failed: {error}")


# --------------------------------------------------
# FORECASTING PAGE
# --------------------------------------------------

elif page == "Forecasting":

    st.title("🔮 Sales Forecasting")

    st.write(
        "Estimate future monthly revenue using "
        "historical sales data and evaluate model performance."
    )

    st.divider()

    
    try:
        # Load the selected dataset directly from MySQL
        rows = load_selected_mysql_dataset()

        if not rows:
            st.stop()

        forecast_horizon = st.slider(

            "Forecast horizon (months)",
            min_value=1,
            max_value=12,
            value=3
        )

        result = forecast_sales(
            rows,
            forecast_horizon=forecast_horizon
        )

        st.success(
            "Sales forecasting model trained and evaluated."
        )

        # --------------------------------------------------
        # MODEL INFORMATION
        # --------------------------------------------------

        st.subheader("Model Information")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Forecasting Model",
            result["model"]
        )

        col2.metric(
            "Training Months",
            result["training_months"]
        )

        col3.metric(
            "Testing Months",
            result["testing_months"]
        )

        st.caption(
            "Chronological train/test split: "
            "the latest observations are reserved for testing."
        )

        st.divider()

        # --------------------------------------------------
        # MODEL EVALUATION
        # --------------------------------------------------

        st.subheader("Model Evaluation")

        model_metrics = result["model_metrics"]
        baseline_metrics = result["baseline_metrics"]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Model MAE",
            f"₹{model_metrics['mae']:,.2f}"
        )

        col2.metric(
            "Model RMSE",
            f"₹{model_metrics['rmse']:,.2f}"
        )

        col3.metric(
            "Model MAPE",
            (
                f"{model_metrics['mape']:.2f}%"
                if model_metrics["mape"] is not None
                else "N/A"
            )
        )

        st.markdown("#### Baseline Comparison")

        comparison = [
            {
                "Metric": "MAE",
                "Linear Model": model_metrics["mae"],
                "Baseline": baseline_metrics["mae"]
            },
            {
                "Metric": "RMSE",
                "Linear Model": model_metrics["rmse"],
                "Baseline": baseline_metrics["rmse"]
            },
            {
                "Metric": "MAPE (%)",
                "Linear Model": model_metrics["mape"],
                "Baseline": baseline_metrics["mape"]
            }
        ]

        render_table(comparison)

        if result["model_is_better"]:

            st.success(
                "The linear trend model achieved lower MAE "
                "than the baseline on the test period."
            )

        else:

            st.warning(
                "The baseline achieved equal or lower MAE. "
                "The linear model is not currently outperforming "
                "the baseline."
            )

        st.divider()

        # --------------------------------------------------
        # ACTUAL VS PREDICTED
        # --------------------------------------------------

        st.subheader("Actual vs Predicted Revenue")

        evaluation = result["evaluation"]

        evaluation_figure = go.Figure()

        evaluation_figure.add_trace(
            go.Scatter(
                x=[item["month"] for item in evaluation],
                y=[item["actual"] for item in evaluation],
                mode="lines+markers",
                name="Actual Revenue"
            )
        )

        evaluation_figure.add_trace(
            go.Scatter(
                x=[item["month"] for item in evaluation],
                y=[item["predicted"] for item in evaluation],
                mode="lines+markers",
                name="Linear Model Prediction"
            )
        )

        evaluation_figure.add_trace(
            go.Scatter(
                x=[item["month"] for item in evaluation],
                y=[item["baseline"] for item in evaluation],
                mode="lines",
                name="Baseline Prediction"
            )
        )

        evaluation_figure.update_layout(
            xaxis_title="Month",
            yaxis_title="Revenue (₹)",
            hovermode="x unified",
            template="plotly_white"
        )

        st.plotly_chart(
            evaluation_figure,
            use_container_width=True
        )

        evaluation_table = [
            {
                "Month": item["month"],
                "Actual Revenue": item["actual"],
                "Model Prediction": item["predicted"],
                "Baseline Prediction": item["baseline"]
            }
            for item in evaluation
        ]

        render_table(evaluation_table)

        st.divider()

        # --------------------------------------------------
        # FUTURE FORECAST
        # --------------------------------------------------

        st.subheader("Future Revenue Forecast")

        forecasts = result["future_forecasts"]

        forecast_figure = go.Figure()

        forecast_figure.add_trace(
            go.Scatter(
                x=[item["month"] for item in result["history"]],
                y=[item["revenue"] for item in result["history"]],
                mode="lines+markers",
                name="Historical Revenue"
            )
        )

        forecast_figure.add_trace(
            go.Scatter(
                x=[item["month"] for item in forecasts],
                y=[
                    item["predicted_revenue"]
                    for item in forecasts
                ],
                mode="lines+markers",
                name="Forecast Revenue",
                line=dict(dash="dash")
            )
        )

        forecast_figure.update_layout(
            xaxis_title="Month",
            yaxis_title="Revenue (₹)",
            hovermode="x unified",
            template="plotly_white"
        )

        st.plotly_chart(
            forecast_figure,
            use_container_width=True
        )

        forecast_table = [
            {
                "Forecast Month": item["month"],
                "Predicted Revenue": item["predicted_revenue"]
            }
            for item in forecasts
        ]

        render_table(forecast_table)

        st.divider()

        # --------------------------------------------------
        # DOWNLOAD FORECAST
        # --------------------------------------------------

        st.subheader("Export Forecast Results")

        forecast_buffer = io.StringIO()

        writer = csv.writer(forecast_buffer)

        writer.writerow([
            "Month",
            "Predicted Revenue"
        ])

        for item in forecasts:

            writer.writerow([
                item["month"],
                item["predicted_revenue"]
            ])

        st.download_button(
            label="📥 Download Sales Forecast",
            data=forecast_buffer.getvalue().encode("utf-8-sig"),
            file_name="senx_sales_forecast.csv",
            mime="text/csv"
        )

        st.caption(
            "Forecasts are experimental linear-trend estimates. "
            "They do not account for seasonality, promotions, "
            "holidays or external economic factors."
        )

    except Exception as error:

        st.error(f"Forecasting failed: {error}")

elif page == "Dataset Management":

    st.title("Dataset Management")

    st.write(
        "View and monitor all completed datasets stored "
        "in your SenX MySQL database."
    )

    st.divider()

    try:

        # Retrieve datasets from MySQL
        datasets = get_dataset_list()

        if not datasets:

            st.warning(
                "No completed datasets found. "
                "Import a dataset from the Data Cleaning page."
            )

        else:

            # Dataset statistics
            total_datasets = len(datasets)

            total_records = sum(
                item["row_count"] for item in datasets
            )

            total_columns = max(
                item["column_count"] for item in datasets
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Datasets",
                f"{total_datasets:,}"
            )

            col2.metric(
                "Total Records",
                f"{total_records:,}"
            )

            col3.metric(
                "Latest Dataset Columns",
                f"{total_columns:,}"
            )

            st.divider()

            st.subheader("Imported Datasets")

            # Prepare dataset information for display
            dataset_table = []

            for item in datasets:

                uploaded_at = item["uploaded_at"]

                if uploaded_at:
                    uploaded_at = uploaded_at.strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                else:
                    uploaded_at = "Not available"

                dataset_table.append({
                    "Dataset ID": item["id"],
                    "Filename": item["filename"],
                    "Records": f"{item['row_count']:,}",
                    "Columns": item["column_count"],
                    "Uploaded At": uploaded_at,
                    "Status": "Completed"
                })

            render_table(dataset_table)

            st.divider()

            st.subheader("Dataset Details")

            dataset_options = {
                (
                    f"{item['filename']} "
                    f"(ID: {item['id']})"
                ): item["id"]
                for item in datasets
            }

            selected_label = st.selectbox(
                "Select a dataset",
                options=list(dataset_options.keys()),
                key="senx_management_dataset_selector"
            )

            selected_id = dataset_options[selected_label]

            selected_dataset = next(
                item for item in datasets
                if item["id"] == selected_id
            )

            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:

                st.info(
                    f"Dataset ID: {selected_dataset['id']}"
                )

                st.info(
                    f"Filename: {selected_dataset['filename']}"
                )

            with detail_col2:

                st.info(
                    f"Records: "
                    f"{selected_dataset['row_count']:,}"
                )

                st.info(
                    f"Columns: "
                    f"{selected_dataset['column_count']:,}"
                )

            st.success(
                "Dataset is successfully stored in MySQL."
            )
            
            st.divider()

            st.subheader("Delete Dataset")

            st.warning(
                "Deleting a dataset permanently removes it "
                "and its associated sales records from MySQL."
            )

            delete_options = {
                f"{item['filename']} (ID: {item['id']})": item["id"]
                for item in datasets
            }

            dataset_to_delete = st.selectbox(
                "Select dataset to delete",
                options=list(delete_options.keys()),
                key="senx_delete_dataset_selector"
            )

            selected_delete_id = delete_options[dataset_to_delete]

            confirm_delete = st.checkbox(
                "I understand that this action cannot be undone.",
                key="senx_confirm_delete"
            )

            if st.button(
                "Delete Selected Dataset",
                type="primary",
                disabled=not confirm_delete
            ):
                with st.spinner("Deleting dataset..."):

                    delete_result = delete_dataset(
                        selected_delete_id
                    )

                if delete_result["success"]:
                    st.success(delete_result["message"])

                    st.rerun()

                else:
                    st.error(delete_result["message"])


    except Exception as error:

        st.error(
            f"Dataset management failed: {error}"
        )

# --------------------------------------------------
# REPORTS PAGE
# --------------------------------------------------


elif page == "Reports":

    st.title("Business Reports")
    st.write(
        "Generate and download executive business reports "
        "using your MySQL dataset."
    )

    try:
        # Load dataset from MySQL
        rows = load_selected_mysql_dataset()

        if not rows:
            st.stop()

        # Identify dataset columns
        headers = list(rows[0].keys())

        # Calculate business analytics
        result = analyze_sales(rows)
        summary = result["summary"]

        st.divider()

        st.subheader("Report Preview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Revenue",
                f"{summary['total_revenue']:,.2f}"
            )

        with col2:
            st.metric(
                "Total Profit",
                f"{summary['total_profit']:,.2f}"
            )

        with col3:
            st.metric(
                "Total Orders",
                f"{summary['total_orders']:,}"
            )

        st.divider()

        st.subheader("Download Reports")

        col1, col2 = st.columns(2)

        # PDF Report
        with col1:
            st.markdown("### PDF Executive Report")
            st.write(
                "Download a professional PDF containing "
                "your business KPIs and executive summary."
            )

            pdf_file = generate_pdf_report(summary)

            st.download_button(
                label="Download PDF Report",
                data=pdf_file,
                file_name="SenX_Business_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        # Excel Report
        with col2:
            st.markdown("### Excel Business Report")
            st.write(
                "Download an Excel workbook containing "
                "business KPIs and the complete sales dataset."
            )

            excel_file = generate_excel_report(
                headers,
                rows,
                summary
            )

            st.download_button(
                label="Download Excel Report",
                data=excel_file,
                file_name="SenX_Business_Report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True
            )

    except Exception as error:
        st.error(f"Report generation failed: {error}")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.sidebar.divider()
st.sidebar.caption("Built with Python and Streamlit")
