
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation


def get_value(row, column_name):
    """Find a column without depending on capitalization."""

    for key, value in row.items():
        if key.strip().casefold() == column_name.casefold():
            return value

    return None


def to_number(value):
    """Convert a value safely into Decimal."""

    if value is None:
        return Decimal("0")

    try:
        number = Decimal(str(value).replace(",", ""))

        if not number.is_finite():
            return Decimal("0")

        return number

    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_date(value):
    """Parse supported date formats."""

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



def calculate_rfm_scores(customers):
    """
    Assign scores from 1 to 5.
    Identical metric values receive identical scores.
    """

    if not customers:
        return customers

    def assign_scores(metric, higher_is_better=True):

        unique_values = sorted(
            {customer[metric] for customer in customers},
            reverse=not higher_is_better
        )

        total_unique = len(unique_values)

        score_mapping = {}

        for index, value in enumerate(unique_values):

            score_mapping[value] = min(
                5,
                (index * 5 // total_unique) + 1
            )

        for customer in customers:

            customer[f"{metric}_score"] = score_mapping[
                customer[metric]
            ]

    assign_scores("recency_days", higher_is_better=False)
    assign_scores("frequency", higher_is_better=True)
    assign_scores("monetary", higher_is_better=True)

    for customer in customers:

        r = customer["recency_days_score"]
        f = customer["frequency_score"]
        m = customer["monetary_score"]

        customer["rfm_score"] = f"{r}{f}{m}"

        if r >= 4 and f >= 4 and m >= 4:
            segment = "Champions"

        elif f >= 4 and m >= 3:
            segment = "Loyal Customers"

        elif r >= 4 and f >= 2:
            segment = "Potential Loyalists"

        elif r <= 2 and f >= 3:
            segment = "At Risk"

        elif r <= 2 and f <= 2:
            segment = "Hibernating"

        elif r >= 4:
            segment = "Recent Customers"

        else:
            segment = "Others"

        customer["segment"] = segment

    return customers

def analyze_customers(rows, expected_lifespan_years=3):
    """
    Perform customer-level RFM and spending analysis.

    CLV is a simple historical-spending projection,
    not a trained predictive model.
    """

    customer_data = defaultdict(
        lambda: {
            "name": "Unknown",
            "orders": set(),
            "monetary": Decimal("0"),
            "dates": []
        }
    )

    all_dates = []

    # --------------------------------------------------
    # Aggregate transaction records by customer
    # --------------------------------------------------

    for row in rows:

        customer_id = get_value(row, "Customer ID")

        if not customer_id:
            continue

        customer_name = (
            get_value(row, "Customer Name") or "Unknown"
        )

        order_id = get_value(row, "Order ID")

        sales = to_number(
            get_value(row, "Sales")
        )

        order_date = parse_date(
            get_value(row, "Order Date")
        )

        customer = customer_data[customer_id]

        customer["name"] = customer_name
        customer["monetary"] += sales

        if order_id:
            customer["orders"].add(order_id)

        if order_date:
            customer["dates"].append(order_date)
            all_dates.append(order_date)

    if not customer_data:
        return {
            "summary": {},
            "customers": [],
            "segments": [],
            "observation_days": 0
        }

    if not all_dates:
        raise ValueError(
            "No valid order dates found for customer analysis."
        )

    # --------------------------------------------------
    # Calculate observation period
    # --------------------------------------------------

    first_date = min(all_dates)
    reference_date = max(all_dates)

    observation_days = max(
        1,
        (reference_date - first_date).days + 1
    )

    # --------------------------------------------------
    # Calculate customer RFM values
    # --------------------------------------------------

    customers = []

    for customer_id, data in customer_data.items():

        if not data["dates"]:
            continue

        recency_days = (
            reference_date - max(data["dates"])
        ).days

        frequency = len(data["orders"])
        monetary = data["monetary"]

        average_order_value = (
            monetary / frequency
            if frequency else Decimal("0")
        )

        annual_spending = (
            monetary * Decimal("365") / observation_days
        )

        estimated_clv = (
            annual_spending * Decimal(
                str(expected_lifespan_years)
            )
        )

        customers.append({
            "customer_id": customer_id,
            "customer_name": data["name"],
            "recency_days": recency_days,
            "frequency": frequency,
            "monetary": round(float(monetary), 2),
            "average_order_value": round(
                float(average_order_value), 2
            ),
            "estimated_annual_spending": round(
                float(annual_spending), 2
            ),
            "estimated_clv": round(
                float(estimated_clv), 2
            )
        })

    # --------------------------------------------------
    # RFM segmentation
    # --------------------------------------------------

    customers = calculate_rfm_scores(customers)

    customers.sort(
        key=lambda customer: customer["monetary"],
        reverse=True
    )

    # --------------------------------------------------
    # Segment-level summary
    # --------------------------------------------------

    segment_data = defaultdict(
        lambda: {
            "customers": 0,
            "revenue": 0.0
        }
    )

    for customer in customers:

        segment = customer["segment"]

        segment_data[segment]["customers"] += 1

        segment_data[segment]["revenue"] += (
            customer["monetary"]
        )

    segments = []

    for segment, values in segment_data.items():

        segments.append({
            "segment": segment,
            "customers": values["customers"],
            "revenue": round(values["revenue"], 2)
        })

    segments.sort(
        key=lambda item: item["customers"],
        reverse=True
    )

    # --------------------------------------------------
    # Customer summary
    # --------------------------------------------------

    total_customers = len(customers)

    total_revenue = sum(
        customer["monetary"]
        for customer in customers
    )

    repeat_customers = sum(
        1 for customer in customers
        if customer["frequency"] > 1
    )

    average_customer_spend = (
        total_revenue / total_customers
        if total_customers else 0
    )

    summary = {
        "total_customers": total_customers,
        "repeat_customers": repeat_customers,
        "repeat_customer_percentage": round(
            repeat_customers / total_customers * 100, 2
        ) if total_customers else 0,
        "average_customer_spend": round(
            average_customer_spend, 2
        ),
        "total_customer_revenue": round(
            total_revenue, 2
        ),
        "observation_days": observation_days,
        "reference_date": reference_date.strftime("%Y-%m-%d")
    }

    return {
        "summary": summary,
        "customers": customers,
        "segments": segments,
        "observation_days": observation_days
    }
