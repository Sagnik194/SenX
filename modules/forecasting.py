
from collections import defaultdict
from datetime import datetime
from math import ceil, sqrt


def get_value(row, column_name):
    """Find a column without depending on capitalization."""

    for key, value in row.items():
        if key.strip().casefold() == column_name.casefold():
            return value

    return None


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


def month_key(date_value):
    return date_value.year * 12 + date_value.month - 1


def month_label(key):
    year = key // 12
    month = key % 12 + 1

    return f"{year}-{month:02d}"


def to_number(value):
    try:
        number = float(str(value).replace(",", ""))

        if not is_finite(number):
            return 0.0

        return number

    except (TypeError, ValueError):
        return 0.0


def is_finite(value):
    return value == value and abs(value) != float("inf")


def aggregate_monthly_revenue(rows):
    """Aggregate sales into a continuous monthly time series."""

    monthly_totals = defaultdict(float)

    for row in rows:

        order_date = parse_date(
            get_value(row, "Order Date")
        )

        if order_date is None:
            continue

        sales = to_number(
            get_value(row, "Sales")
        )

        monthly_totals[month_key(order_date)] += sales

    if not monthly_totals:
        raise ValueError("No valid monthly sales data was found.")

    first_month = min(monthly_totals)
    last_month = max(monthly_totals)

    # Include months with no transactions as zero-revenue months.
    return [
        {
            "month": month_label(key),
            "revenue": round(monthly_totals.get(key, 0.0), 2)
        }
        for key in range(first_month, last_month + 1)
    ]


def linear_regression_fit(x_values, y_values):
    """Fit a simple linear regression using least squares."""

    count = len(x_values)

    if count < 2:
        raise ValueError("At least two observations are required.")

    mean_x = sum(x_values) / count
    mean_y = sum(y_values) / count

    denominator = sum(
        (x - mean_x) ** 2 for x in x_values
    )

    if denominator == 0:
        raise ValueError("Cannot fit a model with identical x values.")

    slope = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(x_values, y_values)
    ) / denominator

    intercept = mean_y - slope * mean_x

    return intercept, slope


def predict(intercept, slope, x):
    """Predict revenue for a time index."""

    return max(0.0, intercept + slope * x)


def evaluate_predictions(actual, predicted):
    """Calculate forecasting error metrics."""

    if not actual:
        raise ValueError("No test observations available.")

    errors = [
        prediction - real
        for real, prediction in zip(actual, predicted)
    ]

    mae = sum(abs(error) for error in errors) / len(errors)

    rmse = sqrt(
        sum(error ** 2 for error in errors) / len(errors)
    )

    percentage_errors = [
        abs(error) / abs(real) * 100
        for real, error in zip(actual, errors)
        if real != 0
    ]

    mape = (
        sum(percentage_errors) / len(percentage_errors)
        if percentage_errors else None
    )

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2) if mape is not None else None
    }


def forecast_sales(rows, forecast_horizon=3):
    """
    Train and evaluate a linear trend model.

    Uses the latest chronological observations as the test set.
    Also compares against a last-value baseline.
    """

    if forecast_horizon < 1:
        raise ValueError("Forecast horizon must be at least one month.")

    monthly_data = aggregate_monthly_revenue(rows)

    values = [
        item["revenue"]
        for item in monthly_data
    ]

    count = len(values)

    if count < 6:
        raise ValueError(
            "At least six months of historical data are required."
        )

    # Keep at least three months for testing.
    test_size = max(3, ceil(count * 0.20))
    test_size = min(test_size, count - 3)

    train_values = values[:-test_size]
    test_values = values[-test_size:]

    train_x = list(range(len(train_values)))
    test_x = list(range(len(train_values), count))

    # Train the linear trend model.
    intercept, slope = linear_regression_fit(
        train_x,
        train_values
    )

    model_predictions = [
        predict(intercept, slope, x)
        for x in test_x
    ]

    # Baseline: predict every test month using the last training month.
    baseline_predictions = [
        train_values[-1]
        for _ in test_values
    ]

    model_metrics = evaluate_predictions(
        test_values,
        model_predictions
    )

    baseline_metrics = evaluate_predictions(
        test_values,
        baseline_predictions
    )

    evaluation = []

    for index, actual, predicted, baseline in zip(
        test_x,
        test_values,
        model_predictions,
        baseline_predictions
    ):

        evaluation.append({
            "month": monthly_data[index]["month"],
            "actual": round(actual, 2),
            "predicted": round(predicted, 2),
            "baseline": round(baseline, 2)
        })

    # Refit using all available historical observations.
    all_x = list(range(count))

    final_intercept, final_slope = linear_regression_fit(
        all_x,
        values
    )

    future_forecasts = []

    for step in range(forecast_horizon):

        future_index = count + step
        month_number = month_key(
            datetime.strptime(
                monthly_data[-1]["month"] + "-01",
                "%Y-%m-%d"
            )
        ) + step + 1

        future_forecasts.append({
            "month": month_label(month_number),
            "predicted_revenue": round(
                predict(
                    final_intercept,
                    final_slope,
                    future_index
                ),
                2
            )
        })

    model_is_better = model_metrics["mae"] < baseline_metrics["mae"]

    return {
        "history": monthly_data,
        "evaluation": evaluation,
        "future_forecasts": future_forecasts,
        "model_metrics": model_metrics,
        "baseline_metrics": baseline_metrics,
        "model_is_better": model_is_better,
        "model": "Linear Trend Regression",
        "training_months": len(train_values),
        "testing_months": len(test_values),
        "trend_per_month": round(final_slope, 2)
    }
