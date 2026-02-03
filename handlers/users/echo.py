from aiogram import types
from loader import dp

# ------------------------------------------------------------------------------------------
# BU YERDA HAM O'ZGARISH BOR: chat_type=types.ChatType.PRIVATE
# Bu degani bot guruhdagi oddiy gaplarni eshitmaydi, faqat lichkaga yozsa javob beradi.
# ------------------------------------------------------------------------------------------
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=None)
async def bot_echo(message: types.Message):
    # Bu yerda xohlasang javob qaytar, xohlasang shunchaki 'pass' deb yozib qo'y.
    # Hozircha user yozgan gapni o'ziga qaytaradi (faqat lichkada):
    await message.answer(message.text)