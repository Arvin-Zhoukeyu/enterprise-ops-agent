from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.llm import create_bailian_client
from app.observability.usage import record_usage


class BailianEmbeddings(Embeddings):
    """Keep raw provider usage; LangChain's embedding wrapper discards it."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        if not texts:
            return vectors
        with create_bailian_client() as client:
            for start in range(0, len(texts), 10):
                response = client.embeddings.create(
                    input=texts[start:start + 10],
                    model=settings.dashscope_embedding_model,
                    dimensions=settings.dashscope_embedding_dimensions,
                    encoding_format="float",
                )
                record_usage(response.usage, embedding=True)
                vectors.extend(item.embedding for item in sorted(response.data, key=lambda x: x.index))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
