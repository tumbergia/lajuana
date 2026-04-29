import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.tools import MongoDBVectorClient, create_tourist_tools, create_ops_tools

@pytest.fixture
def mock_vector_client():
    mc = AsyncMock()
    mc.search = AsyncMock(return_value="vector info")
    return mc

def test_tourist_tools_uses_public_scope(mock_vector_client):
    tools = create_tourist_tools(booking_service=MagicMock(), vector_client=mock_vector_client)
    
    search_tool = next((t for t in tools if t.name == "search_information"), None)
    assert search_tool is not None
    
    asyncio.run(search_tool.ainvoke({"query": "horarios"}))
    
    mock_vector_client.search.assert_called_once_with("horarios", scope="public")


def test_ops_tools_uses_public_and_ops_scope(mock_vector_client):
    tools = create_ops_tools(
        ops_service=MagicMock(),
        reservation_service=MagicMock(),
        participant_service=MagicMock(),
        equine_service=MagicMock(),
        schedule_service=MagicMock(),
        saddle_service=MagicMock(),
        vector_client=mock_vector_client,
    )
    
    search_ops_tool = next((t for t in tools if t.name == "search_ops_information"), None)
    assert search_ops_tool is not None
    
    asyncio.run(search_ops_tool.ainvoke({"query": "alimentacion caballos"}))
    
    mock_vector_client.search.assert_called_once_with("alimentacion caballos", scope=["public", "ops"])


def test_vector_client_rejects_non_string_query():
    client = MongoDBVectorClient()

    with pytest.raises(ValueError, match="Vector search query must be a string or a list of strings"):
        asyncio.run(client.search({"query": "alimentacion caballos"}))
