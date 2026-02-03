from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MediaGroup

from loader import dp, db, bot
from states.states import BroadcastStates


# Admin check function
async def is_admin(user_id: int) -> bool:
    return await db.is_admin(user_id)


# /reklama buyrug'i - faqat adminlar uchun (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['reklama'])
async def start_broadcast(message: types.Message):
    # Admin check
    if not await is_admin(message.from_user.id):
        return

    await message.answer(
        "📢 <b>Reklama yuborish</b>\n\n"
        "Reklama matnini yuboring yoki /skip buyrug'ini yuboring:",
        parse_mode="HTML"
    )
    await BroadcastStates.waiting_for_text.set()


# Matnni qabul qilish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_text, content_types=types.ContentTypes.TEXT)
async def get_broadcast_text(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    if message.text == "/skip":
        await state.update_data(text=None)
    else:
        await state.update_data(text=message.text)

    await message.answer(
        "📁 <b>Fayllarni yuboring</b>\n\n"
        "Bir nechta fayl yuborishingiz mumkin.\n"
        "Tugallash uchun /done yoki tashlab ketish uchun /skip yuboring:",
        parse_mode="HTML"
    )
    await state.update_data(files=[])
    await BroadcastStates.waiting_for_files.set()


# Fayllarni qabul qilish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_files, content_types=types.ContentTypes.DOCUMENT)
async def get_broadcast_files(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    data = await state.get_data()
    files = data.get('files', [])
    files.append(message.document.file_id)
    await state.update_data(files=files)

    await message.answer(
        f"✅ Fayl qo'shildi! Jami: {len(files)}\n\n"
        "Yana fayl yuboring yoki /done tugmasini bosing.",
        parse_mode="HTML"
    )


# Fayllarni tugatish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_files, commands=['done', 'skip'])
async def finish_files(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    if message.text == "/skip":
        await state.update_data(files=[])

    await message.answer(
        "🖼 <b>Rasmlarni yuboring</b>\n\n"
        "Bir nechta rasm yuborishingiz mumkin.\n"
        "Tugallash uchun /done yoki tashlab ketish uchun /skip yuboring:",
        parse_mode="HTML"
    )
    await state.update_data(images=[])
    await BroadcastStates.waiting_for_images.set()


# Rasmlarni qabul qilish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_images, content_types=types.ContentTypes.PHOTO)
async def get_broadcast_images(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    data = await state.get_data()
    images = data.get('images', [])
    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)

    await message.answer(
        f"✅ Rasm qo'shildi! Jami: {len(images)}\n\n"
        "Yana rasm yuboring yoki /done tugmasini bosing.",
        parse_mode="HTML"
    )


# Rasmlarni tugatish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_images, commands=['done', 'skip'])
async def finish_images(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    if message.text == "/skip":
        await state.update_data(images=[])

    await message.answer(
        "🔗 <b>Link yuboring</b>\n\n"
        "Tugma uchun linkni yuboring yoki /skip yuboring:",
        parse_mode="HTML"
    )
    await BroadcastStates.waiting_for_link.set()


# Linkni qabul qilish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_link, content_types=types.ContentTypes.TEXT)
async def get_broadcast_link(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    if message.text == "/skip":
        await state.update_data(link=None, link_name=None)
        await show_preview(message, state)
    else:
        await state.update_data(link=message.text)
        await message.answer(
            "✏️ <b>Link nomini yuboring:</b>",
            parse_mode="HTML"
        )
        await BroadcastStates.waiting_for_link_name.set()


# Link nomini qabul qilish (FAQAT LICHKADA)
@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=BroadcastStates.waiting_for_link_name, content_types=types.ContentTypes.TEXT)
async def get_broadcast_link_name(message: types.Message, state: FSMContext):
    # Admin check
    if not await is_admin(message.from_user.id):
        await state.finish()
        return

    await state.update_data(link_name=message.text)
    await show_preview(message, state)


# Preview ko'rsatish
async def show_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = data.get('text')
    files = data.get('files', [])
    images = data.get('images', [])
    link = data.get('link')
    link_name = data.get('link_name')

    # Preview matni
    preview_text = "📢 <b>Reklama ko'rinishi:</b>\n\n"
    if text:
        preview_text += f"{text}\n\n"

    preview_text += f"📁 Fayllar: {len(files)}\n"
    preview_text += f"🖼 Rasmlar: {len(images)}\n"

    if link:
        preview_text += f"🔗 Link: {link}\n"
        preview_text += f"✏️ Link nomi: {link_name}\n"

    # Tugmalar
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Yuborish", callback_data="broadcast_send"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="broadcast_cancel")
    )

    await message.answer(preview_text, reply_markup=keyboard, parse_mode="HTML")
    await BroadcastStates.confirm.set()


# Yuborishni tasdiqlash
@dp.callback_query_handler(text="broadcast_send", state=BroadcastStates.confirm)
async def confirm_broadcast(call: types.CallbackQuery, state: FSMContext):
    # Admin check
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Siz admin emassiz!")
        await state.finish()
        return

    await call.answer()
    await call.message.edit_text("⏳ Reklama yuborilmoqda...")

    data = await state.get_data()
    text = data.get('text')
    files = data.get('files', [])
    images = data.get('images', [])
    link = data.get('link')
    link_name = data.get('link_name')

    # Barcha userlarni olish
    users = await db.get_all_users()

    success = 0
    failed = 0

    # Inline tugma (agar link bo'lsa)
    keyboard = None
    if link and link_name:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(link_name, url=link))

    for user in users:
        try:
            user_id = user['telegram_id']

            # Rasmlarni yuborish
            if images:
                if len(images) == 1:
                    await bot.send_photo(user_id, images[0], caption=text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    media = MediaGroup()
                    for idx, img in enumerate(images):
                        if idx == 0 and text:
                            media.attach_photo(img, caption=text)
                        else:
                            media.attach_photo(img)
                    await bot.send_media_group(user_id, media)
                    if keyboard:
                        await bot.send_message(user_id, "👇 Havola:", reply_markup=keyboard)

            # Fayllarni yuborish
            elif files:
                for file_id in files:
                    await bot.send_document(user_id, file_id, caption=text if text else None, reply_markup=keyboard,
                                            parse_mode="HTML")

            # Faqat matn
            elif text:
                await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")

            success += 1
        except Exception as e:
            failed += 1
            print(f"Xato: {user_id} - {e}")

    await call.message.edit_text(
        f"✅ <b>Reklama yuborildi!</b>\n\n"
        f"Muvaffaqiyatli: {success}\n"
        f"Xato: {failed}",
        parse_mode="HTML"
    )

    await state.finish()


# Bekor qilish
@dp.callback_query_handler(text="broadcast_cancel", state="*")
async def cancel_broadcast(call: types.CallbackQuery, state: FSMContext):
    # Admin check
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Siz admin emassiz!")
        await state.finish()
        return

    await call.answer("❌ Bekor qilindi")
    await state.finish()
    await call.message.edit_text("❌ Reklama yuborish bekor qilindi.")