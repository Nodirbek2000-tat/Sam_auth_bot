from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db
from states.states import InitialQuestionsState
from keyboards.inline.buttons import (
    get_initial_questions_menu,
    get_initial_question_list_keyboard,
    get_initial_question_type_keyboard,
    get_add_more_options_keyboard,
    get_initial_question_actions,
    get_initial_question_delete_confirm,
    get_initial_question_toggle_keyboard
)
from handlers.users.admin_panel import is_admin


@dp.callback_query_handler(text="admin:initial_questions", state='*')
async def callback_initial_questions_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    questions = await db.get_all_initial_questions()
    active_count = sum(1 for q in questions if q['is_active'])

    text = (
        "❓ <b>KIRISH SAVOLLARI</b>\n\n"
        f"📊 Jami: <b>{len(questions)}</b> ta\n"
        f"✅ Aktiv: <b>{active_count}</b> ta\n\n"
        "Bu savollar foydalanuvchi /start bosganida so'raladi."
    )

    await callback.message.edit_text(text, reply_markup=get_initial_questions_menu())
    await callback.answer()


@dp.callback_query_handler(text="initial_q:add", state='*')
async def callback_add_initial_question(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    await callback.message.edit_text(
        "❓ <b>Yangi savol qo'shish</b>\n\n"
        "Savol matnini kiriting:\n"
        "<i>(Masalan: Telefon raqamingiz nechchi?)</i>"
    )

    await state.update_data(options=[])
    await InitialQuestionsState.question_text.set()
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialQuestionsState.question_text)
async def process_question_text(message: types.Message, state: FSMContext):
    await state.update_data(question_text=message.text.strip())

    await message.answer(
        f"✅ Savol: <b>{message.text}</b>\n\n"
        "Endi savol turini tanlang:",
        reply_markup=get_initial_question_type_keyboard()
    )

    await InitialQuestionsState.field_type.set()


@dp.callback_query_handler(text="initial_q_type:text", state=InitialQuestionsState.field_type)
async def process_type_text(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    question = await db.add_initial_question(
        question_text=data['question_text'],
        field_type='text',
        options=None,
        is_active=True
    )

    await state.finish()

    await callback.message.edit_text(
        f"✅ <b>Savol qo'shildi!</b>\n\n"
        f"❓ {data['question_text']}\n"
        f"📋 Tur: Matn\n\n"
        "/admin - Admin panel"
    )
    await callback.answer()


@dp.callback_query_handler(text="initial_q_type:choice", state=InitialQuestionsState.field_type)
async def process_type_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📋 <b>Variantli savol</b>\n\n"
        "1-variantni kiriting:"
    )

    await InitialQuestionsState.add_option.set()
    await callback.answer()


@dp.callback_query_handler(text="initial_q_type:photo", state=InitialQuestionsState.field_type)
async def process_type_photo(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    question = await db.add_initial_question(
        question_text=data['question_text'],
        field_type='photo',
        options=None,
        is_active=True
    )

    await state.finish()

    await callback.message.edit_text(
        f"✅ <b>Savol qo'shildi!</b>\n\n"
        f"❓ {data['question_text']}\n"
        f"📋 Tur: Rasm\n\n"
        "/admin - Admin panel"
    )
    await callback.answer()


@dp.callback_query_handler(text="initial_q_type:location", state=InitialQuestionsState.field_type)
async def process_type_location(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    question = await db.add_initial_question(
        question_text=data['question_text'],
        field_type='location',
        options=None,
        is_active=True
    )

    await state.finish()

    await callback.message.edit_text(
        f"✅ <b>Savol qo'shildi!</b>\n\n"
        f"❓ {data['question_text']}\n"
        f"📋 Tur: Lokatsiya\n\n"
        "/admin - Admin panel"
    )
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialQuestionsState.add_option)
async def process_add_option(message: types.Message, state: FSMContext):
    data = await state.get_data()
    options = data.get('options', [])
    options.append(message.text.strip())

    await state.update_data(options=options)

    text = f"✅ <b>Variant qo'shildi!</b>\n\n"
    text += f"📋 <b>Variantlar:</b>\n"
    for i, opt in enumerate(options, 1):
        text += f"{i}. {opt}\n"

    text += f"\nYana variant qo'shasizmi?"

    await message.answer(text, reply_markup=get_add_more_options_keyboard())


@dp.callback_query_handler(text="initial_option:add_more", state=InitialQuestionsState.add_option)
async def callback_add_more_option(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get('options', [])

    await callback.message.edit_text(
        f"📋 <b>Variantlar:</b> {len(options)} ta\n\n"
        f"{len(options) + 1}-variantni kiriting:"
    )
    await callback.answer()


@dp.callback_query_handler(text="initial_option:finish", state=InitialQuestionsState.add_option)
async def callback_finish_options(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get('options', [])

    if not options:
        await callback.answer("Kamida 1 ta variant qo'shing!", show_alert=True)
        return

    question = await db.add_initial_question(
        question_text=data['question_text'],
        field_type='choice',
        options=options,
        is_active=True
    )

    await state.finish()

    text = f"✅ <b>Savol qo'shildi!</b>\n\n"
    text += f"❓ {data['question_text']}\n"
    text += f"📋 Tur: Variantlar\n"
    text += f"🔘 Variantlar: {len(options)} ta\n\n"
    text += "/admin - Admin panel"

    await callback.message.edit_text(text)
    await callback.answer()


@dp.callback_query_handler(text="initial_q:list", state='*')
async def callback_initial_questions_list(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    questions = await db.get_all_initial_questions()

    if not questions:
        try:
            await callback.message.edit_text(
                "❓ <b>Kirish savollari ro'yxati</b>\n\n"
                "Hozircha savollar yo'q.",
                reply_markup=get_initial_questions_menu()
            )
        except Exception:
            pass  # Agar xabar bir xil bo'lsa, xatoni e'tiborsiz qoldiramiz

        await callback.answer()
        return

    text = "❓ <b>Kirish savollari ro'yxati</b>\n\n"
    text += "✅ - Aktiv | ⏸ - Noaktiv\n\n"

    try:
        await callback.message.edit_text(text, reply_markup=get_initial_question_list_keyboard(questions))
    except Exception:
        pass

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("initial_q:view:"), state='*')
async def callback_view_initial_question(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    question_id = int(callback.data.split(":")[2])
    question = await db.get_initial_question(question_id)

    if not question:
        await callback.answer("Savol topilmadi!", show_alert=True)
        return

    status = "✅ Aktiv" if question['is_active'] else "⏸ Noaktiv"

    field_types = {
        'text': '📝 Matn',
        'choice': '🔘 Variantlar',
        'photo': '📷 Rasm',
        'location': '📍 Lokatsiya'
    }

    unknown = "Noma'lum"

    text = (
        f"❓ <b>Savol ma'lumotlari</b>\n\n"
        f"📋 Savol: <b>{question['question_text']}</b>\n"
        f"📊 Tur: {field_types.get(question['field_type'], unknown)}\n"
        f"📊 Status: {status}\n"
    )

    if question['field_type'] == 'choice' and question['options']:
        text += f"\n<b>Variantlar ({len(question['options'])} ta):</b>\n"
        for i, opt in enumerate(question['options'], 1):
            text += f"{i}. {opt}\n"

    await callback.message.edit_text(text,
                                     reply_markup=get_initial_question_actions(question_id, question['is_active']))
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("initial_q:toggle:"), state='*')
async def callback_toggle_initial_question(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    question_id = int(callback.data.split(":")[2])
    question = await db.get_initial_question(question_id)

    if not question:
        await callback.answer("Savol topilmadi!", show_alert=True)
        return

    new_status = not question['is_active']
    await db.toggle_initial_question(question_id, new_status)

    question = await db.get_initial_question(question_id)
    status = "✅ Aktiv" if question['is_active'] else "⏸ Noaktiv"

    field_types = {
        'text': '📝 Matn',
        'choice': '🔘 Variantlar',
        'photo': '📷 Rasm',
        'location': '📍 Lokatsiya'
    }

    unknown = "Noma'lum"

    text = (
        f"❓ <b>Savol ma'lumotlari</b>\n\n"
        f"📋 Savol: <b>{question['question_text']}</b>\n"
        f"📊 Tur: {field_types.get(question['field_type'], unknown)}\n"
        f"📊 Status: {status}\n"
    )

    if question['field_type'] == 'choice' and question['options']:
        text += f"\n<b>Variantlar ({len(question['options'])} ta):</b>\n"
        for i, opt in enumerate(question['options'], 1):
            text += f"{i}. {opt}\n"

    await callback.message.edit_text(text,
                                     reply_markup=get_initial_question_actions(question_id, question['is_active']))

    status_text = "aktiv" if new_status else "noaktiv"
    await callback.answer(f"Savol {status_text} qilindi!")


@dp.callback_query_handler(lambda c: c.data.startswith("initial_q:delete:") and "confirm" not in c.data, state='*')
async def callback_delete_initial_question(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    question_id = int(callback.data.split(":")[2])
    question = await db.get_initial_question(question_id)

    if not question:
        await callback.answer("Savol topilmadi!", show_alert=True)
        return

    await callback.message.edit_text(
        f"🗑 <b>Savolni o'chirish</b>\n\n"
        f"❓ <b>{question['question_text']}</b>\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_initial_question_delete_confirm(question_id)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("initial_q:delete_confirm:"), state='*')
async def callback_delete_initial_question_confirm(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    question_id = int(callback.data.split(":")[2])
    question = await db.get_initial_question(question_id)

    if not question:
        await callback.answer("Savol topilmadi!", show_alert=True)
        return

    await db.delete_initial_question(question_id)

    await callback.message.edit_text(f"✅ Savol o'chirildi!")
    await callback.answer("O'chirildi!")