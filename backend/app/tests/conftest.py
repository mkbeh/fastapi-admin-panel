import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

import asyncio
from typing import Generator

import pytest
from httpx import AsyncClient

from main import app
from db import db_init
from db.sessions import in_transaction
from .utils import *


# store history of failures per test class name and per
# index in parametrize (if parametrize used)
_test_failed_incremental: dict[str, dict[tuple[int, ...], str]] = {}


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        # incremental marker is used
        if call.excinfo is not None:
            # the test has failed
            # retrieve the class name of the test
            cls_name = str(item.cls)
            # retrieve the index of the test (if parametrize
            # is used in combination with incremental)
            parametrize_index = (
                tuple(item.callspec.indices.values())
                if hasattr(item, "callspec")
                else ()
            )
            # retrieve the name of the test function
            test_name = item.originalname or item.name
            # store in _test_failed_incremental the original name of the failed test
            _test_failed_incremental.setdefault(cls_name, {}).setdefault(
                parametrize_index, test_name
            )


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        # retrieve the class name of the test
        cls_name = str(item.cls)
        # check if a previous test has failed for this class
        if cls_name in _test_failed_incremental:
            # retrieve the index of the test (if parametrize
            # is used in combination with incremental)
            parametrize_index = (
                tuple(item.callspec.indices.values())
                if hasattr(item, "callspec")
                else ()
            )
            # retrieve the name of the first test function to
            # fail for this class name and index
            test_name = _test_failed_incremental[cls_name].get(parametrize_index, None)
            # if name found, test has failed for the
            # combination of class name & test name
            if test_name is not None:
                pytest.xfail("previous test failed ({})".format(test_name))


@pytest.fixture(scope="class", autouse=True)
async def async_client(db) -> Generator:
    await db_init()

    headers = await get_token_headers()
    client = AsyncClient(
        app=app,
        base_url="http://testserver",
        headers=headers
    )
    async with client as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    yield asyncio.get_event_loop()


@pytest.fixture(scope="session")
async def db():
    async with in_transaction() as db:
        yield db
    await clear_db()
