from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from keyboards.inline.buttons import get_bulk_approval_confirm_keyboard
from handlers.users.admin_panel import is_admin


@dp.callback_query_handler(text="approval:approve_all", state='*')
async def callback_approve_all_confirm(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    pending_count = await db.count_pending_approvals()

    if pending_count == 0:
        await callback.answer("Kutayotgan so'rovlar yo'q!", show_alert=True)
        return

    text = (
        "✅ <b>Hammasini tasdiqlash</b>\n\n"
        f"📊 Tasdiqlash uchun: <b>{pending_count}</b> ta so'rov\n\n"
        f"⚠️ Barcha kutayotgan foydalanuvchilar tasdiqlanadi!\n\n"
        f"Tasdiqlaysizmi?"
    )

    await callback.message.edit_text(text, reply_markup=get_bulk_approval_confirm_keyboard())
    await callback.answer()


@dp.callback_query_handler(text="approval:approve_all_confirm", state='*')
async def callback_approve_all_execute(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    await callback.message.edit_text("⏳ Jarayon davom etmoqda...")

    pending_users = await db.get_pending_approvals()

    success = 0
    failed = 0

    for user in pending_users:
        try:
            # Tasdiqlash
            await db.approve_user_profile(user['id'])

            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    user['telegram_id'],
                    "✅ <b>Tabriklaymiz!</b>\n\n"
                    "Sizning profilingiz tasdiqlandi!\n\n"
                    "📝 Endi so'rovnomani to'ldirishingiz mumkin.\n"
                    "/register - So'rovnomani boshlash"
                )
            except:
                pass

            success += 1
        except Exception as e:
            failed += 1
            print(f"Xato: {user['telegram_id']} - {e}")

    await callback.message.edit_text(
        f"✅ <b>Jarayon tugadi!</b>\n\n"
        f"Tasdiqlandi: <b>{success}</b> ta\n"
        f"Xato: <b>{failed}</b> ta"
    )
    await callback.answer("Tugadi!")


@dp.callback_query_handler(text="approval:approve_all_cancel", state='*')
async def callback_approve_all_cancel(callback: types.CallbackQuery):
    pending_count = await db.count_pending_approvals()

    text = (
        "⏳ <b>FOYDALANUVCHILARNI TASDIQLASH</b>\n\n"
        f"📊 Kutayotgan so'rovlar: <b>{pending_count}</b> ta"
    )

    from keyboards.inline.buttons import get_user_approvals_menu
    await callback.message.edit_text(text, reply_markup=get_user_approvals_menu())
    await callback.answer("Bekor qilindi")