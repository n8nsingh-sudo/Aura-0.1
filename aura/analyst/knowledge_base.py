import fitz  # PyMuPDF
from docx import Document
from pathlib import Path

def knowledge_base(query: str) -> str:
    """
    Retrieves relevant reference documents from knowledge base
    based on keyword matching with user query.

    Returns only matched document content (not all files).
    """

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    docs_path = PROJECT_ROOT / "docs" / "knowledge_base"

    if not docs_path.exists():
        return "Knowledge base is empty."

    query_lower = query.lower()
    matched_content = []

    for file in docs_path.glob("*"):
        try:
            file_name_lower = file.name.lower()

            # Simple relevance check
            if any(keyword in file_name_lower for keyword in query_lower.split()):

                if file.suffix.lower() == ".pdf":
                    with fitz.open(file) as doc:
                        text = ""
                        for page in doc[:10]:  # limit pages to avoid overload
                            text += page.get_text()

                elif file.suffix.lower() == ".docx":
                    doc = Document(file)
                    text = "\n".join([para.text for para in doc.paragraphs[:100]])

                else:
                    continue

                matched_content.append(
                    f"\n--- REFERENCE FILE: {file.name} ---\n{text[:8000]}"
                )

        except Exception:
            continue

    if not matched_content:
        return "No relevant reference document found."

    return "\n\n".join(matched_content)
