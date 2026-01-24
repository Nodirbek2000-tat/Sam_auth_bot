from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Yo'nalishlar ro'yxati
YUNALISHLAR = [
    "“Iqtidorli yoshlar bilan ishlash” klubi rahbarligi",
    "Yoshlar ma’naviyatini yuksaltirish a'zoligi",
    "Axborot texnologiyalari a'zoligi",
    "Sport va sog‘lom turmush tarzini targ‘ib qilish a'zoligi",
    "Ijtimoiy faollik va lider yoshlar bilan ishlash a'zoligi",
    "Ijodkor yoshlar bilan ishlash a'zoligiga",
    "Yoshlarning takliflarini o‘rganish va rivojlantirish a'zoligi",
    "Yoshlar aql markazi a'zoligiga",
    "Inklyuziv va imkoniyati cheklangan yoshlar bilan ishlash a'zoligi",
]


def get_yunalish_keyboard():
    """Yo'nalishlar tugmalarini yaratish"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for i, yunalish in enumerate(YUNALISHLAR, 1):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{i}. {yunalish}",
                callback_data=f"yunalish_{i}"
            )
        )

    return keyboard


# Tasdiqlash tugmalari
confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_no")
        ]
    ]
)