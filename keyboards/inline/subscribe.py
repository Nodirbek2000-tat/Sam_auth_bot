from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_subscribe_keyboard(not_subscribed: list) -> InlineKeyboardMarkup:
    """
    Obuna bo'lish tugmalarini yaratish

    not_subscribed: Obuna bo'lmagan kanallar ro'yxati
        [{"name": "Kanal nomi", "username": "kanal_username"}, ...]
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Har bir kanal uchun tugma
    for channel in not_subscribed:
        keyboard.add(
            InlineKeyboardButton(
                text=f"📢 {channel['name']}",
                url=f"https://t.me/{channel['username']}"
            )
        )

    # Tekshirish tugmasi
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Tekshirish",
            callback_data="check_subscription"
        )
    )

    return keyboard