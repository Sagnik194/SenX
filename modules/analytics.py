
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from datetime import datetime


def get_value(row, column_name):
    """Find a column without depending on capitalization."""

    for key, value in row.items():
        if key.strip().casefold() == column_name.casefold():
            return value

    return None


def to_number(value):
    """Safely convert a value into Decimal."""

    if value is None:
        return Decimal("0")

    try:
        number = Decimal(str(value).replace(",", ""))

        if not number.is_finite():
            return Decimal("0")

        return number

    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_order_date(value):
    """Parse supported order date formats."""

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y"
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return None


def analyze_sales(rows):
    """
    Calculate business KPIs and sales breakdowns.

    Input:
        List of cleaned dictionaries.

    Output:
        Dictionary containing summary and grouped analytics.
    """

    revenue = Decimal("0")
    profit = Decimal("0")
    total_quantity = Decimal("0")

    order_ids = set()
    customer_ids = set()

    category_data = defaultdict(
        lambda: {
            "sales": Decimal("0"),
            "profit": Decimal("0"),
            "quantity": Decimal("0")
        }
    )

    region_data = defaultdict(
        lambda: {
            "sales": Decimal("0"),
            "profit": Decimal("0")
        }
    )

    product_data = defaultdict(
        lambda: {
            "sales": Decimal("0"),
            "profit": Decimal("0"),
            "quantity": Decimal("0")
        }
    )

    monthly_revenue = defaultdict(
        lambda: Decimal("0")
    )

    valid_sales_rows = 0
    invalid_date_rows = 0

    for row in rows:

        sales = to_number(get_value(row, "Sales"))
        row_profit = to_number(get_value(row, "Profit"))
        quantity = to_number(get_value(row, "Quantity"))

        order_id = get_value(row, "Order ID")
        customer_id = get_value(row, "Customer ID")

        category = get_value(row, "Category") or "Unknown"
        region = get_value(row, "Region") or "Unknown"
        product = get_value(row, "Product Name") or "Unknown"

        revenue += sales
        profit += row_profit
        total_quantity += quantity

        valid_sales_rows += 1

        if order_id:
            order_ids.add(order_id)

        if customer_id:
            customer_ids.add(customer_id)

        # Category performance
        category_data[category]["sales"] += sales
        category_data[category]["profit"] += row_profit
        category_data[category]["quantity"] += quantity

        # Regional performance
        region_data[region]["sales"] += sales
        region_data[region]["profit"] += row_profit

        # Product performance
        product_data[product]["sales"] += sales
        product_data[product]["profit"] += row_profit
        product_data[product]["quantity"] += quantity

        # Monthly revenue
        order_date = parse_order_date(
            get_value(row, "Order Date")
        )

        if order_date:
            month = order_date.strftime("%Y-%m")
            monthly_revenue[month] += sales
        else:
            invalid_date_rows += 1

    total_orders = len(order_ids)
    total_customers = len(customer_ids)

    average_order_value = (
        revenue / total_orders
        if total_orders else Decimal("0")
    )

    profit_margin = (
        (profit / revenue) * 100
        if revenue else Decimal("0")
    )

    def format_number(value):
        return round(float(value), 2)

    def convert_groups(group_data):

        results = []

        for name, values in group_data.items():

            results.append({
                "name": name,
                "sales": format_number(values["sales"]),
                "profit": format_number(values["profit"]),
                "quantity": format_number(values["quantity"])
                if "quantity" in values else 0
            })

        return results

    categories = sorted(
        convert_groups(category_data),
        key=lambda item: item["sales"],
        reverse=True
    )

    regions = sorted(
        convert_groups(region_data),
        key=lambda item: item["sales"],
        reverse=True
    )

    products = sorted(
        convert_groups(product_data),
        key=lambda item: item["sales"],
        reverse=True
    )

    monthly = [
        {
            "month": month,
            "revenue": format_number(value)
        }
        for month, value in sorted(monthly_revenue.items())
    ]

    return {
        "summary": {
            "total_revenue": format_number(revenue),
            "total_profit": format_number(profit),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "average_order_value": format_number(average_order_value),
            "profit_margin": format_number(profit_margin),
            "total_quantity": format_number(total_quantity),
            "total_records": valid_sales_rows,
            "invalid_date_rows": invalid_date_rows
        },
        "categories": categories,
        "regions": regions,
        "products": products,
        "monthly_revenue": monthly
    }
