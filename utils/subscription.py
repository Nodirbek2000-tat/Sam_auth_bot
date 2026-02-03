from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def check_subscription(bot, db, user_id: int) -> dict:
    """Foydalanuvchi barcha kanallarga obuna bo'lganini tekshirish"""
    not_subscribed = []

    channels = await db.get_all_channels()

    if not channels:
        return {"is_subscribed": True, "not_subscribed": []}

    for channel in channels:
        try:
            member = await bot.get_chat_member(
                chat_id=f"@{channel['channel_username']}",
                user_id=user_id
            )

            if member.status in ["left", "kicked"]:
                not_subscribed.append({
                    "id": channel['id'],
                    "name": channel['channel_name'],
                    "username": channel['channel_username']
                })

        except Exception as e:
            print(f"Kanal tekshirishda xatolik ({channel['channel_username']}): {e}")
            not_subscribed.append({
                "id": channel['id'],
                "name": channel['channel_name'],
                "username": channel['channel_username']
            })

    return {
        "is_subscribed": len(not_subscribed) == 0,
        "not_subscribed": not_subscribed
    }


def get_subscribe_keyboard(not_subscribed: list) -> InlineKeyboardMarkup:
    """Obuna bo'lish tugmalarini yaratish"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel in not_subscribed:
        keyboard.add(
            InlineKeyboardButton(
                text=f"📢 {channel['name']}",
                url=f"https://t.me/{channel['username']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="✅ Tekshirish",
            callback_data="check_subscription"
        )
    )

    return keyboard


async def check_and_request_subscription(bot, db, message: types.Message) -> bool:
    """Obunani tekshirish va so'rash"""
    result = await check_subscription(bot, db, message.from_user.id)

    if not result["is_subscribed"]:
        await message.answer(
            "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>",
            reply_markup=get_subscribe_keyboard(result["not_subscribed"])
        )
        return False

    return True


async def check_bot_is_admin(bot, channel_username: str) -> dict:
    """Bot kanalda admin ekanligini tekshirish"""
    try:
        chat = await bot.get_chat(f"@{channel_username}")
        bot_member = await bot.get_chat_member(
            chat_id=f"@{channel_username}",
            user_id=(await bot.get_me()).id
        )

        if bot_member.status in ["administrator", "creator"]:
            return {
                "success": True,
                "channel_name": chat.title,
                "channel_username": channel_username
            }
        else:
            return {
                "success": False,
                "error": "Bot bu kanalda admin emas!"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Kanal topilmadi yoki bot qo'shilmagan: {str(e)}"
        }