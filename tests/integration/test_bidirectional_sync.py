from types import SimpleNamespace

import pytest

from services.relay import send_copy


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict]] = []

    async def send_message(self, **kwargs):
        self.sent.append(("message", kwargs))
        return SimpleNamespace(message_id=1)

    async def send_photo(self, **kwargs):
        self.sent.append(("photo", kwargs))
        return SimpleNamespace(message_id=2)

    async def send_document(self, **kwargs):
        self.sent.append(("document", kwargs))
        return SimpleNamespace(message_id=3)

    async def send_video(self, **kwargs):
        self.sent.append(("video", kwargs))
        return SimpleNamespace(message_id=4)

    async def send_audio(self, **kwargs):
        self.sent.append(("audio", kwargs))
        return SimpleNamespace(message_id=5)

    async def send_voice(self, **kwargs):
        self.sent.append(("voice", kwargs))
        return SimpleNamespace(message_id=6)


@pytest.mark.asyncio
async def test_private_to_topic_sync():
    source = SimpleNamespace(
        text="Не могу оплатить",
        caption=None,
        photo=None,
        document=None,
        video=None,
        audio=None,
        voice=None,
    )
    bot = FakeBot()
    await send_copy(bot, source, chat_id=-100100, message_thread_id=77)
    msg_type, payload = bot.sent[0]
    assert msg_type == "message"
    assert payload["chat_id"] == -100100
    assert payload["message_thread_id"] == 77


@pytest.mark.asyncio
async def test_topic_to_private_sync():
    source = SimpleNamespace(
        text=None,
        caption="Скриншот ошибки",
        photo=[SimpleNamespace(file_id="small"), SimpleNamespace(file_id="large")],
        document=None,
        video=None,
        audio=None,
        voice=None,
    )
    bot = FakeBot()
    await send_copy(bot, source, chat_id=123456789)
    msg_type, payload = bot.sent[0]
    assert msg_type == "photo"
    assert payload["chat_id"] == 123456789
    assert payload["photo"] == "large"
