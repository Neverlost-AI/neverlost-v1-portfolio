from pathlib import Path

from config import RAW_DIR, ensure_directories


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def list_documents(raw_dir: Path = RAW_DIR) -> list[Path]:
    ensure_directories()
    return sorted(
        path
        for path in raw_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def main() -> None:
    documents = list_documents()
    if not documents:
        print(f"No supported documents found in {RAW_DIR}")
        return
    print("Documents ready for extraction:")
    for document in documents:
        print(f"- {document.name}")


if __name__ == "__main__":
    main()

