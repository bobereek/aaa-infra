import asyncpg
import pytest
import pytest_asyncio

from homework.tasks.pg_task import ItemStorage, ItemEntry


class ItemStorageTest(ItemStorage):
    async def drop_tables(self) -> None:
        # Remove entire table.
        await self._pool.execute("DROP TABLE items;")

    async def get_items_count(self) -> int:
        return await self._pool.fetchval("SELECT count(*) FROM items;")


@pytest.mark.asyncio
async def test_postgres_available():
    conn: asyncpg.Connection = await asyncpg.connect()
    values = await conn.fetchrow(
        "SELECT 1",
    )
    assert values
    await conn.close()


@pytest_asyncio.fixture()
async def item_storage() -> ItemStorageTest:
    db = ItemStorageTest()
    await db.connect()
    await db.create_tables_structure()
    yield db
    await db.drop_tables()
    await db.disconnect()


@pytest.mark.asyncio
async def test_insert_just_works(item_storage: ItemStorageTest):
    items = [
        ItemEntry(item_id=1, user_id=7, title="test1", description="test2"),
        ItemEntry(item_id=2, user_id=7, title="test1", description="test2"),
    ]
    await item_storage.save_items(items)
    assert await item_storage.get_items_count() == 2


@pytest.mark.parametrize(
    "items,violation_expected",
    [
        (
            [
                ItemEntry(item_id=1, user_id=7, title="test1", description="test2"),
                ItemEntry(item_id=1, user_id=7, title="test1", description="test2"),
            ],
            asyncpg.UniqueViolationError,
        ),
        (
            [
                ItemEntry(item_id=1, user_id=None, title="test1", description="test2"),
            ],
            asyncpg.NotNullViolationError,
        ),
        (
            [
                ItemEntry(item_id=1, user_id=7, title=None, description="test2"),
            ],
            asyncpg.NotNullViolationError,
        ),
        (
            [
                ItemEntry(item_id=1, user_id=7, title="test1", description=None),
            ],
            asyncpg.NotNullViolationError,
        ),
    ],
)
@pytest.mark.asyncio
async def test_insert_violations(
    item_storage: ItemStorageTest,
    items: list[ItemEntry],
    violation_expected: type[asyncpg.IntegrityConstraintViolationError],
):
    with pytest.raises(violation_expected):
        await item_storage.save_items(items)

    assert await item_storage.get_items_count() == 0, "Таблица items не пуста!"


@pytest.mark.asyncio
async def test_find_works(item_storage: ItemStorageTest):
    items = [
        ItemEntry(item_id=1, user_id=7, title="test1", description="test2"),
        ItemEntry(item_id=2, user_id=7, title="test1", description="test2"),
        ItemEntry(item_id=3, user_id=8, title="test1", description="test2"),
    ]
    await item_storage.save_items(items)

    found = await item_storage.find_similar_items(
        user_id=7, title="test1", description="test2"
    )
    assert sorted([i.item_id for i in found]) == [
        1,
        2,
    ], "Найденные item_id не совпадают с ожидаемыми!"
