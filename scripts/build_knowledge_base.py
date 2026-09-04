from app.rag.loader import (
    load_documents,
)
from app.rag.splitter import (
    split_documents,
)
from app.rag.vector_store import (
    create_vector_store,
)


def main():

    print(
        "Loading enterprise documents..."
    )

    raw_documents = (
        load_documents()
    )

    print(
        f"Documents: "
        f"{len(raw_documents)}"
    )

    chunks = split_documents(
        raw_documents
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    create_vector_store(
        chunks
    )

    print(
        "Knowledge base built successfully."
    )


if __name__ == "__main__":
    main()