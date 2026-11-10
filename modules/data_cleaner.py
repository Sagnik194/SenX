
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


# Columns that should contain numeric values
NUMERIC_COLUMNS = {
    "sales",
    "profit",
    "quantity",
    "discount"
}

# Columns that should contain dates
DATE_COLUMNS = {
    "order date",
    "ship date"
}

DATE_FORMATS = [
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y"
]


def normalize_cell(value):
    """Trim spaces and standardize empty values."""

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def convert_numeric(value):
    """Validate and normalize numeric values."""

    if value is None:
        return None, False

    try:
        number = Decimal(value.replace(",", ""))

        if not number.is_finite():
            return None, True

        return format(number.normalize(), "f"), False

    except (InvalidOperation, ValueError):
        return None, True


def convert_date(value):
    """Convert supported date formats into YYYY-MM-DD."""

    if value is None:
        return None, False

    for date_format in DATE_FORMATS:

        try:
            parsed_date = datetime.strptime(value, date_format)
            return parsed_date.strftime("%Y-%m-%d"), False

        except ValueError:
            continue

    return None, True


def clean_dataset(headers, rows, remove_duplicates=True):
    """
    Clean a dataset without using Pandas.

    Returns:
        cleaned_rows
        cleaning_report
    """

    original_row_count = len(rows)
    cleaned_rows = []

    seen_rows = set()
    duplicates_removed = 0
    invalid_values = {}
    missing_before = {}
    missing_after = {}

    # Normalize column names for type detection
    normalized_headers = {
        header: header.strip().casefold()
        for header in headers
    }

    # Count missing values in original dataset
    for header in headers:
        missing_before[header] = sum(
            1 for row in rows
            if normalize_cell(row.get(header)) is None
        )

    for original_row in rows:

        cleaned_row = {}

        # Step 1: Normalize spaces and empty cells
        for header in headers:

            value = normalize_cell(original_row.get(header))
            column_type = normalized_headers[header]

            # Step 2: Validate numeric columns
            if column_type in NUMERIC_COLUMNS:

                value, invalid = convert_numeric(value)

                if invalid:
                    invalid_values[header] = (
                        invalid_values.get(header, 0) + 1
                    )

            # Step 3: Standardize date columns
            elif column_type in DATE_COLUMNS:

                value, invalid = convert_date(value)

                if invalid:
                    invalid_values[header] = (
                        invalid_values.get(header, 0) + 1
                    )

            cleaned_row[header] = value

        # Step 4: Detect exact duplicates after normalization
        row_signature = tuple(
            cleaned_row.get(header)
            for header in headers
        )

        if remove_duplicates and row_signature in seen_rows:
            duplicates_removed += 1
            continue

        seen_rows.add(row_signature)
        cleaned_rows.append(cleaned_row)

    # Count missing values after cleaning
    for header in headers:

        missing_after[header] = sum(
            1 for row in cleaned_rows
            if row.get(header) is None
        )

    report = {
        "original_rows": original_row_count,
        "cleaned_rows": len(cleaned_rows),
        "duplicates_removed": duplicates_removed,
        "rows_removed": original_row_count - len(cleaned_rows),
        "original_columns": len(headers),
        "total_missing_before": sum(missing_before.values()),
        "total_missing_after": sum(missing_after.values()),
        "missing_before": missing_before,
        "missing_after": missing_after,
        "invalid_values": invalid_values
    }

    return cleaned_rows, report


def save_cleaned_csv(headers, rows, output_path):
    """Save cleaned records into a separate CSV file."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=headers
        )

        writer.writeheader()
        writer.writerows(rows)

    return output_path
