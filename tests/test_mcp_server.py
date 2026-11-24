from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("mcp")

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from paperqa.agents.models import AgentStatus
from paperqa.mcp_server import create_server, main

pytestmark = pytest.mark.offline


def _make_response(question: str) -> SimpleNamespace:
    return SimpleNamespace(
        session=SimpleNamespace(
            answer=f"Answer to {question}",
            formatted_answer=f"Question: {question}\n\nAnswer to {question}",
            cost=0.42,
            contexts=[object(), object()],
        ),
        status=AgentStatus.SUCCESS,
    )


@pytest.mark.asyncio
async def test_server_advertises_only_paperqa_ask() -> None:
    async with Client(create_server()) as client:
        result = await client.list_tools()

    assert [tool.name for tool in result.tools] == ["paperqa_ask"]
    tool = result.tools[0]
    assert tool.input_schema["required"] == ["question"]
    assert tool.input_schema["properties"]["question"]["type"] == "string"
    assert tool.input_schema["properties"]["question"]["minLength"] == 1
    assert tool.output_schema is not None
    assert set(tool.output_schema["properties"]) == {
        "answer",
        "formatted_answer",
        "status",
        "cost",
        "source_count",
    }


@pytest.mark.asyncio
async def test_paperqa_ask_returns_minimal_answer_fields() -> None:
    agent_query = AsyncMock(side_effect=lambda question, _: _make_response(question))
    with (
        patch("paperqa.agents.main.agent_query", agent_query),
        patch("paperqa.mcp_server._get_settings", return_value=object()),
    ):
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "paperqa_ask", {"question": "What is the main finding?"}
            )

    assert result.is_error is False
    assert result.structured_content == {
        "answer": "Answer to What is the main finding?",
        "formatted_answer": (
            "Question: What is the main finding?\n\nAnswer to What is the main finding?"
        ),
        "status": "success",
        "cost": 0.42,
        "source_count": 2,
    }
    agent_query.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("question", ["", "   "])
async def test_paperqa_ask_rejects_empty_question(question: str) -> None:
    agent_query = AsyncMock()
    with patch("paperqa.agents.main.agent_query", agent_query):
        async with Client(create_server()) as client:
            result = await client.call_tool("paperqa_ask", {"question": question})

    assert result.is_error is True
    agent_query.assert_not_awaited()


@pytest.mark.asyncio
async def test_paperqa_ask_uses_configured_settings_and_paper_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPERQA_SETTINGS", "custom")
    monkeypatch.setenv("PAPERQA_PAPER_DIRECTORY", "/papers/custom")
    settings = SimpleNamespace(
        agent=SimpleNamespace(index=SimpleNamespace(paper_directory="data.mock"))
    )
    get_settings = MagicMock(return_value=settings)
    agent_query = AsyncMock(side_effect=lambda question, _: _make_response(question))
    with (
        patch("paperqa.settings.get_settings", get_settings),
        patch("paperqa.agents.main.agent_query", agent_query),
    ):
        async with Client(create_server()) as client:
            await client.call_tool("paperqa_ask", {"question": "Which papers?"})

    get_settings.assert_called_once_with("custom")
    assert settings.agent.index.paper_directory == "/papers/custom"


@pytest.mark.asyncio
async def test_concurrent_calls_are_serialized() -> None:
    active_count = 0
    max_active_count = 0

    async def agent_query(question: str, _: object) -> SimpleNamespace:
        nonlocal active_count, max_active_count
        active_count += 1
        max_active_count = max(max_active_count, active_count)
        await asyncio.sleep(0.05)
        active_count -= 1
        return _make_response(question)

    with (
        patch("paperqa.agents.main.agent_query", side_effect=agent_query),
        patch("paperqa.mcp_server._get_settings", return_value=object()),
    ):
        async with Client(create_server()) as client:
            results = await asyncio.gather(
                client.call_tool("paperqa_ask", {"question": "First"}),
                client.call_tool("paperqa_ask", {"question": "Second"}),
            )

    assert all(not result.is_error for result in results)
    assert max_active_count == 1


@pytest.mark.asyncio
async def test_paperqa_failure_is_a_tool_error_and_server_stays_available() -> None:
    def agent_query(question: str, _: object) -> SimpleNamespace:
        if question == "fail":
            raise RuntimeError("simulated failure")
        return _make_response(question)

    with (
        patch("paperqa.agents.main.agent_query", side_effect=agent_query),
        patch("paperqa.mcp_server._get_settings", return_value=object()),
    ):
        async with Client(create_server()) as client:
            failed = await client.call_tool("paperqa_ask", {"question": "fail"})
            available = await client.list_tools()
            succeeded = await client.call_tool("paperqa_ask", {"question": "recover"})

    assert failed.is_error is True
    assert isinstance(failed.content[0], TextContent)
    assert "simulated failure" in failed.content[0].text
    assert [tool.name for tool in available.tools] == ["paperqa_ask"]
    assert succeeded.is_error is False


@pytest.mark.asyncio
async def test_stdio_server_keeps_protocol_on_stdout_and_survives_tool_errors() -> None:
    script_path = Path(sys.executable).with_name("paperqa-mcp")
    command = shutil.which("paperqa-mcp") or (
        str(script_path) if script_path.exists() else None
    )
    assert command is not None
    server_params = StdioServerParameters(
        command=command,
        cwd=Path(__file__).parent.parent,
        env={"PAPERQA_SETTINGS": "__missing_test_preset__"},
    )

    async with Client(server_params) as client:
        initial_tools = await client.list_tools()
        failed = await client.call_tool("paperqa_ask", {"question": "A question"})
        remaining_tools = await client.list_tools()

    assert [tool.name for tool in initial_tools.tools] == ["paperqa_ask"]
    assert failed.is_error is True
    assert [tool.name for tool in remaining_tools.tools] == ["paperqa_ask"]


def test_main_runs_stdio_transport() -> None:
    server = MagicMock()
    with (
        patch("paperqa.mcp_server._configure_logging"),
        patch("paperqa.mcp_server.create_server", return_value=server),
    ):
        main()

    server.run.assert_called_once_with(transport="stdio")
