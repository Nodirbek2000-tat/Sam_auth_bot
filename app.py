import asyncio
import logging

from aiogram import executor

import handlers
from loader import dp, db, bot
from data import config


async def on_startup(dispatcher):
    # Ma'lumotlar bazasini ulash
    await db.create()

    # Barcha jadvallarni yaratish
    await db.create_all_tables()

    # Super Admin qo'shish
    admin_id = config.ADMINS[0]

    try:
        await db.add_admin(telegram_id=int(admin_id), is_super=True, added_by=None)
        print(f"✅ Super Admin qo'shildi: {admin_id}")
    except Exception as e:
        print(f"⚠️ Admin qo'shishda xato (ehtimol allaqachon bor): {e}")

    print("✅ Bot ishga tushdi!")


async def on_shutdown(dispatcher):
    await bot.close()
    print("Bot to'xtatildi!")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )