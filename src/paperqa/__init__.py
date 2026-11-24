# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

# Load runtime credentials and settings overrides before importing PaperQA modules
# that read environment variables at import time.
load_dotenv(find_dotenv(usecwd=True))

from lmi import (
    EmbeddingModel,
    HybridEmbeddingModel,
    LiteLLMEmbeddingModel,
    LiteLLMModel,
    LLMModel,
    LLMResult,
    SentenceTransformerEmbeddingModel,
    SparseEmbeddingModel,
    embedding_model_factory,
)

from paperqa.agents import ask
from paperqa.agents.main import agent_query
from paperqa.docs import Docs, PQASession
from paperqa.llms import (
    NumpyVectorStore,
    QdrantVectorStore,
    VectorStore,
)
from paperqa.settings import Settings, get_settings
from paperqa.types import Context, Doc, DocDetails, Text
from paperqa.version import __version__

__all__ = [
    "Context",
    "Doc",
    "DocDetails",
    "Docs",
    "EmbeddingModel",
    "HybridEmbeddingModel",
    "LLMModel",
    "LLMResult",
    "LiteLLMEmbeddingModel",
    "LiteLLMModel",
    "NumpyVectorStore",
    "PQASession",
    "QdrantVectorStore",
    "SentenceTransformerEmbeddingModel",
    "Settings",
    "SparseEmbeddingModel",
    "Text",
    "VectorStore",
    "__version__",
    "agent_query",
    "ask",
    "embedding_model_factory",
    "get_settings",
]
