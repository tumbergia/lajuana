import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.tools import MongoDBVectorClient
from app.core.config import settings

@pytest.fixture(autouse=True)
def mock_knowledge_document():
    with patch("app.agents.tools.KnowledgeDocument", autospec=True) as mock_doc:
        yield mock_doc

@pytest.fixture
def mongo_vector_client():
    client = MongoDBVectorClient()
    client.embeddings = AsyncMock()
    client.embeddings.aembed_query.return_value = [0.1, 0.2, 0.3]
    return client

@pytest.mark.asyncio
async def test_search_pipeline_called_with_correct_scope_public(mongo_vector_client, mock_knowledge_document):
    mock_collection = MagicMock()
    mock_aggregate = MagicMock()
    mock_aggregate.to_list = AsyncMock(return_value=[
        {"text": "Texto public", "source": "docs/public.md", "score": 0.9, "scope": "public"}
    ])
    mock_collection.aggregate.return_value = mock_aggregate
    mock_knowledge_document.get_motor_collection.return_value = mock_collection

    result = await mongo_vector_client.search("Dime algo", scope="public")
    
    assert "Texto public" in result
    
    mock_collection.aggregate.assert_called_once()
    pipeline = mock_collection.aggregate.call_args[0][0]
    vector_search_stage = pipeline[0]["$vectorSearch"]
    assert vector_search_stage["filter"]["scope"] == {"$in": ["public"]}

@pytest.mark.asyncio
async def test_search_pipeline_called_with_correct_scope_list(mongo_vector_client, mock_knowledge_document):
    mock_collection = MagicMock()
    mock_aggregate = MagicMock()
    mock_aggregate.to_list = AsyncMock(return_value=[
        {"text": "Texto ops", "source": "docs/ops.md", "score": 0.9, "scope": "ops"}
    ])
    mock_collection.aggregate.return_value = mock_aggregate
    mock_knowledge_document.get_motor_collection.return_value = mock_collection

    result = await mongo_vector_client.search("Dime algo", scope=["public", "ops"])
    
    assert "Texto ops" in result
    
    pipeline = mock_collection.aggregate.call_args[0][0]
    vector_search_stage = pipeline[0]["$vectorSearch"]
    assert vector_search_stage["filter"]["scope"] == {"$in": ["public", "ops"]}

@pytest.mark.asyncio
async def test_search_no_results(mongo_vector_client, mock_knowledge_document):
    mock_collection = MagicMock()
    mock_aggregate = MagicMock()
    mock_aggregate.to_list = AsyncMock(return_value=[])
    mock_collection.aggregate.return_value = mock_aggregate
    mock_knowledge_document.get_motor_collection.return_value = mock_collection

    result = await mongo_vector_client.search("Dime algo", scope="public")
    
    assert result == "No se encontró información relevante en la base de conocimientos."
