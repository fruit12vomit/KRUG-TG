import os
import asyncio
import uuid
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "⭕️ Привет! Я <b>КРУЖОК</b> — превращаю видео в кружочки!\n\n"
        "Просто отправь мне видео 🎥 и получи готовый кружочек за секунды ✨\n\n"
        "⚠️ <b>Ограничения:</b>\n"
        "• Длина: до 60 секунд\n"
        "• Размер: до 50 МБ",
        parse_mode="HTML"
    )

@router.message(F.video | F.document)
async def handle_video(message: Message):
    status_msg = await message.answer("⭕️ Делаю кружочек...")
    if message.video:
        file = message.video
        if file.duration and file.duration > 60:
            await status_msg.edit_text("❌ Видео длиннее 60 секунд!")
            return
    else:
        file = message.document
        if not file.mime_type or not file.mime_type.startswith("video"):
            await status_msg.edit_text("❌ Это не видеофайл!")
            return
    if file.file_size and file.file_size > 50 * 1024 * 1024:
        await status_msg.edit_text("❌ Файл слишком большой (макс. 50 МБ).")
        return
    uid = str(uuid.uuid4())[:8]
    input_path = f"/tmp/input_{uid}.mp4"
    output_path = f"/tmp/output_{uid}.mp4"
    try:
        tg_file = await message.bot.get_file(file.file_id)
        await message.bot.download_file(tg_file.file_path, input_path)
        await status_msg.edit_text("✨ Почти готово...")
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "crop=min(iw\\,ih):min(iw\\,ih),scale=640:640",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-c:a", "aac", "-b:a", "64k",
            "-movflags", "+faststart", "-t", "60", output_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("Ошибка FFmpeg")
        with open(output_path, "rb") as video_file:
            await message.answer_video_note(video_file)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

@router.message()
async def handle_other(message: Message):
    await message.answer("⭕️ Отправь мне видео, и я сделаю кружочек!")
