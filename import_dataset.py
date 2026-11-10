
from modules.database_service import import_cleaned_dataset


if __name__ == "__main__":
    print("Starting SenX dataset import...")

    result = import_cleaned_dataset()

    print("\nImport Result:")
    for key, value in result.items():
        print(f"{key}: {value}")
