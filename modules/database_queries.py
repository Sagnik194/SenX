
from sqlalchemy import func
from database.connection import SessionLocal
from database.models import Dataset, SalesRecord

from database.connection import SessionLocal
from database.models import Dataset, SalesRecord


def get_latest_dataset():
    """Return the most recently imported dataset."""

    db = SessionLocal()

    try:
        return (
            db.query(Dataset)
            .filter(Dataset.status == "completed")
            .order_by(Dataset.uploaded_at.desc(), Dataset.id.desc())
            .first()
        )
    finally:
        db.close()


def get_dataset_list():
    """Return information about all completed datasets."""

    db = SessionLocal()

    try:
        datasets = (
            db.query(Dataset)
            .filter(Dataset.status == "completed")
            .order_by(Dataset.uploaded_at.desc())
            .all()
        )

        return [
            {
                "id": dataset.id,
                "filename": dataset.filename,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "uploaded_at": dataset.uploaded_at
            }
            for dataset in datasets
        ]
    finally:
        db.close()


def get_sales_records(dataset_id=None):
    """
    Retrieve sales records from MySQL.

    Returns dictionaries using the original Superstore CSV column names
    so existing SenX analytics modules can process them.
    """

    db = SessionLocal()

    try:
        query = db.query(SalesRecord)

        if dataset_id is None:
            latest = (
                db.query(Dataset)
                .filter(Dataset.status == "completed")
                .order_by(Dataset.uploaded_at.desc(), Dataset.id.desc())
                .first()
            )

            if latest is None:
                return []

            dataset_id = latest.id

        query = query.filter(SalesRecord.dataset_id == dataset_id)

        records = query.order_by(SalesRecord.id).all()

        result = []

        for record in records:
            result.append({
                "Row ID": record.row_id,
                "Order ID": record.order_id,
                "Order Date": (
                    record.order_date.isoformat()
                    if record.order_date else ""
                ),
                "Ship Date": (
                    record.ship_date.isoformat()
                    if record.ship_date else ""
                ),
                "Ship Mode": record.ship_mode,
                "Customer ID": record.customer_id,
                "Customer Name": record.customer_name,
                "Segment": record.segment,
                "Country": record.country,
                "City": record.city,
                "State": record.state,
                "Postal Code": record.postal_code,
                "Region": record.region,
                "Product ID": record.product_id,
                "Category": record.category,
                "Sub-Category": record.sub_category,
                "Product Name": record.product_name,
                "Sales": (
                    str(record.sales)
                    if record.sales is not None else ""
                ),
                "Quantity": (
                    str(record.quantity)
                    if record.quantity is not None else ""
                ),
                "Discount": (
                    str(record.discount)
                    if record.discount is not None else ""
                ),
                "Profit": (
                    str(record.profit)
                    if record.profit is not None else ""
                )
            })

        return result

    finally:
        db.close()


def get_database_summary(dataset_id=None):
    """Calculate basic KPIs directly from MySQL."""

    db = SessionLocal()

    try:
        if dataset_id is None:
            latest = (
                db.query(Dataset)
                .filter(Dataset.status == "completed")
                .order_by(Dataset.uploaded_at.desc(), Dataset.id.desc())
                .first()
            )

            if latest is None:
                return None

            dataset_id = latest.id

        summary = (
            db.query(
                func.count(SalesRecord.id),
                func.sum(SalesRecord.sales),
                func.sum(SalesRecord.profit),
                func.count(func.distinct(SalesRecord.order_id)),
                func.count(func.distinct(SalesRecord.customer_id))
            )
            .filter(SalesRecord.dataset_id == dataset_id)
            .one()
        )

        return {
            "total_records": summary[0] or 0,
            "total_revenue": float(summary[1] or 0),
            "total_profit": float(summary[2] or 0),
            "total_orders": summary[3] or 0,
            "total_customers": summary[4] or 0
        }

    finally:
        db.close()

def delete_dataset(dataset_id):
    """
    Delete a dataset and its associated sales records.
    """

    db = SessionLocal()

    try:
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset is None:
            return {
                "success": False,
                "message": "Dataset not found."
            }

        filename = dataset.filename

        # Delete the dataset.
        # Associated records are deleted through
        # the configured ORM cascade relationship.
        db.delete(dataset)
        db.commit()

        return {
            "success": True,
            "message": f"Dataset '{filename}' deleted successfully."
        }

    except Exception as error:
        db.rollback()

        return {
            "success": False,
            "message": str(error)
        }

    finally:
        db.close()

