import shutil
from pathlib import Path

try:
    from pymongo import MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

from config import CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME


DATA_PROCESSED_DIR = Path("data/processed")
FEATURES_DIR = Path("data/features")
REPORTS_DIR = Path("reports")
MODELS_DIR = Path("models")


def ask_yes_no(question: str) -> bool:
    ans = input(f"{question} (y/n): ").strip().lower()
    return ans == "y"


def remove_dir(path: Path):
    if path.is_dir():
        shutil.rmtree(path)
        print(f"Da xoa thu muc: {path}")
    else:
        print(f"Khong ton tai, bo qua: {path}")


def cleanup_files():
    print("\n=== CLEANUP FILE OUTPUTS ===")

    if ask_yes_no(f"Xoa thu muc processed images ({DATA_PROCESSED_DIR})?"):
        remove_dir(DATA_PROCESSED_DIR)

    if ask_yes_no(f"Xoa thu muc features ({FEATURES_DIR})?"):
        remove_dir(FEATURES_DIR)

    if ask_yes_no(f"Xoa cac bao cao trong {REPORTS_DIR} (figures, models)?"):
        if REPORTS_DIR.is_dir():
            for sub in REPORTS_DIR.iterdir():
                if sub.is_dir():
                    remove_dir(sub)
        else:
            print(f"Khong ton tai, bo qua: {REPORTS_DIR}")

    if ask_yes_no(f"Xoa cac model da train trong {MODELS_DIR}?"):
        remove_dir(MODELS_DIR)


def cleanup_mongodb():
    if not HAS_MONGO:
        print("pymongo chua cai, bo qua cleanup MongoDB.")
        return

    print("\n=== CLEANUP MONGODB ===")
    if not ask_yes_no(
        f"Xac nhan XOA TOAN BO du lieu trong MongoDB {DATABASE_NAME}.{COLLECTION_NAME}?"
    ):
        print("Bo qua xoa MongoDB.")
        return

    client = MongoClient(CONNECTION_STRING)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    deleted = collection.delete_many({})
    client.close()
    print(f"Da xoa {deleted.deleted_count} documents trong {DATABASE_NAME}.{COLLECTION_NAME}.")


def main():
    print("CLEANUP KET QUA PIPELINE")
    print("=" * 60)

    cleanup_files()
    cleanup_mongodb()

    print("\nHoan tat cleanup.")


if __name__ == "__main__":
    main()
