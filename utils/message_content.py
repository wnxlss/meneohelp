from dataclasses import dataclass
from datetime import datetime, timezone

from aiogram.types import Message


@dataclass(slots=True)
class MessagePayload:
    text: str | None
    file_id: str | None
    file_type: str | None
    sent_at: datetime


def extract_payload(message: Message) -> MessagePayload:
    if message.text:
        return MessagePayload(text=message.text, file_id=None, file_type=None, sent_at=datetime.now(timezone.utc))
    if message.caption:
        text = message.caption
    else:
        text = None
    if message.photo:
        return MessagePayload(
            text=text,
            file_id=message.photo[-1].file_id,
            file_type="photo",
            sent_at=datetime.now(timezone.utc),
        )
    if message.document:
        return MessagePayload(
            text=text,
            file_id=message.document.file_id,
            file_type="document",
            sent_at=datetime.now(timezone.utc),
        )
    if message.video:
        return MessagePayload(
            text=text,
            file_id=message.video.file_id,
            file_type="video",
            sent_at=datetime.now(timezone.utc),
        )
    if message.audio:
        return MessagePayload(
            text=text,
            file_id=message.audio.file_id,
            file_type="audio",
            sent_at=datetime.now(timezone.utc),
        )
    if message.voice:
        return MessagePayload(
            text=text,
            file_id=message.voice.file_id,
            file_type="voice",
            sent_at=datetime.now(timezone.utc),
        )
    return MessagePayload(
        text=text or "[Неподдерживаемый тип сообщения]",
        file_id=None,
        file_type="unsupported",
        sent_at=datetime.now(timezone.utc),
    )
