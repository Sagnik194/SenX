
import csv
import io
from pathlib import Path
from io import BytesIO
from openpyxl import load_workbook
from pathlib import Path
from datetime import date, datetime

def read_file_content(source):
    """
    Read a CSV file from a file path, bytes, or uploaded file.
    Try common encodings used by business datasets.
    """

    if hasattr(source, "getvalue"):
        raw_data = source.getvalue()

    elif isinstance(source, bytes):
        raw_data = source

    elif isinstance(source, (str, Path)):
        raw_data = Path(source).read_bytes()

    else:
        raise TypeError("Unsupported file source.")

    if isinstance(raw_data, str):
        return raw_data

    encodings = ["utf-8-sig", "cp1252", "latin-1"]

    for encoding in encodings:
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("Could not decode the CSV file.")



def load_csv(source):
    """
    Load CSV data and return headers and rows.
    Preserves duplicate and blank column values correctly.
    """

    content = read_file_content(source)

    if not content.strip():
        raise ValueError("The uploaded CSV file is empty.")

    
    # Detect the delimiter using the header row.
    first_line = next(
        (line for line in content.splitlines() if line.strip()),
        ""
    )

    delimiters = [",", ";", "\t", "|"]

    delimiter = max(
        delimiters,
        key=lambda item: first_line.count(item)
    )

    reader = csv.reader(
        io.StringIO(content),
        delimiter=delimiter
    )


    raw_headers = next(reader, None)

    if not raw_headers:
        raise ValueError("CSV file does not contain column headers.")

    # Clean and make headers unique.
    headers = []

    for index, header in enumerate(raw_headers, start=1):
        name = (header or "").strip()

        if not name:
            name = f"column_{index}"

        original = name
        suffix = 2

        while name in headers:
            name = f"{original}_{suffix}"
            suffix += 1

        headers.append(name)

    rows = []

    for line_number, values in enumerate(reader, start=2):

        # Ignore completely empty rows.
        if not any(value.strip() for value in values):
            continue

        # Reject rows containing extra columns.
        if len(values) > len(headers):
            raise ValueError(
                f"Malformed CSV data near line {line_number}: "
                "a row contains more values than the header."
            )

        # Fill missing trailing columns with None.
        values = values + [None] * (len(headers) - len(values))

        cleaned_row = {}

        for header, value in zip(headers, values):
            if value is None:
                cleaned_row[header] = None
            else:
                value = value.strip()
                cleaned_row[header] = value if value else None

        rows.append(cleaned_row)

    return headers, rows



def get_numeric_value(value):
    """Convert a numeric string into a float."""

    if value is None:
        return None

    try:
        return float(value.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def profile_dataset(headers, rows):
    """
    Generate basic data-quality and statistical information.
    """

    total_rows = len(rows)
    total_columns = len(headers)

    missing_values = {}

    for column in headers:
        missing_values[column] = sum(
            1 for row in rows
            if row.get(column) is None
        )

    # Detect duplicate rows
    seen = set()
    duplicate_count = 0

    for row in rows:
        row_signature = tuple(row.get(column) for column in headers)

        if row_signature in seen:
            duplicate_count += 1
        else:
            seen.add(row_signature)

    # Calculate numeric column statistics
    numeric_summary = {}

    for column in headers:

        values = [
            get_numeric_value(row.get(column))
            for row in rows
        ]

        values = [value for value in values if value is not None]

        if values:
            numeric_summary[column] = {
                "count": len(values),
                "sum": round(sum(values), 2),
                "average": round(sum(values) / len(values), 2),
                "minimum": round(min(values), 2),
                "maximum": round(max(values), 2)
            }

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": duplicate_count,
        "missing_values": missing_values,
        "numeric_summary": numeric_summary
    }

def load_excel(source):
    """
    Load an Excel workbook and return:
    headers: list of column names
    rows: list of dictionaries
    """

    if hasattr(source, "getvalue"):
        source = BytesIO(source.getvalue())

    elif isinstance(source, bytes):
        source = BytesIO(source)

    workbook = load_workbook(
        source,
        read_only=True,
        data_only=True
    )

    try:
        worksheet = workbook.active
        iterator = worksheet.iter_rows(values_only=True)

        first_row = next(iterator, None)

        if not first_row:
            return [], []

        headers = []
        used_headers = set()

        for index, value in enumerate(first_row, start=1):
            header = str(value).strip() if value is not None else ""

            if not header:
                header = f"Column_{index}"

            original_header = header
            counter = 1

            while header in used_headers:
                counter += 1
                header = f"{original_header}_{counter}"

            used_headers.add(header)
            headers.append(header)

        rows = []

        for values in iterator:
            if not any(value is not None for value in values):
                continue

            row = {}

            for index, header in enumerate(headers):
                value = values[index] if index < len(values) else None

                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                elif value is not None:
                    value = str(value).strip()

                row[header] = value

            rows.append(row)

        return headers, rows

    finally:
        workbook.close()

def load_uploaded_dataset(uploaded_file):
    """
    Automatically load CSV or Excel files.
    Returns headers and rows.
    """

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return load_csv(uploaded_file)

    elif filename.endswith((".xlsx", ".xlsm")):
        return load_excel(uploaded_file)

    else:
        raise ValueError(
            "Unsupported file format. Please upload CSV or Excel."
        )

