import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.sync_knowledge import sync_knowledge

@pytest.fixture
def mock_generate_embedding():
    with patch("app.sync_knowledge.generate_embedding", new_callable=AsyncMock) as mocked:
        mocked.return_value = [0.1, 0.2]
        yield mocked

@pytest.fixture
def mock_experience_doc():
    with patch("app.sync_knowledge.ExperienceDocument") as mocked:
        mock_list = AsyncMock()
        experiencia = MagicMock(
            id="exp1",
            name="Paseo de Olla",
            short_description="Paseo",
            description="Un paseo en olla muy bueno",
            duration=30,
            price=50000,
            max_participants=10,
            includes=["Comida"],
            requirements=["Ropa comoda"],
            is_active=True
        )
        mock_list.to_list = AsyncMock(return_value=[experiencia])
        mocked.find.return_value = mock_list
        yield mocked

@pytest.fixture
def mock_equine_doc():
    with patch("app.sync_knowledge.EquineDocument") as mocked:
        mock_list = AsyncMock()
        equino = MagicMock(
            id="eq1",
            code="EQ-001",
            name="Rayo",
            breed="Paso Fino",
            birth_date="2020-01-01",
            sex="MACHO",
            special_features=["Alto"],
            role="Cabalgata",
            diet_type="Pasto",
            health_notes="Ninguna",
            is_active=True,
            is_available=True,
            availability_notes=""
        )
        mock_list.to_list = AsyncMock(return_value=[equino])
        mocked.find_all.return_value = mock_list
        yield mocked

@pytest.fixture
def mock_policy_doc():
    with patch("app.sync_knowledge.PolicyDocument") as mocked:
        mock_list = AsyncMock()
        policy = MagicMock(
            id="pol1",
            title="Politicas de cancelacion",
            category="Reservas",
            content="Ninguna cancelacion",
            is_active=True
        )
        mock_list.to_list = AsyncMock(return_value=[policy])
        mocked.find_all.return_value = mock_list
        yield mocked

@pytest.fixture
def mock_knowledge_doc():
    with patch("app.sync_knowledge.KnowledgeDocument") as mocked:
        collection = MagicMock()
        bulk_mock = AsyncMock()
        bulk_mock.return_value.inserted_count = 0
        bulk_mock.return_value.modified_count = 1
        bulk_mock.return_value.upserted_count = 2
        collection.bulk_write = bulk_mock
        
        mocked.get_motor_collection.return_value = collection
        yield mocked

@pytest.fixture
def mock_mongo_client():
    with patch("app.sync_knowledge.AsyncMongoClient") as mocked:
        yield mocked

@pytest.fixture
def mock_init_beanie():
    with patch("app.sync_knowledge.init_beanie", new_callable=AsyncMock) as mocked:
        yield mocked

@pytest.mark.asyncio
async def test_sync_knowledge(
    mock_init_beanie,
    mock_mongo_client,
    mock_knowledge_doc,
    mock_policy_doc,
    mock_equine_doc,
    mock_experience_doc,
    mock_generate_embedding,
):
    await sync_knowledge()
    
    mock_init_beanie.assert_called_once()
    mock_generate_embedding.assert_called()
    
    mock_knowledge_doc.get_motor_collection.assert_called()
    
    collection = mock_knowledge_doc.get_motor_collection.return_value
    assert collection.bulk_write.call_count == 1
    
    args, kwargs = collection.bulk_write.call_args
    requests = args[0]
    assert len(requests) == 3
