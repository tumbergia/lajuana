from __future__ import annotations

import pytest

from app.common.enums import NotificationChannel
from app.core.db import preflight_notification_template_natural_key
from app.documents.notification_template_document import NotificationTemplateDocument
from app.migrations.seed_notification_templates import (
    SEED_TEMPLATES,
    seed_notification_templates,
)
from app.migrations.versions.fix_notification_template_natural_key_index import (
    COMPOUND_INDEX_NAME,
    FixNotificationTemplateNaturalKeyIndexMigration,
)


def test_notification_template_document_uses_compound_natural_key() -> None:
    indexes = NotificationTemplateDocument.Settings.indexes

    assert len(indexes) == 1
    assert indexes[0].document == {
        "name": COMPOUND_INDEX_NAME,
        "unique": True,
        "key": {"template_key": 1, "channel": 1},
    }


@pytest.mark.asyncio
async def test_seed_uses_template_key_and_channel_natural_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_pairs = {
        ("reservation_confirmed.internal", NotificationChannel.EMAIL),
    }
    inserted_pairs: list[tuple[str, NotificationChannel]] = []
    lookups: list[dict[str, object]] = []

    class FakeNotificationTemplateDocument:
        def __init__(self, **payload: object) -> None:
            self.payload = payload

        @classmethod
        async def find_one(cls, query: dict[str, object]) -> object | None:
            lookups.append(query)
            pair = (query["template_key"], query["channel"])
            if pair in existing_pairs:
                return object()
            return None

        async def insert(self) -> None:
            pair = (self.payload["template_key"], self.payload["channel"])
            inserted_pairs.append(pair)
            existing_pairs.add(pair)

    async def fake_init_db() -> None:
        return None

    monkeypatch.setattr(
        "app.migrations.seed_notification_templates.NotificationTemplateDocument",
        FakeNotificationTemplateDocument,
    )
    monkeypatch.setattr("app.migrations.seed_notification_templates.init_db", fake_init_db)

    created = await seed_notification_templates()

    assert created == len(SEED_TEMPLATES) - 1
    assert (
        "reservation_confirmed.internal",
        NotificationChannel.IN_APP,
    ) in inserted_pairs
    assert all(set(query) == {"template_key", "channel"} for query in lookups)


@pytest.mark.asyncio
async def test_notification_template_index_migration_drops_legacy_unique_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dropped_indexes: list[str] = []
    created_indexes: list[dict[str, object]] = []
    deleted_filters: list[dict[str, object]] = []

    class FakeCollection:
        async def list_indexes(self):
            class FakeIndexCursor:
                def __aiter__(self):
                    async def generator():
                        for index in [
                            {"name": "_id_", "key": {"_id": 1}},
                            {
                                "name": "template_key_1",
                                "key": {"template_key": 1},
                                "unique": True,
                            },
                        ]:
                            yield index

                    return generator()

            return FakeIndexCursor()

        async def drop_index(self, index_name: str) -> None:
            dropped_indexes.append(index_name)

        async def aggregate(self, pipeline: list[dict[str, object]]):
            assert pipeline[1]["$sort"] == {
                "template_key": 1,
                "channel": 1,
                "updated_at": -1,
                "created_at": -1,
                "_id": 1,
            }

            class FakeAggregateCursor:
                def __aiter__(self):
                    async def generator():
                        yield {
                            "_id": {
                                "template_key": "participant_form_resent.customer",
                                "channel": "whatsapp",
                            },
                            "ids": ["keep-id", "drop-id-1", "drop-id-2"],
                            "count": 3,
                        }

                    return generator()

            return FakeAggregateCursor()

        async def delete_many(self, filter_query: dict[str, object]):
            deleted_filters.append(filter_query)

            class Result:
                deleted_count = 2

            return Result()

        async def create_index(self, keys: list[tuple[str, int]], **kwargs: object) -> None:
            created_indexes.append({"keys": keys, **kwargs})

    class FakeDatabase:
        def __getitem__(self, name: str) -> FakeCollection:
            assert name == "notification_templates"
            return FakeCollection()

    class FakeClient:
        def get_default_database(self) -> FakeDatabase:
            return FakeDatabase()

    fake_db = type("FakeDbHolder", (), {"client": FakeClient()})()
    monkeypatch.setattr("app.core.db.db", fake_db)

    await FixNotificationTemplateNaturalKeyIndexMigration().apply()

    assert dropped_indexes == ["template_key_1"]
    assert deleted_filters == [{"_id": {"$in": ["drop-id-1", "drop-id-2"]}}]
    assert created_indexes == [
        {
            "keys": [("template_key", 1), ("channel", 1)],
            "unique": True,
            "name": COMPOUND_INDEX_NAME,
        }
    ]


@pytest.mark.asyncio
async def test_preflight_notification_template_natural_key_dedupes_by_pair() -> None:
    dropped_indexes: list[str] = []
    deleted_filters: list[dict[str, object]] = []

    class FakeCollection:
        async def list_indexes(self):
            class FakeIndexCursor:
                def __aiter__(self):
                    async def generator():
                        for index in [
                            {"name": "_id_", "key": {"_id": 1}},
                            {
                                "name": "template_key_1",
                                "key": {"template_key": 1},
                                "unique": True,
                            },
                            {
                                "name": COMPOUND_INDEX_NAME,
                                "key": {"template_key": 1, "channel": 1},
                                "unique": True,
                            },
                        ]:
                            yield index

                    return generator()

            return FakeIndexCursor()

        async def drop_index(self, index_name: str) -> None:
            dropped_indexes.append(index_name)

        async def aggregate(self, pipeline: list[dict[str, object]]):
            assert pipeline[0]["$match"] == {
                "template_key": {"$exists": True},
                "channel": {"$exists": True},
            }

            class FakeAggregateCursor:
                def __aiter__(self):
                    async def generator():
                        yield {
                            "_id": {
                                "template_key": "participant_form_resent.customer",
                                "channel": "whatsapp",
                            },
                            "ids": ["newest", "older", "oldest"],
                            "count": 3,
                        }

                    return generator()

            return FakeAggregateCursor()

        async def delete_many(self, filter_query: dict[str, object]):
            deleted_filters.append(filter_query)

            class Result:
                deleted_count = 2

            return Result()

    dropped, removed = await preflight_notification_template_natural_key(FakeCollection())

    assert dropped == ["template_key_1"]
    assert removed == 2
    assert dropped_indexes == ["template_key_1"]
    assert deleted_filters == [{"_id": {"$in": ["older", "oldest"]}}]
