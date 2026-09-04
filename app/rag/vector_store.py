from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import (
    OpenAIEmbeddings,
)

from app.core.config import settings


VECTOR_DB_PATH = (
    "data/chroma"
)


def get_embeddings():

    return OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model="text-embedding-3-small",
    )


def create_vector_store(
    documents,
):

    Path(
        VECTOR_DB_PATH
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store = (
        Chroma.from_documents(
            documents=documents,
            embedding=get_embeddings(),
            persist_directory=(
                VECTOR_DB_PATH
            ),
            collection_name=(
                "enterprise_policy"
            ),
        )
    )

    return vector_store


def load_vector_store():

    return Chroma(
        persist_directory=(
            VECTOR_DB_PATH
        ),
        embedding_function=(
            get_embeddings()
        ),
        collection_name=(
            "enterprise_policy"
        ),
    )