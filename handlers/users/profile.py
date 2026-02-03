from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db
from keyboards.inline.buttons import get_profile_keyboard


@dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['profile'], state='*')
async def cmd_profile(message: types.Message, state: FSMContext):
    await state.finish()

    profile = await db.get_user_profile(message.from_user.id)

    if not profile:
        await message.answer(
            "⚠️ Sizda profil mavjud emas!\n\n"
            "/start - Ma'lumotlarni to'ldirish"
        )
        return

    # Profil ma'lumotlarini ko'rsatish
    text = "👤 <b>Sizning profilingiz:</b>\n\n"
    text += f"👤 Ism: <b>{profile['first_name']}</b>\n"
    text += f"👤 Familiya: <b>{profile['last_name']}</b>\n"
    text += f"📅 Tug'ilgan sana: <b>{profile['birth_date'].strftime('%d.%m.%Y')}</b>\n"
    text += f"📍 Manzil: <b>{profile['address']}</b>\n\n"

    if profile['is_approved']:
        text += "✅ Status: <b>Tasdiqlangan</b>"
    elif profile['is_rejected']:
        text += "❌ Status: <b>Rad etilgan</b>"
    else:
        text += "⏳ Status: <b>Ko'rib chiqilmoqda</b>"

    # Qo'shimcha javoblarni olish
    additional = await db.get_initial_responses(profile['id'])

    if additional:
        text += "\n\n<b>Qo'shimcha ma'lumotlar:</b>\n"
        for resp in additional:
            question = await db.get_initial_question(resp['question_id'])
            if question:
                if resp['answer_type'] == 'text' or resp['answer_type'] == 'choice':
                    text += f"• {question['question_text']}: <b>{resp['answer']}</b>\n"
                elif resp['answer_type'] == 'photo':
                    text += f"• {question['question_text']}: 📷 Rasm\n"
                elif resp['answer_type'] == 'location':
                    import json
                    loc = json.loads(resp['answer']) if isinstance(resp['answer'], str) else resp['answer']
                    link = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
                    text += f"• {question['question_text']}: <a href='{link}'>📍 Xaritada ko'rish</a>\n"

    await message.answer(
        text,
        reply_markup=get_profile_keyboard(profile['is_approved']),
        disable_web_page_preview=False
    )


@dp.callback_query_handler(text="profile:view", state='*')
async def callback_view_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    profile = await db.get_user_profile(callback.from_user.id)

    if not profile:
        await callback.message.edit_text(
            "⚠️ Sizda profil mavjud emas!\n\n"
            "/start - Ma'lumotlarni to'ldirish"
        )
        await callback.answer()
        return

    # Profil ma'lumotlarini ko'rsatish
    text = "👤 <b>Sizning profilingiz:</b>\n\n"
    text += f"👤 Ism: <b>{profile['first_name']}</b>\n"
    text += f"👤 Familiya: <b>{profile['last_name']}</b>\n"
    text += f"📅 Tug'ilgan sana: <b>{profile['birth_date'].strftime('%d.%m.%Y')}</b>\n"
    text += f"📍 Manzil: <b>{profile['address']}</b>\n\n"

    if profile['is_approved']:
        text += "✅ Status: <b>Tasdiqlangan</b>"
    elif profile['is_rejected']:
        text += "❌ Status: <b>Rad etilgan</b>"
    else:
        text += "⏳ Status: <b>Ko'rib chiqilmoqda</b>"

    # Qo'shimcha javoblarni olish
    additional = await db.get_initial_responses(profile['id'])

    if additional:
        text += "\n\n<b>Qo'shimcha ma'lumotlar:</b>\n"
        for resp in additional:
            question = await db.get_initial_question(resp['question_id'])
            if question:
                if resp['answer_type'] == 'text' or resp['answer_type'] == 'choice':
                    text += f"• {question['question_text']}: <b>{resp['answer']}</b>\n"
                elif resp['answer_type'] == 'photo':
                    text += f"• {question['question_text']}: 📷 Rasm\n"
                elif resp['answer_type'] == 'location':
                    import json
                    loc = json.loads(resp['answer']) if isinstance(resp['answer'], str) else resp['answer']
                    link = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
                    text += f"• {question['question_text']}: <a href='{link}'>📍 Xaritada ko'rish</a>\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_profile_keyboard(profile['is_approved']),
        disable_web_page_preview=False
    )
    await callback.answer()