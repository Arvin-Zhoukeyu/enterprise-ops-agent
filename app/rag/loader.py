from pathlib import Path


KNOWLEDGE_DIR = Path(
    "data/knowledge"
)


def load_documents() -> list[dict]:

    documents = []

    for path in KNOWLEDGE_DIR.glob(
        "*.txt"
    ):

        content = path.read_text(
            encoding="utf-8"
        )

        documents.append(
            {
                "document_id":
                    path.stem,

                "source":
                    path.name,

                "content":
                    content,
            }
        )

    return documents