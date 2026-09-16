from config import CHUNKS_DIR, EXTRACTED_DIR, PROCESSED_DIR, ensure_directories
from utils import normalize_whitespace, read_json, write_json


def chunk_text(text: str, max_words: int = 180, overlap_words: int = 35) -> list[str]:
    words = normalize_whitespace(text).split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap_words)
    return chunks


def build_chunks() -> list[dict]:
    ensure_directories()
    pages = read_json(EXTRACTED_DIR / "extracted_pages.json", [])
    chunks = []
    for page in pages:
        for index, chunk in enumerate(chunk_text(page.get("text", "")), start=1):
            chunk_id = f"{page['document']}::p{page.get('page') or 'na'}::c{index}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document": page["document"],
                    "page": page.get("page"),
                    "chunk_index": index,
                    "text": chunk,
                }
            )
    write_json(CHUNKS_DIR / "chunks.json", chunks)
    write_json(PROCESSED_DIR / "chunks.json", chunks)
    return chunks


def main() -> None:
    chunks = build_chunks()
    print(f"Built {len(chunks)} source-linked chunks.")
    print(f"Wrote {CHUNKS_DIR / 'chunks.json'}")


if __name__ == "__main__":
    main()
