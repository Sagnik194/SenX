import pytest
from io import BytesIO

from openpyxl import load_workbook
from pypdf import PdfReader

from modules.report_generator import (
    generate_pdf_report,
    generate_excel_report
)


@pytest.fixture
def sample_report_data():

    headers = [
        "Order ID",
        "Customer ID",
        "Category",
        "Sales",
        "Profit"
    ]

    rows = [
        {
            "Order ID": "ORD-001",
            "Customer ID": "CUST-001",
            "Category": "Technology",
            "Sales": 500.00,
            "Profit": 100.00
        },
        {
            "Order ID": "ORD-002",
            "Customer ID": "CUST-002",
            "Category": "Furniture",
            "Sales": 800.00,
            "Profit": 150.00
        }
    ]

    summary = {
        "total_revenue": 1300.00,
        "total_profit": 250.00,
        "total_orders": 2,
        "total_customers": 2,
        "average_order_value": 650.00,
        "profit_margin": 19.23,
        "total_quantity": 3,
        "total_records": 2
    }

    return headers, rows, summary


def test_excel_report_generation(sample_report_data):

    headers, rows, summary = sample_report_data

    result = generate_excel_report(
        headers,
        rows,
        summary
    )

    assert result is not None
    assert len(result) > 0

    workbook = load_workbook(
        BytesIO(result),
        data_only=True
    )

    assert "Executive Summary" in workbook.sheetnames
    assert "Sales Data" in workbook.sheetnames

    summary_sheet = workbook["Executive Summary"]
    sales_sheet = workbook["Sales Data"]

    assert sales_sheet.max_row == 3
    assert sales_sheet.max_column == 5

    workbook.close()


def test_pdf_report_generation(sample_report_data):

    _, _, summary = sample_report_data

    result = generate_pdf_report(summary)

    assert result is not None
    assert len(result) > 0

    pdf = PdfReader(BytesIO(result))

    assert len(pdf.pages) >= 1

    extracted_text = " ".join(
        page.extract_text() or ""
        for page in pdf.pages
    )

    assert "SenX" in extracted_text
    assert "Executive Summary" in extracted_text
    assert "Total Revenue" in extracted_text


def test_excel_report_contains_all_records(sample_report_data):

    headers, rows, summary = sample_report_data

    result = generate_excel_report(
        headers,
        rows,
        summary
    )

    workbook = load_workbook(BytesIO(result))

    sales_sheet = workbook["Sales Data"]

    exported_records = sales_sheet.max_row - 1

    assert exported_records == len(rows)

    workbook.close()
