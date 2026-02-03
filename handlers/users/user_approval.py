from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from keyboards.inline.buttons import (
    get_user_approvals_menu,
    get_pending_users_keyboard,
    get_user_detail_keyboard
)
from handlers.users.admin_panel import is_admin


@dp.callback_query_handler(text="admin:user_approvals", state='*')
async def callback_user_approvals_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    pending_count = await db.count_pending_approvals()

    text = (
        "⏳ <b>FOYDALANUVCHILARNI TASDIQLASH</b>\n\n"
        f"📊 Kutayotgan so'rovlar: <b>{pending_count}</b> ta"
    )

    await callback.message.edit_text(text, reply_markup=get_user_approvals_menu())
    await callback.answer()


@dp.callback_query_handler(text="approval:pending_list", state='*')
async def callback_pending_users_list(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    pending_users = await db.get_pending_approvals()

    if not pending_users:
        await callback.message.edit_text(
            "⏳ <b>Kutayotgan so'rovlar</b>\n\n"
            "Hozircha kutayotgan so'rovlar yo'q.",
            reply_markup=get_user_approvals_menu()
        )
        await callback.answer()
        return

    text = "⏳ <b>Kutayotgan so'rovlar</b>\n\n"

    await callback.message.edit_text(text, reply_markup=get_pending_users_keyboard(pending_users))
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("approval:view:"), state='*')
async def callback_view_user_approval(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await db.get_user_profile_by_id(profile_id)

    if not profile:
        await callback.answer("Profil topilmadi!", show_alert=True)
        return

    # Foydalanuvchi ma'lumotlarini olish
    text = "👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
    text += f"👤 Ism: <b>{profile['first_name']}</b>\n"
    text += f"👤 Familiya: <b>{profile['last_name']}</b>\n"
    text += f"📅 Tug'ilgan sana: <b>{profile['birth_date'].strftime('%d.%m.%Y')}</b>\n"
    text += f"📍 Manzil: <b>{profile['address']}</b>\n"
    text += f"🆔 User ID: <code>{profile['telegram_id']}</code>\n"

    # Qo'shimcha javoblarni olish
    additional = await db.get_initial_responses(profile_id)

    if additional:
        text += "\n<b>Qo'shimcha ma'lumotlar:</b>\n"

        has_photos = False
        has_location = False

        for resp in additional:
            question = await db.get_initial_question(resp['question_id'])
            if question:
                if resp['answer_type'] == 'text' or resp['answer_type'] == 'choice':
                    text += f"• {question['question_text']}: <b>{resp['answer']}</b>\n"
                elif resp['answer_type'] == 'photo':
                    text += f"• {question['question_text']}: 📷 (pastda)\n"
                    has_photos = True
                elif resp['answer_type'] == 'location':
                    import json
                    loc = json.loads(resp['answer']) if isinstance(resp['answer'], str) else resp['answer']
                    link = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
                    text += f"• {question['question_text']}: <a href='{link}'>📍 Xaritada ko'rish</a>\n"
                    has_location = True

    # Rasmlarni yuborish
    if additional:
        photo_responses = [r for r in additional if r['answer_type'] == 'photo']

        if photo_responses:
            from aiogram.types import MediaGroup, InputMediaPhoto

            media = MediaGroup()
            for resp in photo_responses:
                question = await db.get_initial_question(resp['question_id'])
                caption = question['question_text'] if question else "Rasm"
                media.attach_photo(resp['answer'], caption=caption)

            try:
                await callback.message.answer_media_group(media)
            except:
                pass

    await callback.message.answer(
        text,
        reply_markup=get_user_detail_keyboard(profile_id),
        disable_web_page_preview=False
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("approval:approve:"), state='*')
async def callback_approve_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await db.get_user_profile_by_id(profile_id)

    if not profile:
        await callback.answer("Profil topilmadi!", show_alert=True)
        return

    # Tasdiqlash
    await db.approve_user_profile(profile_id)

    # Foydalanuvchiga xabar yuborish
    try:
        await bot.send_message(
            profile['telegram_id'],
            "✅ <b>Tabriklaymiz!</b>\n\n"
            "Sizning profilingiz tasdiqlandi!\n\n"
            "📝 Endi so'rovnomani to'ldirishingiz mumkin.\n"
            "/register - So'rovnomani boshlash"
        )
    except:
        pass

    await callback.message.edit_text(
        f"✅ <b>Foydalanuvchi tasdiqlandi!</b>\n\n"
        f"👤 {profile['first_name']} {profile['last_name']}\n"
        f"🆔 ID: <code>{profile['telegram_id']}</code>"
    )
    await callback.answer("Tasdiqlandi!")


@dp.callback_query_handler(lambda c: c.data.startswith("approval:reject:"), state='*')
async def callback_reject_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await db.get_user_profile_by_id(profile_id)

    if not profile:
        await callback.answer("Profil topilmadi!", show_alert=True)
        return

    # Rad etish
    await db.reject_user_profile(profile_id)

    # Foydalanuvchiga xabar yuborish
    try:
        await bot.send_message(
            profile['telegram_id'],
            "❌ <b>Afsuski!</b>\n\n"
            "Sizning profilingiz rad etildi.\n\n"
            "📝 Qayta so'rov yuborish uchun:\n"
            "/start - Boshlash"
        )
    except:
        pass

    await callback.message.edit_text(
        f"❌ <b>Foydalanuvchi rad etildi!</b>\n\n"
        f"👤 {profile['first_name']} {profile['last_name']}\n"
        f"🆔 ID: <code>{profile['telegram_id']}</code>"
    )
    await callback.answer("Rad etildi!")