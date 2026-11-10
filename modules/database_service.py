
import csv
import hashlib
import json

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import Dataset, SalesRecord


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_FILE = (
    PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
)


def get_value(row, column):
    """Read a CSV value safely."""

    value = row.get(column)

    if value is None:
        return None

    value = str(value).strip()

    if not value or value.lower() in ("none", "null", "nan"):
        return None

    return value


def parse_integer(value):
    if value is None:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def parse_decimal(value):
    if value is None:
        return None

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_date(value):
    if value is None:
        return None

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S"
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


def calculate_content_hash(headers, rows):
    """
    Generate a SHA-256 fingerprint from dataset headers and row values.

    The filename is intentionally excluded.
    """

    digest = hashlib.sha256()

    normalized_headers = [
        str(header).strip()
        for header in headers
    ]

    header_content = json.dumps(
        normalized_headers,
        ensure_ascii=False,
        separators=(",", ":")
    )

    digest.update(header_content.encode("utf-8"))

    for row in rows:

        normalized_values = []

        for header in normalized_headers:

            value = row.get(header)

            if value is None:
                normalized_values.append(None)
            else:
                normalized_values.append(str(value).strip())

        row_content = json.dumps(
            normalized_values,
            ensure_ascii=False,
            separators=(",", ":")
        )

        digest.update(b"\n")
        digest.update(row_content.encode("utf-8"))

    return digest.hexdigest()


def create_sales_record(row, dataset_id):
    """Convert one dataset row into a SQLAlchemy SalesRecord."""

    return SalesRecord(
        dataset_id=dataset_id,

        row_id=parse_integer(get_value(row, "Row ID")),

        order_id=get_value(row, "Order ID"),
        order_date=parse_date(get_value(row, "Order Date")),
        ship_date=parse_date(get_value(row, "Ship Date")),
        ship_mode=get_value(row, "Ship Mode"),

        customer_id=get_value(row, "Customer ID"),
        customer_name=get_value(row, "Customer Name"),
        segment=get_value(row, "Segment"),

        country=get_value(row, "Country"),
        city=get_value(row, "City"),
        state=get_value(row, "State"),
        postal_code=get_value(row, "Postal Code"),
        region=get_value(row, "Region"),

        product_id=get_value(row, "Product ID"),
        category=get_value(row, "Category"),
        sub_category=get_value(row, "Sub-Category"),
        product_name=get_value(row, "Product Name"),

        sales=parse_decimal(get_value(row, "Sales")),
        quantity=parse_integer(get_value(row, "Quantity")),
        discount=parse_decimal(get_value(row, "Discount")),
        profit=parse_decimal(get_value(row, "Profit"))
    )


def import_cleaned_dataset(
    file_path=CLEANED_FILE,
    batch_size=1000,
    headers=None,
    rows=None,
    filename=None
):
    """
    Import a cleaned dataset into MySQL.

    Supports:
    1. An existing cleaned CSV file.
    2. In-memory cleaned CSV or Excel data.

    Uses SHA-256 content hashing to detect duplicate datasets.
    """

    db: Session = SessionLocal()

    try:

        # ------------------------------------------
        # OPTION 1: Use cleaned data already in memory
        # ------------------------------------------

        if headers is not None and rows is not None:

            headers = list(headers)

            required_columns = {
                "Order ID",
                "Order Date",
                "Customer ID",
                "Product ID",
                "Sales",
                "Profit"
            }

            available_columns = set(headers)
            missing_columns = required_columns - available_columns

            if missing_columns:
                return {
                    "success": False,
                    "message": (
                        "Missing required columns: "
                        + ", ".join(sorted(missing_columns))
                    )
                }

            data_rows = rows
            source_filename = (
                filename or "uploaded_cleaned_dataset.csv"
            )
            column_count = len(headers)

        # ------------------------------------------
        # OPTION 2: Read the existing cleaned CSV file
        # ------------------------------------------

        elif headers is None and rows is None:

            file_path = Path(file_path)

            if not file_path.exists():
                return {
                    "success": False,
                    "message": f"Dataset file not found: {file_path}"
                }

            with file_path.open(
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as csv_file:

                reader = csv.DictReader(csv_file)

                headers = list(reader.fieldnames or [])

                required_columns = {
                    "Order ID",
                    "Order Date",
                    "Customer ID",
                    "Product ID",
                    "Sales",
                    "Profit"
                }

                available_columns = set(headers)
                missing_columns = required_columns - available_columns

                if missing_columns:
                    return {
                        "success": False,
                        "message": (
                            "Missing required CSV columns: "
                            + ", ".join(sorted(missing_columns))
                        )
                    }

                data_rows = list(reader)

                source_filename = filename or file_path.name
                column_count = len(headers)

        else:

            return {
                "success": False,
                "message": (
                    "Both headers and rows must be provided together."
                )
            }

        # ------------------------------------------
        # VALIDATE DATASET
        # ------------------------------------------

        total_rows = len(data_rows)

        if total_rows == 0:
            return {
                "success": False,
                "message": "The cleaned dataset contains no records."
            }

        if batch_size <= 0:
            return {
                "success": False,
                "message": "Batch size must be greater than zero."
            }

        # ------------------------------------------
        # GENERATE SHA-256 CONTENT FINGERPRINT
        # ------------------------------------------

        content_hash = calculate_content_hash(
            headers,
            data_rows
        )

        # ------------------------------------------
        # CHECK FOR AN EXISTING DATASET
        # ------------------------------------------

        existing_dataset = (
            db.query(Dataset)
            .filter(
                Dataset.content_hash == content_hash,
                Dataset.status == "completed"
            )
            .first()
        )

        if existing_dataset:

            return {
                "success": False,
                "duplicate": True,
                "dataset_id": existing_dataset.id,
                "message": (
                    "This dataset has already been imported. "
                    f"Existing dataset ID: {existing_dataset.id}."
                )
            }

        # ------------------------------------------
        # CREATE DATASET ENTRY
        # ------------------------------------------

        dataset = Dataset(
            filename=source_filename,
            content_hash=content_hash,
            row_count=0,
            column_count=column_count,
            status="importing"
        )

        db.add(dataset)
        db.flush()

        # ------------------------------------------
        # IMPORT RECORDS IN BATCHES
        # ------------------------------------------

        imported_count = 0
        batch = []

        for row in data_rows:

            batch.append(
                create_sales_record(
                    row,
                    dataset.id
                )
            )

            if len(batch) >= batch_size:

                db.add_all(batch)
                db.flush()

                imported_count += len(batch)
                batch.clear()

        if batch:

            db.add_all(batch)
            db.flush()

            imported_count += len(batch)

        # ------------------------------------------
        # COMPLETE IMPORT
        # ------------------------------------------

        dataset.row_count = imported_count
        dataset.status = "completed"

        db.commit()

        return {
            "success": True,
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "records_imported": imported_count,
            "columns": dataset.column_count,
            "content_hash": content_hash,
            "message": "Dataset imported successfully."
        }

    except Exception as error:

        db.rollback()

        return {
            "success": False,
            "message": str(error)
        }

    finally:

        db.close()
