
from database.connection import SessionLocal
from database.models import Dataset
from modules.database_queries import get_sales_records
from modules.database_service import calculate_content_hash


def main():
    db = SessionLocal()

    try:
        datasets = (
            db.query(Dataset)
            .order_by(Dataset.id)
            .all()
        )

        fingerprints = {}

        for dataset in datasets:
            rows = get_sales_records(dataset.id)

            if not rows:
                print(
                    f"Dataset {dataset.id}: No records found."
                )
                continue

            headers = list(rows[0].keys())

            content_hash = calculate_content_hash(
                headers,
                rows
            )

            fingerprints[dataset.id] = content_hash

            print(f"\nDataset ID: {dataset.id}")
            print(f"Filename: {dataset.filename}")
            print(f"Rows: {len(rows)}")
            print(f"SHA-256: {content_hash}")

        print("\n========== DUPLICATE CHECK ==========")

        hash_groups = {}

        for dataset_id, content_hash in fingerprints.items():
            hash_groups.setdefault(
                content_hash, []
            ).append(dataset_id)

        for content_hash, dataset_ids in hash_groups.items():
            if len(dataset_ids) > 1:
                print(
                    f"Duplicate content found: Dataset IDs {dataset_ids}"
                )
            else:
                print(
                    f"Unique content: Dataset ID {dataset_ids[0]}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()
