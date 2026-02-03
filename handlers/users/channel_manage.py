from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, db, bot
from states.states import ChannelState
from utils.subscription import check_bot_is_admin
from keyboards.inline.buttons import (
    get_channels_menu, get_channel_list_keyboard,
    get_channel_actions, get_channel_delete_confirm
)
from handlers.users.admin_panel import is_admin


def get_cancel_keyboard(retry_callback: str):
    """Bekor qilish tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Qayta urinish", callback_data=retry_callback),
        InlineKeyboardButton("🔙 Admin panelga", callback_data="admin:back")
    )
    return keyboard


@dp.callback_query_handler(text="admin:channels", state='*')
async def callback_channels_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    channels_count = await db.count_channels()

    text = (
        "📢 <b>KANALLAR</b>\n\n"
        f"📊 Jami: <b>{channels_count}</b> ta\n\n"
        "Majburiy obuna kanallari"
    )

    await callback.message.edit_text(text, reply_markup=get_channels_menu())
    await callback.answer()


@dp.callback_query_handler(text="channel:add", state='*')
async def callback_add_channel(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    # Bekor qilish tugmasi
    cancel_kb = InlineKeyboardMarkup()
    cancel_kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="channel:cancel_add"))

    await callback.message.edit_text(
        "📢 <b>Kanal qo'shish</b>\n\n"
        "Kanal username'ini kiriting:\n"
        "<i>(Masalan: my_channel yoki @my_channel)</i>\n\n"
        "⚠️ Bot kanalda admin bo'lishi kerak!",
        reply_markup=cancel_kb
    )

    await ChannelState.add_channel.set()
    await callback.answer()


@dp.callback_query_handler(text="channel:cancel_add", state='*')
async def callback_cancel_add_channel(callback: types.CallbackQuery, state: FSMContext):
    """Kanal qo'shishni bekor qilish"""
    await state.finish()

    await callback.message.edit_text(
        "❌ <b>Bekor qilindi!</b>",
        reply_markup=get_cancel_keyboard("channel:add")
    )
    await callback.answer()


# Cancel buyrug'i FAQAT LICHKADA
@dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['cancel'], state=ChannelState.add_channel)
async def cmd_cancel_channel(message: types.Message, state: FSMContext):
    """Kanal qo'shishni /cancel bilan bekor qilish"""
    await state.finish()

    await message.answer(
        "❌ <b>Bekor qilindi!</b>",
        reply_markup=get_cancel_keyboard("channel:add")
    )


# Username qabul qilish FAQAT LICHKADA
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=ChannelState.add_channel)
async def process_add_channel(message: types.Message, state: FSMContext):
    username = message.text.strip()

    if username.startswith("@"):
        username = username[1:]

    if "t.me/" in username:
        username = username.split("t.me/")[-1]

    result = await check_bot_is_admin(bot, username)

    # Xatolik tugmalari
    error_kb = InlineKeyboardMarkup(row_width=1)
    error_kb.add(
        InlineKeyboardButton("🔄 Qayta urinish", callback_data="channel:add"),
        InlineKeyboardButton("🔙 Admin panelga", callback_data="admin:back")
    )

    if not result['success']:
        await state.finish()
        await message.answer(
            f"❌ <b>Xatolik!</b>\n\n{result['error']}",
            reply_markup=error_kb
        )
        return

    channels = await db.get_all_channels()
    for ch in channels:
        if ch['channel_username'].lower() == username.lower():
            await state.finish()
            await message.answer(
                f"⚠️ <b>@{username}</b> allaqachon qo'shilgan!",
                reply_markup=error_kb
            )
            return

    await db.add_channel(
        channel_name=result['channel_name'],
        channel_username=username
    )

    await state.finish()

    # Muvaffaqiyat tugmalari
    success_kb = InlineKeyboardMarkup(row_width=1)
    success_kb.add(
        InlineKeyboardButton("➕ Yana kanal qo'shish", callback_data="channel:add"),
        InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="channel:list"),
        InlineKeyboardButton("🔙 Admin panelga", callback_data="admin:back")
    )

    await message.answer(
        f"✅ <b>Kanal qo'shildi!</b>\n\n"
        f"📢 Nomi: {result['channel_name']}\n"
        f"🔗 Username: @{username}",
        reply_markup=success_kb
    )


@dp.callback_query_handler(text="channel:list", state='*')
async def callback_channel_list(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    channels = await db.get_all_channels()

    if not channels:
        await callback.message.edit_text(
            "📢 <b>Kanallar ro'yxati</b>\n\n"
            "Hozircha kanallar yo'q.",
            reply_markup=get_channels_menu()
        )
        await callback.answer()
        return

    text = "📢 <b>Kanallar ro'yxati</b>\n\n"

    await callback.message.edit_text(text, reply_markup=get_channel_list_keyboard(channels))
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("channel:view:"), state='*')
async def callback_view_channel(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    channel_id = int(callback.data.split(":")[2])
    channel = await db.get_channel(channel_id)

    if not channel:
        await callback.answer("Kanal topilmadi!", show_alert=True)
        return

    text = (
        f"📢 <b>{channel['channel_name']}</b>\n\n"
        f"🔗 Username: @{channel['channel_username']}\n"
        f"📅 Qo'shilgan: {channel['added_at'].strftime('%d.%m.%Y')}"
    )

    await callback.message.edit_text(text, reply_markup=get_channel_actions(channel_id))
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("channel:delete:") and "confirm" not in c.data, state='*')
async def callback_delete_channel(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    channel_id = int(callback.data.split(":")[2])
    channel = await db.get_channel(channel_id)

    if not channel:
        await callback.answer("Kanal topilmadi!", show_alert=True)
        return

    await callback.message.edit_text(
        f"🗑 <b>Kanalni o'chirish</b>\n\n"
        f"📢 <b>{channel['channel_name']}</b>\n"
        f"🔗 @{channel['channel_username']}\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_channel_delete_confirm(channel_id)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("channel:delete_confirm:"), state='*')
async def callback_delete_channel_confirm(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    channel_id = int(callback.data.split(":")[2])
    channel = await db.get_channel(channel_id)

    if not channel:
        await callback.answer("Kanal topilmadi!", show_alert=True)
        return

    await db.remove_channel(channel_id)

    # O'chirilgandan keyin tugmalar
    deleted_kb = InlineKeyboardMarkup(row_width=1)
    deleted_kb.add(
        InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="channel:list"),
        InlineKeyboardButton("🔙 Admin panelga", callback_data="admin:back")
    )

    await callback.message.edit_text(
        f"✅ <b>{channel['channel_name']}</b> o'chirildi!",
        reply_markup=deleted_kb
    )
    await callback.answer("O'chirildi!")