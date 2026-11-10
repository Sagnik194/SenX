
from modules.customer_analysis import analyze_customers


def get_sample_customers():
    return [
        {
            "Customer ID": "C001",
            "Customer Name": "Customer One",
            "Order ID": "ORD001",
            "Order Date": "01/01/2025",
            "Sales": "500",
        },
        {
            "Customer ID": "C001",
            "Customer Name": "Customer One",
            "Order ID": "ORD002",
            "Order Date": "10/01/2025",
            "Sales": "300",
        },
        {
            "Customer ID": "C002",
            "Customer Name": "Customer Two",
            "Order ID": "ORD003",
            "Order Date": "15/01/2025",
            "Sales": "200",
        },
    ]


def test_customer_count():
    result = analyze_customers(get_sample_customers())

    assert result["summary"]["total_customers"] == 2


def test_customer_purchase_frequency():
    result = analyze_customers(get_sample_customers())

    customers = result["customers"]

    customer_one = next(
        customer for customer in customers
        if customer["customer_id"] == "C001"
    )

    assert customer_one["frequency"] == 2


def test_customer_monetary_value():
    result = analyze_customers(get_sample_customers())

    customers = result["customers"]

    customer_one = next(
        customer for customer in customers
        if customer["customer_id"] == "C001"
    )

    assert customer_one["monetary"] == 800



def test_customer_clv_is_positive():
    result = analyze_customers(get_sample_customers())

    for customer in result["customers"]:
        assert customer["estimated_clv"] > 0



def test_rfm_scores_are_within_valid_range():
    result = analyze_customers(get_sample_customers())

    for customer in result["customers"]:
        assert 1 <= customer["recency_days_score"] <= 5
        assert 1 <= customer["frequency_score"] <= 5
        assert 1 <= customer["monetary_score"] <= 5
