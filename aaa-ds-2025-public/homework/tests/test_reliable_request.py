import asyncio
import random
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from asyncio_simple_http_server import HttpServer, uri_mapping, HttpResponse

from homework.tasks.reliable_request import ResultsObserver, do_reliable_request


class DataObserver(ResultsObserver):
    def __init__(self):
        self._data_observed = []

    def observe(self, data: bytes) -> None:
        self._data_observed.append(data)

    def get_observed_data(self) -> list[bytes]:
        return self._data_observed


class UsefulHttpServer(HttpServer):
    def __init__(self):
        super().__init__()
        self.port = random.randint(10000, 60000)

    async def connect(self, handler: Any):
        self.add_handler(handler)
        await self.start("localhost", self.port)

    async def disconnect(self):
        await self.close()


class HttpHandler:
    @uri_mapping("/good")
    async def good(self):
        return HttpResponse(200, body=b"Good!")

    @uri_mapping("/slow")
    async def slow(self):
        await asyncio.sleep(random.randrange(5, 10))
        return HttpResponse(200, body=b"Slow!")

    @uri_mapping("/fail")
    async def fail(self):
        if random.random() < 0.5:
            return HttpResponse(500)
        else:
            return HttpResponse(200, body=b"Fail!")


@pytest.fixture()
def observer() -> DataObserver:
    return DataObserver()


@pytest_asyncio.fixture
async def http_server_address() -> AsyncGenerator[str, None]:
    http_server = UsefulHttpServer()
    await http_server.connect(HttpHandler())
    yield f"http://localhost:{http_server.port}"
    await http_server.close()


@pytest.mark.asyncio
async def test_reliable_request(http_server_address: str, observer: DataObserver):
    try:
        await do_reliable_request(f"{http_server_address}/good", observer)
        await do_reliable_request(f"{http_server_address}/slow", observer)
        await do_reliable_request(f"{http_server_address}/fail", observer)
    except Exception as e:
        pytest.fail(f"Test failed due to unexpected exceptions {e}")

    assert observer.get_observed_data() == [b"Good!", b"Slow!", b"Fail!"]
