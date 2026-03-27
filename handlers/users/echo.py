from aiogram import types
from loader import dp

# ------------------------------------------------------------------------------------------
# BU YERDA HAM O'ZGARISH BOR: chat_type=types.ChatType.PRIVATE
# Bu degani bot guruhdagi oddiy gaplarni eshitmaydi, faqat lichkaga yozsa javob beradi.
# ------------------------------------------------------------------------------------------
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=None)
async def bot_echo(message: types.Message):
    await message.answer(
        "Boshlash uchun /start ni bosing."
    )