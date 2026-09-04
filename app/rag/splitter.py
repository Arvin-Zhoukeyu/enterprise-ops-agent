from langchain_core.documents import (
    Document,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


def split_documents(
    raw_documents: list[dict],
) -> list[Document]:

    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
        )
    )

    documents = []

    for raw in raw_documents:

        chunks = splitter.split_text(
            raw["content"]
        )

        for index, chunk in enumerate(
            chunks
        ):

            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "document_id":
                            raw[
                                "document_id"
                            ],

                        "source":
                            raw["source"],

                        "chunk_index":
                            index,
                    },
                )
            )

    return documents