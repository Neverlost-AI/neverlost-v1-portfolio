from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = PROJECT_ROOT / "config"
CASE_PROFILE_PATH = PROFILE_DIR / "case_profile.yaml"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw_documents"
EXTRACTED_DIR = DATA_DIR / "extracted_text"
OCR_DIR = DATA_DIR / "ocr_work"
CHUNKS_DIR = DATA_DIR / "chunks"
PROCESSED_DIR = DATA_DIR / "processed_json"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"
DEBUG_DIR = OUTPUTS_DIR / "debug"


def ensure_directories() -> None:
    for path in [
        PROFILE_DIR,
        RAW_DIR,
        EXTRACTED_DIR,
        OCR_DIR,
        CHUNKS_DIR,
        PROCESSED_DIR,
        REPORTS_DIR,
        DEBUG_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
