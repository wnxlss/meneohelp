from aiogram import Bot
from aiogram.types import Message


async def send_copy(bot: Bot, source: Message, chat_id: int, message_thread_id: int | None = None) -> Message:
    def kwargs():
        if message_thread_id is None:
            return {"chat_id": chat_id}
        return {"chat_id": chat_id, "message_thread_id": message_thread_id}

    if source.text:
        return await bot.send_message(text=source.text, **kwargs())
    if source.photo:
        return await bot.send_photo(photo=source.photo[-1].file_id, caption=source.caption, **kwargs())
    if source.document:
        return await bot.send_document(document=source.document.file_id, caption=source.caption, **kwargs())
    if source.video:
        return await bot.send_video(video=source.video.file_id, caption=source.caption, **kwargs())
    if source.audio:
        return await bot.send_audio(audio=source.audio.file_id, caption=source.caption, **kwargs())
    if source.voice:
        return await bot.send_voice(voice=source.voice.file_id, caption=source.caption, **kwargs())
    return await bot.send_message(text="Получено сообщение неподдерживаемого типа.", **kwargs())
