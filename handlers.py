import os
import asyncio
import uuid
import json
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command

router = Router()

STATS_FILE = "/tmp/stats.json"
ADMIN_ID = 170998607

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {"users": [], "circles": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

@router.message(CommandStart())
async def cmd_start(message: Message):
    stats = load_stats()
    if message.from_user.id not in stats["users"]:
        stats["users"].append(message.from_user.id)
        save_stats(stats)
    await message.answer(
        "⭕️ Привет! Я КРУЖОК — превращаю видео в кружочки!\n\n"
        "Просто отправь мне видео 🎥 и получи готовый кружочек за секунды ✨\n\n"
        "⚠️ Ограничения:\n"
        "• Длина: до 60 секунд\n"
        "• Размер: до 50 МБ\n\n"
        "Сделано с любовью\n"
        "Лиза Требухова @fruit_vomit"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❗ Как использовать кружок\n\n"
        "1. Нажми «Переслать» на кружке\n"
        "2. Выбери свой чат или канал\n"
        "3. Включи «Скрыть отправителя»\n\n"
        "Готово — будет выглядеть как будто ты записал его сам 👌"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⭕️ Отправь мне видео, и я сделаю кружочек!")
        return
    stats = load_stats()
    await message.answer(
        f"📊 Статистика КРУЖОК\n\n"
        f"👤 Пользователей: {len(stats['users'])}\n"
        f"⭕️ Кружков сделано: {stats['circles']}"
    )

@router.message(F.video | F.document)
async def handle_video(message: Message):
    stats = load_stats()
    if message.from_user.id not in stats["users"]:
        stats["users"].append(message.from_user.id)
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
        await status_msg.edit_text(
            "❌ Видео слишком большое (больше 50 МБ)\n\n"
            "Отправь его не файлом, а как обычное видео — просто выбери из галереи и отправь 📲"
        )
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
            "-vf",
            "crop=min(iw\\,ih):min(iw\\,ih),scale=640:640,"
            "format=yuva420p,"
            "geq=lum='p(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lte(hypot(X-320\\,Y-320)\\,318)\\,255\\,0)',"
            "pad=640:640:0:0:black@1,"
            "format=yuv420p",
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

        video = FSInputFile(output_path)
        await message.answer_video(video)
        await status_msg.delete()
        stats["circles"] += 1
        save_stats(stats)
        await message.answer("Готово ✔️ твой кружок выше 👆🏿\nВозвращайся 🖤")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

@router.message()
async def handle_other(message: Message):
    await message.answer("⭕️ Отправь мне видео, и я сделаю кружочек!")
