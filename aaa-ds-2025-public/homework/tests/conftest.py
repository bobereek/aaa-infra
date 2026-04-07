import random

import pytest


@pytest.fixture(scope="session", autouse=True)
def random_seed():
    random.seed(42)


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    return 42
