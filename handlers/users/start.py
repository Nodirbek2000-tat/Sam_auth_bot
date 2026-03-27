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

    # Registratsiya sozlamasini tekshirish
    registration_enabled = (await db.get_setting("registration_enabled", "true")) == "true"

    if registration_enabled:
        # ON — profil holatini tekshirish
        profile = await db.get_user_profile(message.from_user.id)

        if not profile:
            # Profil yo'q — ro'yxatdan o'tishni taklif qilish
            await message.answer(
                f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
                "📝 Botdan foydalanish uchun avval ma'lumotlaringizni to'ldiring:",
                reply_markup=get_start_keyboard(has_profile=False)
            )
        elif profile['is_rejected']:
            # Rad etilgan — qayta ro'yxatdan o'tishni taklif qilish
            await message.answer(
                f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
                "❌ Sizning so'rovingiz avval rad etilgan.\n\n"
                "🔄 Qayta ro'yxatdan o'tishingiz mumkin:",
                reply_markup=get_start_keyboard(has_profile=True, is_rejected=True)
            )
        elif profile['is_approved']:
            # Tasdiqlangan — so'rovnomaga yo'naltirish
            await message.answer(
                f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
                "✅ Profilingiz tasdiqlangan!\n\n"
                "📋 So'rovnomani to'ldirish uchun tugmani bosing:",
                reply_markup=get_start_keyboard(has_profile=True, is_approved=True)
            )
        else:
            # Kutish rejimida
            await message.answer(
                f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
                "⏳ Sizning so'rovingiz ko'rib chiqilmoqda.\n\n"
                "Admin tasdiqlashini kuting.",
                reply_markup=get_start_keyboard(has_profile=True)
            )
    else:
        # OFF — to'g'ridan so'rovnoma
        await message.answer(
            f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
            "📋 So'rovnomani to'ldirish uchun tugmani bosing:",
            reply_markup=get_start_keyboard(has_profile=True, is_approved=True)
        )


@dp.callback_query_handler(text="check_subscription", state='*')
async def callback_check_subscription(callback: types.CallbackQuery, state: FSMContext):
    from utils.subscription import check_subscription, get_subscribe_keyboard

    result = await check_subscription(bot, db, callback.from_user.id)

    if result["is_subscribed"]:
        registration_enabled = (await db.get_setting("registration_enabled", "true")) == "true"

        if registration_enabled:
            profile = await db.get_user_profile(callback.from_user.id)

            if not profile:
                await callback.message.edit_text(
                    "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                    "📝 Endi ma'lumotlaringizni to'ldiring:",
                    reply_markup=get_start_keyboard(has_profile=False)
                )
            elif profile['is_rejected']:
                await callback.message.edit_text(
                    "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                    "❌ Sizning so'rovingiz avval rad etilgan.\n\n"
                    "🔄 Qayta ro'yxatdan o'tishingiz mumkin:",
                    reply_markup=get_start_keyboard(has_profile=True, is_rejected=True)
                )
            elif profile['is_approved']:
                await callback.message.edit_text(
                    "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                    "📋 So'rovnomani to'ldirish uchun tugmani bosing:",
                    reply_markup=get_start_keyboard(has_profile=True, is_approved=True)
                )
            else:
                await callback.message.edit_text(
                    "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                    "⏳ Sizning so'rovingiz ko'rib chiqilmoqda.\n\n"
                    "Admin tasdiqlashini kuting.",
                    reply_markup=get_start_keyboard(has_profile=True)
                )
        else:
            await callback.message.edit_text(
                "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
                "📋 So'rovnomani to'ldirish uchun tugmani bosing:",
                reply_markup=get_start_keyboard(has_profile=True, is_approved=True)
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