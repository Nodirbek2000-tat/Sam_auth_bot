from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from utils.subscription import check_and_request_subscription
from keyboards.inline.buttons import get_start_keyboard


@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()

    # Foydalanuvchini bazaga qo'shish
    user = await db.get_user(message.from_user.id)

    if not user:
        # Yangi foydalanuvchi
        await db.add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )

    # Obuna tekshiruvi
    if not await check_and_request_subscription(bot, db, message):
        return

    # Profil ma'lumotlarini tekshirish
    profile = await db.get_user_profile(message.from_user.id)

    if not profile:
        # Boshlang'ich ma'lumotlar to'ldirilmagan
        await message.answer(
            f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
            "📝 Botdan foydalanish uchun avval ma'lumotlaringizni to'ldiring:",
            reply_markup=get_start_keyboard(has_profile=False)
        )
    else:
        # Profil mavjud, tasdiqlash statusini tekshirish
        if profile['is_approved']:
            await message.answer(
                f"👋 Assalomu alaykum, <b>{profile['first_name']} {profile['last_name']}</b>!\n\n"
                "✅ Sizning profilingiz tasdiqlangan.\n\n"
                "📝 So'rovnomani to'ldirish uchun tugmani bosing:",
                reply_markup=get_start_keyboard(has_profile=True, is_approved=True)
            )
        elif profile['is_rejected']:
            await message.answer(
                f"👋 Assalomu alaykum, <b>{profile['first_name']} {profile['last_name']}</b>!\n\n"
                "❌ Sizning profilingiz rad etilgan.\n\n"
                "📝 Qayta so'rov yuborish uchun tugmani bosing:",
                reply_markup=get_start_keyboard(has_profile=True, is_approved=False, is_rejected=True)
            )
        else:
            await message.answer(
                f"👋 Assalomu alaykum, <b>{profile['first_name']} {profile['last_name']}</b>!\n\n"
                "⏳ Sizning profilingiz admin tomonidan ko'rib chiqilmoqda.\n\n"
                "Iltimos, kuting...",
                reply_markup=get_start_keyboard(has_profile=True, is_approved=False)
            )


@dp.callback_query_handler(text="check_subscription", state='*')
async def callback_check_subscription(callback: types.CallbackQuery, state: FSMContext):
    from utils.subscription import check_subscription, get_subscribe_keyboard

    result = await check_subscription(bot, db, callback.from_user.id)

    if result["is_subscribed"]:
        profile = await db.get_user_profile(callback.from_user.id)

        if not profile:
            await callback.message.edit_text(
                "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                "📝 Endi ma'lumotlaringizni to'ldiring:",
                reply_markup=get_start_keyboard(has_profile=False)
            )
        else:
            if profile['is_approved']:
                await callback.message.edit_text(
                    "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                    "📝 So'rovnomani to'ldirish uchun tugmani bosing:",
                    reply_markup=get_start_keyboard(has_profile=True, is_approved=True)
                )
            else:
                await callback.message.edit_text(
                    "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                    "⏳ Profilingiz admin tomonidan ko'rib chiqilmoqda.",
                    reply_markup=get_start_keyboard(has_profile=True, is_approved=False)
                )
    else:
        await callback.message.edit_text(
            "⚠️ <b>Siz hali barcha kanallarga obuna bo'lmadingiz!</b>\n\n"
            "Quyidagi kanallarga obuna bo'ling:",
            reply_markup=get_subscribe_keyboard(result["not_subscribed"])
        )

    await callback.answer()


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("🤷 Bekor qiladigan narsa yo'q.")
        return

    await state.finish()
    await message.answer(
        "❌ Bekor qilindi.\n\n"
        "Qaytadan boshlash uchun /start buyrug'ini bosing."
    )