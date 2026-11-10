
from modules.analytics import analyze_sales


def test_sales_summary():
    rows = [
        {
            "Order ID": "ORD001",
            "Customer ID": "C001",
            "Order Date": "01/05/2025",
            "Category": "Technology",
            "Region": "East",
            "Product Name": "Laptop",
            "Sales": "200",
            "Profit": "40",
            "Quantity": "2",
        },
        {
            "Order ID": "ORD002",
            "Customer ID": "C002",
            "Order Date": "02/05/2025",
            "Category": "Furniture",
            "Region": "West",
            "Product Name": "Chair",
            "Sales": "100",
            "Profit": "10",
            "Quantity": "1",
        },
    ]

    result = analyze_sales(rows)
    summary = result["summary"]

    assert summary["total_revenue"] == 300
    assert summary["total_profit"] == 50
    assert summary["total_orders"] == 2
    assert summary["total_customers"] == 2
    assert summary["total_quantity"] == 3


def test_average_order_value():
    rows = [
        {
            "Order ID": "ORD001",
            "Customer ID": "C001",
            "Order Date": "01/05/2025",
            "Sales": "200",
            "Profit": "40",
            "Quantity": "2",
        },
        {
            "Order ID": "ORD002",
            "Customer ID": "C002",
            "Order Date": "02/05/2025",
            "Sales": "100",
            "Profit": "10",
            "Quantity": "1",
        },
    ]

    result = analyze_sales(rows)
    summary = result["summary"]

    assert summary["average_order_value"] == 150
