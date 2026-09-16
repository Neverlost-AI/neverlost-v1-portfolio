import subprocess
from pathlib import Path

from config import EXTRACTED_DIR, OCR_DIR, RAW_DIR, ensure_directories
from ingest_documents import list_documents
from utils import write_json


OCR_TEXT_THRESHOLD = 25
WINDOWS_OCR_SCRIPT = Path(__file__).with_name("windows_ocr.ps1")


def safe_stem(path: Path) -> str:
    return "".join(char if char.isalnum() else "_" for char in path.stem).strip("_")


def run_windows_ocr(image_path: Path) -> tuple[str, str | None]:
    if not WINDOWS_OCR_SCRIPT.exists():
        return "", "windows_ocr.ps1 helper script was not found"
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(WINDOWS_OCR_SCRIPT),
                str(image_path),
            ],
            cwd=str(WINDOWS_OCR_SCRIPT.parent.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except Exception as exc:
        return "", f"Windows OCR call failed: {exc}"

    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout or "Unknown OCR error").strip()
        return "", error
    return completed.stdout.strip(), None


def ocr_pdf_page_image(path: Path, page, page_number: int) -> tuple[str, str | None, Path | None]:
    try:
        images = list(page.images)
    except Exception as exc:
        return "", f"Could not inspect page images for OCR: {exc}", None

    if not images:
        return "", "No embedded page image found for OCR", None

    image = images[0]
    image_path = OCR_DIR / f"{safe_stem(path)}_p{page_number}.png"
    try:
        if getattr(image, "image", None) is not None:
            image.image.save(image_path)
        else:
            image_path = OCR_DIR / f"{safe_stem(path)}_p{page_number}_{image.name}"
            image_path.write_bytes(image.data)
    except Exception as exc:
        return "", f"Could not write OCR page image: {exc}", None

    text, error = run_windows_ocr(image_path)
    return text, error, image_path


def extract_pdf_pages(path: Path) -> list[dict]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install dependencies first: pip install -r requirements.txt") from exc

    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = raw_text
        ocr_text = ""
        ocr_error = None
        ocr_image_path = None
        text_extraction_method = "pypdf"

        if len(raw_text.strip()) < OCR_TEXT_THRESHOLD:
            ocr_text, ocr_error, ocr_image_path = ocr_pdf_page_image(path, page, index)
            if ocr_text.strip():
                text = ocr_text
                text_extraction_method = "windows_media_ocr"
            else:
                text_extraction_method = "pypdf_blank_ocr_failed" if ocr_error else "pypdf_blank_no_ocr_text"

        pages.append(
            {
                "document": path.name,
                "page": index,
                "text": text,
                "text_extraction_method": text_extraction_method,
                "raw_pdf_text_character_count": len(raw_text),
                "ocr_text_character_count": len(ocr_text),
                "ocr_required": len(raw_text.strip()) < OCR_TEXT_THRESHOLD,
                "ocr_applied": bool(ocr_text.strip()),
                "ocr_error": ocr_error,
                "ocr_image_path": str(ocr_image_path) if ocr_image_path else None,
            }
        )
    return pages


def extract_text_file(path: Path) -> list[dict]:
    return [
        {
            "document": path.name,
            "page": None,
            "text": path.read_text(encoding="utf-8", errors="ignore"),
            "text_extraction_method": "plain_text",
            "raw_pdf_text_character_count": None,
            "ocr_text_character_count": 0,
            "ocr_required": False,
            "ocr_applied": False,
            "ocr_error": None,
            "ocr_image_path": None,
        }
    ]


def extract_all(raw_dir: Path = RAW_DIR) -> list[dict]:
    ensure_directories()
    extracted = []
    for document in list_documents(raw_dir):
        if document.suffix.lower() == ".pdf":
            extracted.extend(extract_pdf_pages(document))
        else:
            extracted.extend(extract_text_file(document))

    write_json(EXTRACTED_DIR / "extracted_pages.json", extracted)
    return extracted


def main() -> None:
    extracted = extract_all()
    print(f"Extracted {len(extracted)} page/text records.")
    print(f"Wrote {EXTRACTED_DIR / 'extracted_pages.json'}")


if __name__ == "__main__":
    main()
