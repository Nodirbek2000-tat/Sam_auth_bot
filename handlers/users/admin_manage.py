from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from states.states import AdminState
from keyboards.inline.buttons import (
    get_admins_menu, get_admin_list_keyboard,
    get_admin_actions, get_admin_delete_confirm
)
from handlers.users.admin_panel import is_admin


@dp.callback_query_handler(text="admin:admins", state='*')
async def callback_admins_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    admins = await db.get_all_admins()
    super_admins_count = sum(1 for a in admins if a['is_super'])
    regular_admins_count = len(admins) - super_admins_count

    text = (
        "👥 <b>ADMINLAR</b>\n\n"
        f"📊 Jami: <b>{len(admins)}</b> ta\n"
        f"👑 Super Admin: <b>{super_admins_count}</b> ta\n"
        f"👤 Admin: <b>{regular_admins_count}</b> ta"
    )

    await callback.message.edit_text(text, reply_markup=get_admins_menu())
    await callback.answer()


@dp.callback_query_handler(text="admin_manage:add", state='*')
async def callback_add_admin(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat Super Admin qo'sha oladi!", show_alert=True)
        return

    await callback.message.edit_text(
        "👤 <b>Admin qo'shish</b>\n\n"
        "Yangi admin Telegram ID'sini kiriting:\n\n"
        "<i>ID bilish uchun: @userinfobot</i>"
    )

    await AdminState.add_admin.set()
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminState.add_admin)
async def process_add_admin(message: types.Message, state: FSMContext):
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri ID!\n"
            "Faqat raqam kiriting yoki /cancel bosing."
        )
        return

    if await db.is_admin(new_admin_id):
        await message.answer(
            "⚠️ Bu foydalanuvchi allaqachon admin!\n\n"
            "Boshqa ID kiriting yoki /cancel bosing."
        )
        return

    # ✅ added_by parametri qo'shildi
    await db.add_admin(telegram_id=new_admin_id, is_super=False, added_by=message.from_user.id)

    await state.finish()

    try:
        await bot.send_message(
            new_admin_id,
            "🎉 <b>Tabriklaymiz!</b>\n\n"
            "Siz admin sifatida tayinlandingiz!\n"
            "Admin panel: /admin"
        )
    except:
        pass

    await message.answer(
        f"✅ <b>Yangi admin qo'shildi!</b>\n\n"
        f"🆔 ID: <code>{new_admin_id}</code>\n\n"
        "/admin - Admin panel"
    )


@dp.callback_query_handler(text="admin_manage:add_super", state='*')
async def callback_add_super_admin(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat Super Admin qo'sha oladi!", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 <b>Super Admin qo'shish</b>\n\n"
        "Yangi Super Admin Telegram ID'sini kiriting:\n\n"
        "<i>ID bilish uchun: @userinfobot</i>"
    )

    await AdminState.add_super_admin.set()
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminState.add_super_admin)
async def process_add_super_admin(message: types.Message, state: FSMContext):
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri ID!\n"
            "Faqat raqam kiriting yoki /cancel bosing."
        )
        return

    if await db.is_admin(new_admin_id):
        await message.answer(
            "⚠️ Bu foydalanuvchi allaqachon admin!\n\n"
            "Boshqa ID kiriting yoki /cancel bosing."
        )
        return

    # ✅ added_by parametri qo'shildi
    await db.add_admin(telegram_id=new_admin_id, is_super=True, added_by=message.from_user.id)

    await state.finish()

    try:
        await bot.send_message(
            new_admin_id,
            "🎉 <b>Tabriklaymiz!</b>\n\n"
            "Siz Super Admin sifatida tayinlandingiz!\n"
            "Admin panel: /admin"
        )
    except:
        pass

    await message.answer(
        f"✅ <b>Yangi Super Admin qo'shildi!</b>\n\n"
        f"🆔 ID: <code>{new_admin_id}</code>\n\n"
        "/admin - Admin panel"
    )


@dp.callback_query_handler(text="admin_manage:list", state='*')
async def callback_admin_list(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    admins = await db.get_all_admins()

    if not admins:
        await callback.message.edit_text(
            "👥 <b>Adminlar ro'yxati</b>\n\n"
            "Hozircha adminlar yo'q.",
            reply_markup=get_admins_menu()
        )
        await callback.answer()
        return

    text = "👥 <b>Adminlar ro'yxati</b>\n\n"
    text += "👑 - Super Admin | 👤 - Admin\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_list_keyboard(admins, callback.from_user.id)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_manage:view:"), state='*')
async def callback_view_admin(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    admin_id = int(callback.data.split(":")[2])
    admin = await db.get_admin(admin_id)

    if not admin:
        await callback.answer("Admin topilmadi!", show_alert=True)
        return

    try:
        user = await bot.get_chat(admin_id)
        user_info = f"👤 {user.full_name}"
        if user.username:
            user_info += f" (@{user.username})"
    except:
        user_info = "👤 Noma'lum"

    status = "👑 Super Admin" if admin['is_super'] else "👤 Admin"

    text = (
        f"👤 <b>Admin ma'lumotlari</b>\n\n"
        f"{user_info}\n"
        f"🆔 ID: <code>{admin['telegram_id']}</code>\n"
        f"📊 Status: {status}\n"
        f"📅 Qo'shilgan: {admin['added_at'].strftime('%d.%m.%Y')}"
    )

    # Adminni qo'shgan kishi
    is_creator = admin.get('added_by') == callback.from_user.id if admin.get('added_by') else False

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_actions(admin_id, admin['is_super'], is_creator)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_manage:delete:") and "confirm" not in c.data, state='*')
async def callback_delete_admin(callback: types.CallbackQuery):
    if not await db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat Super Admin o'chira oladi!", show_alert=True)
        return

    admin_id = int(callback.data.split(":")[2])
    admin = await db.get_admin(admin_id)

    if not admin:
        await callback.answer("Admin topilmadi!", show_alert=True)
        return

    if admin['is_super']:
        await callback.answer("⛔ Super Adminni o'chirib bo'lmaydi!", show_alert=True)
        return

    # O'zini qo'shgan adminni o'chira olmasligi
    if admin.get('added_by') and admin['added_by'] != callback.from_user.id:
        await callback.answer("⛔ Faqat o'zi qo'shgan adminni o'chira oladi!", show_alert=True)
        return

    await callback.message.edit_text(
        f"🗑 <b>Adminni o'chirish</b>\n\n"
        f"🆔 ID: <code>{admin_id}</code>\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_admin_delete_confirm(admin_id)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_manage:delete_confirm:"), state='*')
async def callback_delete_admin_confirm(callback: types.CallbackQuery):
    if not await db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat Super Admin o'chira oladi!", show_alert=True)
        return

    admin_id = int(callback.data.split(":")[2])

    result = await db.remove_admin(admin_id)

    if not result:
        await callback.answer("O'chirib bo'lmadi!", show_alert=True)
        return

    try:
        await bot.send_message(
            admin_id,
            "⚠️ Sizning admin huquqlaringiz olib tashlandi."
        )
    except:
        pass

    await callback.message.edit_text(
        f"✅ Admin o'chirildi!\n\n"
        f"🆔 ID: <code>{admin_id}</code>"
    )
    await callback.answer("O'chirildi!")