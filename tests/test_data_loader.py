
import io
import pytest

from openpyxl import Workbook

from modules.data_loader import (
    load_csv,
    load_excel,
    load_uploaded_dataset,
    profile_dataset,
    read_file_content
)


class MockUploadedFile:
    """Simulate a Streamlit uploaded file."""

    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


def create_excel_file():
    """Create an Excel workbook in memory."""

    workbook = Workbook()
    worksheet = workbook.active

    worksheet.append(["Order ID", "Sales", "City"])
    worksheet.append(["ORD001", 1500, "Kolkata"])
    worksheet.append(["ORD002", 2500, "Delhi"])
    worksheet.append(["ORD003", 3000, "Mumbai"])

    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()

    return buffer.getvalue()


def test_csv_file_loading():
    content = (
        b"Order ID,Sales,City\n"
        b"ORD001,1500,Kolkata\n"
        b"ORD002,2500,Delhi\n"
    )

    headers, rows = load_csv(content)

    assert headers == ["Order ID", "Sales", "City"]
    assert len(rows) == 2
    assert rows[0]["Order ID"] == "ORD001"
    assert rows[0]["Sales"] == "1500"


def test_csv_duplicate_headers_are_renamed():
    content = (
        b"Name,Name,Age\n"
        b"Alice,Smith,25\n"
    )

    headers, rows = load_csv(content)

    assert headers == ["Name", "Name_2", "Age"]
    assert rows[0]["Name"] == "Alice"
    assert rows[0]["Name_2"] == "Smith"


def test_csv_blank_headers_are_renamed():
    content = (
        b"Name,,Age\n"
        b"Alice,Smith,25\n"
    )

    headers, rows = load_csv(content)

    assert headers == ["Name", "column_2", "Age"]
    assert rows[0]["column_2"] == "Smith"


def test_csv_empty_rows_are_ignored():
    content = (
        b"Name,City\n"
        b"Alice,Kolkata\n"
        b",\n"
        b"Bob,Delhi\n"
    )

    headers, rows = load_csv(content)

    assert len(rows) == 2


def test_csv_missing_values_are_handled():
    content = (
        b"Name,City,Age\n"
        b"Alice,,25\n"
        b"Bob,Delhi,\n"
    )

    headers, rows = load_csv(content)

    assert rows[0]["City"] is None
    assert rows[1]["Age"] is None


def test_empty_csv_is_rejected():
    with pytest.raises(ValueError):
        load_csv(b"")


def test_malformed_csv_is_rejected():
    content = (
        b"Name,City\n"
        b"Alice,Kolkata,Extra\n"
    )

    with pytest.raises(ValueError):
        load_csv(content)


def test_excel_file_loading():
    headers, rows = load_excel(create_excel_file())

    assert headers == ["Order ID", "Sales", "City"]
    assert len(rows) == 3
    assert rows[0]["Order ID"] == "ORD001"
    assert rows[0]["Sales"] == "1500"


def test_uploaded_csv_dispatch():
    uploaded_file = MockUploadedFile(
        "sales.csv",
        b"Name,Sales\nAlice,1000\n"
    )

    headers, rows = load_uploaded_dataset(uploaded_file)

    assert headers == ["Name", "Sales"]
    assert rows[0]["Name"] == "Alice"


def test_uploaded_excel_dispatch():
    uploaded_file = MockUploadedFile(
        "sales.xlsx",
        create_excel_file()
    )

    headers, rows = load_uploaded_dataset(uploaded_file)

    assert headers == ["Order ID", "Sales", "City"]
    assert len(rows) == 3


def test_unsupported_file_format_is_rejected():
    uploaded_file = MockUploadedFile(
        "sales.pdf",
        b"sample content"
    )

    with pytest.raises(ValueError):
        load_uploaded_dataset(uploaded_file)


def test_profile_dataset():
    headers = ["Name", "Sales"]

    rows = [
        {"Name": "Alice", "Sales": "1000"},
        {"Name": "Bob", "Sales": "2000"},
        {"Name": "Alice", "Sales": "1000"}
    ]

    result = profile_dataset(headers, rows)

    assert result["total_rows"] == 3
    assert result["total_columns"] == 2
    assert result["duplicate_rows"] == 1
    assert result["numeric_summary"]["Sales"]["sum"] == 4000.0


def test_read_file_content_from_bytes():
    content = b"Name,City\nAlice,Kolkata"

    result = read_file_content(content)

    assert "Alice" in result
    assert "Kolkata" in result
