import random

import pytest
import pytest_asyncio
import redis.asyncio as aredis

from homework.tasks.redis_task import UsersByTitleStorage


class UsersByTitleStorageTest(UsersByTitleStorage):
    async def flushall(self) -> None:
        await self._client.flushall()


@pytest.mark.asyncio
async def test_redis_available():
    client = aredis.StrictRedis()
    pong = await client.ping()
    assert pong

    await client.aclose()


@pytest_asyncio.fixture
async def storage() -> UsersByTitleStorageTest:
    s = UsersByTitleStorageTest()
    await s.connect()
    yield s
    await s.flushall()
    await s.disconnect()


@pytest.mark.asyncio
async def test_redis_just_works(storage: UsersByTitleStorageTest):
    await storage.save_item(1, "Привет!")
    await storage.save_item(1, "Мир!")
    await storage.save_item(2, "Привет!")

    assert sorted(await storage.find_users_by_title("Привет!")) == [
        1,
        2,
    ], "Найденные user_id не соответствуют ожидаемым!"


@pytest.mark.asyncio
async def test_redis_stress_test(storage: UsersByTitleStorageTest, faker):
    def dummy_solution(items: list[tuple[int, str]]) -> dict[str, list[int]]:
        items_by_title = {}
        for user_id, title in items:
            items_by_title.setdefault(title, set())
            items_by_title[title].add(user_id)

        return {title: sorted(user_ids) for title, user_ids in items_by_title.items()}

    titles = [faker.name() for _ in range(7)]
    for items_count in range(1, 100):
        items = [
            (random.randint(0, 10), random.choice(titles)) for _ in range(items_count)
        ]
        for user_id, title in items:
            await storage.save_item(user_id, title)

        expected = dummy_solution(items)
        for title in titles:
            found_user_ids = sorted(await storage.find_users_by_title(title))
            expected_user_ids = expected.get(title, [])
            assert (
                found_user_ids == expected_user_ids
            ), f"Найденные user_id не совпадают с ожидаемыми! {items=}"

        # cleanup to avoid tests mutual influence
        await storage.flushall()
