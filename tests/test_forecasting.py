
import pytest

from modules.forecasting import (
    aggregate_monthly_revenue,
    evaluate_predictions,
    forecast_sales
)


def get_sample_sales():
    """Generate 12 months of sample sales data."""

    rows = []

    for month in range(1, 13):
        rows.append({
            "Order Date": f"2025-{month:02d}-15",
            "Sales": str(month * 1000)
        })

    return rows


def test_monthly_revenue_aggregation():
    rows = get_sample_sales()

    result = aggregate_monthly_revenue(rows)

    assert len(result) == 12
    assert result[0]["month"] == "2025-01"
    assert result[0]["revenue"] == 1000.0
    assert result[-1]["month"] == "2025-12"
    assert result[-1]["revenue"] == 12000.0


def test_forecast_generation():
    result = forecast_sales(
        get_sample_sales(),
        forecast_horizon=3
    )

    assert len(result["future_forecasts"]) == 3
    assert len(result["history"]) == 12
    assert len(result["evaluation"]) == result["testing_months"]


def test_forecast_horizon():
    for horizon in [1, 3, 6]:
        result = forecast_sales(
            get_sample_sales(),
            forecast_horizon=horizon
        )

        assert len(result["future_forecasts"]) == horizon


def test_forecast_predictions_are_valid():
    result = forecast_sales(
        get_sample_sales(),
        forecast_horizon=3
    )

    for forecast in result["future_forecasts"]:
        assert isinstance(forecast["predicted_revenue"], float)
        assert forecast["predicted_revenue"] >= 0


def test_evaluation_metrics_are_non_negative():
    metrics = evaluate_predictions(
        actual=[100, 200, 300],
        predicted=[110, 190, 310]
    )

    assert metrics["mae"] >= 0
    assert metrics["rmse"] >= 0
    assert metrics["mape"] >= 0


def test_training_and_testing_months():
    result = forecast_sales(get_sample_sales())

    assert result["training_months"] >= 3
    assert result["testing_months"] >= 3
    assert (
        result["training_months"] + result["testing_months"]
        == 12
    )


def test_forecast_requires_six_months():
    rows = get_sample_sales()[:5]

    with pytest.raises(ValueError):
        forecast_sales(rows)


def test_forecast_rejects_invalid_horizon():
    with pytest.raises(ValueError):
        forecast_sales(get_sample_sales(), forecast_horizon=0)
