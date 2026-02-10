import io
from typing import Tuple
from pdfminer.high_level import extract_text
from docx import Document

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def read_resume_file(file_obj, filename: str) -> Tuple[str, str]:
    ext = filename.lower().split(".")[-1]
    ext = "." + ext
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == ".pdf":
        # pdfminer expects a file-like object or path; use the underlying file handle
        file_obj.seek(0)
        text = extract_text(file_obj.file)
    elif ext == ".docx":
        file_obj.seek(0)
        document = Document(file_obj)
        text = "\n".join([p.text for p in document.paragraphs])
    else:
        file_obj.seek(0)
        raw = file_obj.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        text = str(raw)

    return text, ext
