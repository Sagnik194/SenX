
from modules.data_cleaner import clean_dataset


def test_duplicate_rows_are_removed():
    headers = ["Order ID", "Sales", "Quantity"]

    rows = [
        {"Order ID": "ORD001", "Sales": "100", "Quantity": "2"},
        {"Order ID": "ORD001", "Sales": "100", "Quantity": "2"},
        {"Order ID": "ORD002", "Sales": "200", "Quantity": "3"},
    ]

    cleaned_rows, report = clean_dataset(headers, rows)

    assert len(cleaned_rows) == 2
    assert len(rows) == 3


def test_missing_values_are_normalized():
    headers = ["Order ID", "Sales"]

    rows = [
        {"Order ID": "ORD001", "Sales": ""},
        {"Order ID": "ORD002", "Sales": "100"},
    ]

    cleaned_rows, report = clean_dataset(headers, rows)

    assert cleaned_rows[0]["Sales"] is None
    assert cleaned_rows[1]["Sales"] == "100"



def test_numeric_values_are_validated():
    headers = ["Order ID", "Sales"]

    rows = [
        {"Order ID": "ORD001", "Sales": "100.50"},
        {"Order ID": "ORD002", "Sales": "invalid"},
    ]

    cleaned_rows, report = clean_dataset(headers, rows)

    assert float(cleaned_rows[0]["Sales"]) == 100.50
    assert cleaned_rows[1]["Sales"] is None



def test_cleaning_without_duplicate_removal():
    headers = ["Order ID", "Sales"]

    rows = [
        {"Order ID": "ORD001", "Sales": "100"},
        {"Order ID": "ORD001", "Sales": "100"},
    ]

    cleaned_rows, report = clean_dataset(
        headers,
        rows,
        remove_duplicates=False
    )

    assert len(cleaned_rows) == 2


def test_original_data_is_not_modified():
    headers = ["Order ID", "Sales"]

    rows = [
        {"Order ID": "ORD001", "Sales": "100"},
    ]

    original_rows = [row.copy() for row in rows]

    clean_dataset(headers, rows)

    assert rows == original_rows
