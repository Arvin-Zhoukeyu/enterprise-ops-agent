from app.rag.vector_store import (
    load_vector_store,
)


def search_policy(
    query: str,
    top_k: int = 4,
) -> list[dict]:

    vector_store = (
        load_vector_store()
    )

    documents = (
        vector_store
        .similarity_search(
            query,
            k=top_k,
        )
    )

    results = []

    for document in documents:

        results.append(
            {
                "content":
                    document.page_content,

                "source":
                    document.metadata.get(
                        "source"
                    ),

                "document_id":
                    document.metadata.get(
                        "document_id"
                    ),

                "chunk_index":
                    document.metadata.get(
                        "chunk_index"
                    ),
            }
        )

    return results