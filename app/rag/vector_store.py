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
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        model=(
            settings.dashscope_embedding_model
        ),
        dimensions=(
            settings.dashscope_embedding_dimensions
        ),
        chunk_size=10,
        check_embedding_ctx_length=False,
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
                settings.vector_collection_name
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
            settings.vector_collection_name
        ),
    )
