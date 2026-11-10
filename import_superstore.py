
from pathlib import Path

from modules.database_service import import_dataset_to_database


DATA_FILE = Path("data/processed/superstore_cleaned.csv")


def main():
    if not DATA_FILE.exists():
        print("ERROR: Cleaned dataset not found.")
        print(f"Expected location: {DATA_FILE}")
        return

    print("Starting Superstore dataset import...")

    result = import_dataset_to_database(
        file_path=DATA_FILE,
        filename="superstore_cleaned.csv"
    )

    print("\nIMPORT RESULT")
    print("---------------------------")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
