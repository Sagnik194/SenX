
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import modules.database_service as database_service

from database.connection import Base
from database.models import Dataset, SalesRecord


@pytest.fixture
def test_database(monkeypatch):

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )

    monkeypatch.setattr(
        database_service,
        "SessionLocal",
        TestSessionLocal
    )

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def get_sample_data():

    headers = [
        "Row ID",
        "Order ID",
        "Order Date",
        "Customer ID",
        "Customer Name",
        "Product ID",
        "Category",
        "Sales",
        "Quantity",
        "Discount",
        "Profit"
    ]

    rows = [
        {
            "Row ID": "1",
            "Order ID": "ORD-001",
            "Order Date": "2026-01-10",
            "Customer ID": "CUST-001",
            "Customer Name": "John",
            "Product ID": "PROD-001",
            "Category": "Technology",
            "Sales": "500.00",
            "Quantity": "2",
            "Discount": "0.10",
            "Profit": "100.00"
        },
        {
            "Row ID": "2",
            "Order ID": "ORD-002",
            "Order Date": "2026-01-12",
            "Customer ID": "CUST-002",
            "Customer Name": "Alice",
            "Product ID": "PROD-002",
            "Category": "Furniture",
            "Sales": "800.00",
            "Quantity": "1",
            "Discount": "0.05",
            "Profit": "150.00"
        }
    ]

    return headers, rows


def test_successful_dataset_import(test_database):

    headers, rows = get_sample_data()

    result = database_service.import_cleaned_dataset(
        headers=headers,
        rows=rows,
        filename="test_sales.csv"
    )

    assert result["success"] is True
    assert result["records_imported"] == 2
    assert result["columns"] == len(headers)

    db = test_database()

    try:

        dataset = db.query(Dataset).first()

        assert dataset is not None
        assert dataset.filename == "test_sales.csv"
        assert dataset.row_count == 2
        assert dataset.status == "completed"

        records = db.query(SalesRecord).all()

        assert len(records) == 2

    finally:
        db.close()


def test_duplicate_dataset_import(test_database):

    headers, rows = get_sample_data()

    first_result = database_service.import_cleaned_dataset(
        headers=headers,
        rows=rows,
        filename="duplicate_test.csv"
    )

    second_result = database_service.import_cleaned_dataset(
        headers=headers,
        rows=rows,
        filename="duplicate_test.csv"
    )

    assert first_result["success"] is True
    assert second_result["success"] is False
    assert second_result["duplicate"] is True


def test_missing_required_columns(test_database):

    headers = ["Customer Name", "Category"]

    rows = [
        {
            "Customer Name": "John",
            "Category": "Technology"
        }
    ]

    result = database_service.import_cleaned_dataset(
        headers=headers,
        rows=rows,
        filename="invalid.csv"
    )

    assert result["success"] is False
    assert "Missing required columns" in result["message"]


def test_empty_dataset_import(test_database):

    headers, _ = get_sample_data()

    result = database_service.import_cleaned_dataset(
        headers=headers,
        rows=[],
        filename="empty.csv"
    )

    assert result["success"] is False
    assert "no records" in result["message"].lower()
