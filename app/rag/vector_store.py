from pathlib import Path
from hashlib import sha256

from langchain_chroma import Chroma
from app.rag.embeddings import BailianEmbeddings

from app.core.config import settings
from app.services.risk_rules import RULE_VERSION


def collection_name():
    return settings.vector_collection_name + "_rules_" + RULE_VERSION.replace(".", "_")


VECTOR_DB_PATH = (
    "data/chroma"
)


def get_embeddings():

    return BailianEmbeddings()


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
            ids=[sha256((str(doc.metadata) + doc.page_content).encode()).hexdigest() for doc in documents],
            embedding=get_embeddings(),
            persist_directory=(
                VECTOR_DB_PATH
            ),
            collection_name=(
                collection_name()
            ),
        )
    )

    return vector_store


def load_vector_store():

    store = Chroma(
        persist_directory=(
            VECTOR_DB_PATH
        ),
        embedding_function=(
            get_embeddings()
        ),
        collection_name=(
            collection_name()
        ),
    )
    if not store.get(limit=1)["ids"]:
        raise RuntimeError("Policy index is missing. Run python -m scripts.build_knowledge_base for rules " + RULE_VERSION)
    return store
