
from sqlalchemy import func

from database.connection import SessionLocal
from database.models import Dataset, SalesRecord


def verify_database():
    db = SessionLocal()

    try:
        dataset_count = db.query(Dataset).count()
        record_count = db.query(SalesRecord).count()

        revenue, profit = db.query(
            func.sum(SalesRecord.sales),
            func.sum(SalesRecord.profit)
        ).one()

        order_count = db.query(
            func.count(func.distinct(SalesRecord.order_id))
        ).scalar()

        customer_count = db.query(
            func.count(func.distinct(SalesRecord.customer_id))
        ).scalar()

        print("\n========== SENX DATABASE REPORT ==========")
        print(f"Total datasets       : {dataset_count}")
        print(f"Total sales records  : {record_count}")
        print(f"Total revenue        : {revenue}")
        print(f"Total profit         : {profit}")
        print(f"Total orders         : {order_count}")
        print(f"Total customers      : {customer_count}")
        print("==========================================")

    except Exception as error:
        print("Database verification failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    verify_database()
