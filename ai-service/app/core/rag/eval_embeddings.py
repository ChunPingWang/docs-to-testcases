"""LangChain Embeddings adapter for MiniMax embedding API."""

from typing import List

from langchain_core.embeddings import Embeddings

from app.core.embedding.ollama_embedder import embed_texts, embed_single


class MiniMaxEmbeddings(Embeddings):
    """LangChain-compatible wrapper around MiniMax embedding API."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents (synchronous interface).

        Note: Uses asyncio to run the async MiniMax API call.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're in an async context; create a new thread to avoid deadlock
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, embed_texts(texts, embed_type="db")).result()
        else:
            return asyncio.run(embed_texts(texts, embed_type="db"))

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query (synchronous interface)."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, embed_single(text)).result()
        else:
            return asyncio.run(embed_single(text))
