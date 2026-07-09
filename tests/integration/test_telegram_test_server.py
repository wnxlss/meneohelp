import os

import pytest


@pytest.mark.asyncio
async def test_telegram_test_server_bridge() -> None:
    base_url = os.getenv("TELEGRAM_TEST_SERVER_URL")
    if not base_url:
        pytest.skip("TELEGRAM_TEST_SERVER_URL не задан")
    assert base_url.startswith("http")
