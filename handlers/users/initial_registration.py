from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import datetime

from loader import dp, db, bot
from states.states import InitialRegistrationState
from keyboards.inline.buttons import get_cancel_keyboard, get_send_request_keyboard
from utils.subscription import check_and_request_subscription


@dp.callback_query_handler(text="initial:start", state='*')
async def start_initial_registration(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await check_and_request_subscription(bot, db, callback.message):
        await callback.answer()
        return

    # Boshlang'ich savollarni olish
    questions = await db.get_active_initial_questions()

    # ✅ Record'larni dict'ga aylantirish
    questions_list = [dict(q) for q in questions] if questions else []

    await state.update_data(
        questions=questions_list,  # ✅ TO'G'RI
        current_question=0,
        answers={}
    )

    await callback.message.edit_text(
        "📝 <b>Ma'lumotlaringizni to'ldiring</b>\n\n"
        "Ismingizni kiriting:",
        reply_markup=get_cancel_keyboard("initial:cancel")
    )

    await InitialRegistrationState.first_name.set()
    await callback.answer()


@dp.callback_query_handler(text="initial:cancel", state='*')
async def cancel_initial_registration(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text(
        "❌ Bekor qilindi.\n\n"
        "/start - Qaytadan boshlash"
    )
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())

    await message.answer(
        "📝 Familiyangizni kiriting:",
        reply_markup=get_cancel_keyboard("initial:cancel")
    )

    await InitialRegistrationState.last_name.set()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())

    await message.answer(
        "📅 Tug'ilgan sanangizni kiriting:\n\n"
        "<i>Format: KK.OO.YYYY (masalan: 01.01.2000)</i>",
        reply_markup=get_cancel_keyboard("initial:cancel")
    )

    await InitialRegistrationState.birth_date.set()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    try:
        birth_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        await state.update_data(birth_date=birth_date)

        await message.answer(
            "📍 Yashash manzilingizni kiriting:\n\n"
            "<i>(Masalan: Toshkent shahar, Chilonzor tumani)</i>",
            reply_markup=get_cancel_keyboard("initial:cancel")
        )

        await InitialRegistrationState.address.set()

    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Iltimos, to'g'ri formatda kiriting: KK.OO.YYYY\n"
            "Masalan: 01.01.2000"
        )


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())

    # Qo'shimcha savollar bormi tekshirish
    data = await state.get_data()
    questions = data.get('questions', [])

    if questions:
        # Qo'shimcha savollar bor
        await send_additional_question(message, state)
    else:
        # Qo'shimcha savollar yo'q, tasdiqni ko'rsatish
        await show_confirmation(message, state)


async def send_additional_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions']
    current_idx = data.get('current_question', 0)

    if current_idx >= len(questions):
        # Barcha savollarga javob berildi
        await show_confirmation(message, state)
        return

    question = questions[current_idx]

    question_num = current_idx + 1
    total = len(questions)

    text = (
        f"❓ Qo'shimcha savol {question_num}/{total}:\n\n"
        f"<b>{question['question_text']}</b>"
    )

    if question['field_type'] == 'text':
        await message.answer(text, reply_markup=get_cancel_keyboard("initial:cancel"))
        await InitialRegistrationState.additional_text.set()

    elif question['field_type'] == 'choice':
        from keyboards.inline.buttons import get_additional_options_keyboard
        keyboard = get_additional_options_keyboard(question['options'], current_idx)
        await message.answer(text, reply_markup=keyboard)
        await InitialRegistrationState.additional_choice.set()

    elif question['field_type'] == 'photo':
        await message.answer(
            text + "\n\n📷 Rasm yuboring:",
            reply_markup=get_cancel_keyboard("initial:cancel")
        )
        await InitialRegistrationState.additional_photo.set()

    elif question['field_type'] == 'location':
        await message.answer(
            text + "\n\n📍 Lokatsiyani yuboring:",
            reply_markup=get_cancel_keyboard("initial:cancel")
        )
        await InitialRegistrationState.additional_location.set()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.additional_text,
                    content_types=types.ContentTypes.TEXT)
async def process_additional_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions']
    current_idx = data['current_question']
    answers = data.get('answers', {})

    question = questions[current_idx]
    answers[question['id']] = {
        'question_text': question['question_text'],
        'answer': message.text,
        'type': 'text'
    }

    await state.update_data(
        answers=answers,
        current_question=current_idx + 1
    )

    await send_additional_question(message, state)


@dp.callback_query_handler(lambda c: c.data.startswith("additional:"), state=InitialRegistrationState.additional_choice)
async def process_additional_choice(callback: types.CallbackQuery, state: FSMContext):
    _, question_idx, option_idx = callback.data.split(":")
    question_idx = int(question_idx)
    option_idx = int(option_idx)

    data = await state.get_data()
    questions = data['questions']
    answers = data.get('answers', {})

    question = questions[question_idx]
    answer = question['options'][option_idx]

    answers[question['id']] = {
        'question_text': question['question_text'],
        'answer': answer,
        'type': 'choice'
    }

    await state.update_data(
        answers=answers,
        current_question=question_idx + 1
    )

    await send_additional_question(callback.message, state)
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.additional_photo,
                    content_types=types.ContentTypes.PHOTO)
async def process_additional_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions']
    current_idx = data['current_question']
    answers = data.get('answers', {})

    question = questions[current_idx]
    photo_id = message.photo[-1].file_id

    answers[question['id']] = {
        'question_text': question['question_text'],
        'answer': photo_id,
        'type': 'photo'
    }

    await state.update_data(
        answers=answers,
        current_question=current_idx + 1
    )

    await send_additional_question(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=InitialRegistrationState.additional_location,
                    content_types=types.ContentTypes.LOCATION)
async def process_additional_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions']
    current_idx = data['current_question']
    answers = data.get('answers', {})

    question = questions[current_idx]
    location = {
        'latitude': message.location.latitude,
        'longitude': message.location.longitude
    }

    answers[question['id']] = {
        'question_text': question['question_text'],
        'answer': location,
        'type': 'location'
    }

    await state.update_data(
        answers=answers,
        current_question=current_idx + 1
    )

    await send_additional_question(message, state)


async def show_confirmation(message: types.Message, state: FSMContext):
    data = await state.get_data()

    text = "✅ <b>Ma'lumotlaringizni tekshiring:</b>\n\n"
    text += f"👤 Ism: <b>{data['first_name']}</b>\n"
    text += f"👤 Familiya: <b>{data['last_name']}</b>\n"
    text += f"📅 Tug'ilgan sana: <b>{data['birth_date'].strftime('%d.%m.%Y')}</b>\n"
    text += f"📍 Manzil: <b>{data['address']}</b>\n"

    questions = data.get('questions', [])
    answers = data.get('answers', {})

    if answers:
        text += "\n<b>Qo'shimcha ma'lumotlar:</b>\n"
        for q_id, ans in answers.items():
            if ans['type'] == 'text' or ans['type'] == 'choice':
                text += f"• {ans['question_text']}: <b>{ans['answer']}</b>\n"
            elif ans['type'] == 'photo':
                text += f"• {ans['question_text']}: 📷 Rasm\n"
            elif ans['type'] == 'location':
                loc = ans['answer']
                text += f"• {ans['question_text']}: 📍 Lokatsiya\n"

    text += "\n❓ Admin tasdiqlashi uchun so'rov yuborasizmi?"

    await message.answer(text, reply_markup=get_send_request_keyboard())
    await InitialRegistrationState.confirm.set()


@dp.callback_query_handler(text="initial:send_request", state=InitialRegistrationState.confirm)
async def send_approval_request(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Profilni saqlash
    profile = await db.add_user_profile(
        telegram_id=callback.from_user.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        birth_date=data['birth_date'],
        address=data['address']
    )

    # ✅ Profile'ni dict'ga aylantirish
    profile_dict = dict(profile)

    # Qo'shimcha javoblarni saqlash
    answers = data.get('answers', {})
    for q_id, ans in answers.items():
        await db.add_initial_response(
            profile_id=profile_dict['id'],
            question_id=q_id,
            answer=ans['answer'],
            answer_type=ans['type']
        )

    # Adminlarga xabar yuborish
    admins = await db.get_all_admins()

    for admin in admins:
        try:
            await send_approval_notification(admin['telegram_id'], profile_dict, data)
        except:
            pass

    await callback.message.edit_text(
        "✅ <b>So'rovingiz yuborildi!</b>\n\n"
        "Admin tasdiqlashini kuting.\n"
        "Natija haqida xabar olasiz."
    )

    await state.finish()
    await callback.answer()


async def send_approval_notification(admin_id: int, profile: dict, data: dict):
    from keyboards.inline.buttons import get_approval_keyboard

    text = "🔔 <b>Yangi so'rov!</b>\n\n"
    text += f"👤 Ism: <b>{profile['first_name']}</b>\n"
    text += f"👤 Familiya: <b>{profile['last_name']}</b>\n"
    text += f"📅 Tug'ilgan sana: <b>{profile['birth_date'].strftime('%d.%m.%Y')}</b>\n"
    text += f"📍 Manzil: <b>{profile['address']}</b>\n"
    text += f"🆔 User ID: <code>{profile['telegram_id']}</code>\n"

    answers = data.get('answers', {})
    if answers:
        text += "\n<b>Qo'shimcha ma'lumotlar:</b>\n"
        for q_id, ans in answers.items():
            if ans['type'] == 'text' or ans['type'] == 'choice':
                text += f"• {ans['question_text']}: <b>{ans['answer']}</b>\n"
            elif ans['type'] == 'photo':
                text += f"• {ans['question_text']}: 📷 (pastda)\n"
            elif ans['type'] == 'location':
                loc = ans['answer']
                link = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
                text += f"• {ans['question_text']}: <a href='{link}'>📍 Xaritada ko'rish</a>\n"

    # Rasmlarni yuborish
    has_photos = any(ans['type'] == 'photo' for ans in answers.values())

    if has_photos:
        from aiogram.types import MediaGroup, InputMediaPhoto

        media = MediaGroup()
        for ans in answers.values():
            if ans['type'] == 'photo':
                media.attach_photo(ans['answer'], caption=ans['question_text'])

        await bot.send_media_group(admin_id, media)

    await bot.send_message(
        admin_id,
        text,
        reply_markup=get_approval_keyboard(profile['id']),
        disable_web_page_preview=False
    )


@dp.callback_query_handler(text="initial:edit", state=InitialRegistrationState.confirm)
async def edit_initial_data(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Ma'lumotlaringizni qayta to'ldiring</b>\n\n"
        "Ismingizni kiriting:",
        reply_markup=get_cancel_keyboard("initial:cancel")
    )

    await InitialRegistrationState.first_name.set()
    await callback.answer()