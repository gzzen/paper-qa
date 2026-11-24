from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from mcp.server import MCPServer

    from paperqa.settings import Settings

logger = logging.getLogger(__name__)

# Tantivy, embedding, and answer-index writes aren't safe to overlap within one
# PaperQA process, so every MCP request shares this lock.
_PAPERQA_QUERY_LOCK = asyncio.Lock()


class PaperQAAnswer(BaseModel):
    """Minimal model-facing result from a PaperQA query."""

    answer: str
    formatted_answer: str
    status: str
    cost: float
    source_count: int = Field(ge=0)


def _configure_logging() -> None:
    """Send all diagnostics to stderr, keeping stdout for the MCP wire protocol."""
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        force=True,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _get_settings() -> Settings:
    from paperqa.settings import get_settings

    settings_name = os.environ.get("PAPERQA_SETTINGS") or "deepseek"
    settings = get_settings(settings_name)
    if paper_directory := os.environ.get("PAPERQA_PAPER_DIRECTORY"):
        settings.agent.index.paper_directory = paper_directory
    return settings


def create_server() -> MCPServer:
    """Create the paperqa MCP server without importing MCP until requested."""
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError

    from paperqa.version import __version__

    server = MCPServer(
        "paperqa",
        version=__version__,
        instructions=(
            "Answer questions from the configured local PaperQA corpus and return a "
            "cited answer."
        ),
    )

    @server.tool(name="paperqa_ask")
    async def paperqa_ask(
        question: Annotated[
            str,
            Field(
                min_length=1,
                description="A non-empty question to ask the configured paper corpus.",
            ),
        ],
    ) -> PaperQAAnswer:
        """Ask the configured PaperQA corpus a question."""
        if not question.strip():
            raise ToolError("question must not be empty")

        from paperqa.agents.main import agent_query

        try:
            async with _PAPERQA_QUERY_LOCK:
                response = await agent_query(question, _get_settings())
        except Exception as exc:
            logger.exception("paperqa_ask failed")
            raise ToolError(f"PaperQA query failed: {exc}") from exc

        return PaperQAAnswer(
            answer=response.session.answer,
            formatted_answer=response.session.formatted_answer,
            status=str(response.status),
            cost=response.session.cost,
            source_count=len(response.session.contexts),
        )

    return server


def main() -> None:
    """Run the PaperQA MCP server over stdio."""
    _configure_logging()
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
