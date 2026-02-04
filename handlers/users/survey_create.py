from aiogram import types
from aiogram.dispatcher import FSMContext
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
import os
import tempfile

from loader import dp, db
from states.states import SurveyCreateState
from keyboards.inline.buttons import (
    get_surveys_menu, get_field_type_keyboard,
    get_add_more_fields_keyboard, get_add_option_keyboard,
    get_survey_confirm_keyboard
)
from handlers.users.admin_panel import is_admin


@dp.callback_query_handler(text="admin:surveys", state='*')
async def callback_surveys_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    surveys_count = await db.count_surveys()
    active = await db.get_active_survey()
    active_name = active['name'] if active else "Yo'q"

    text = (
        "📋 <b>SO'ROVNOMALAR</b>\n\n"
        f"📊 Jami: <b>{surveys_count}</b> ta\n"
        f"✅ Aktiv: <b>{active_name}</b>"
    )

    await callback.message.edit_text(text, reply_markup=get_surveys_menu())
    await callback.answer()


@dp.callback_query_handler(text="survey:create", state='*')
async def callback_create_survey(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    await callback.message.edit_text(
        "📝 <b>Yangi so'rovnoma yaratish</b>\n\n"
        "So'rovnoma nomini kiriting:\n"
        "<i>(Masalan: Yoshlar anketa 2024)</i>"
    )

    await SurveyCreateState.name.set()
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=SurveyCreateState.name)
async def process_survey_name(message: types.Message, state: FSMContext):
    await state.update_data(
        survey_name=message.text,
        fields=[],
        current_field={},
        current_options=[]
    )

    await message.answer(
        "✅ So'rovnoma nomi: <b>" + message.text + "</b>\n\n"
                                                  "Endi ustunlarni qo'shamiz.\n\n"
                                                  "📌 <b>1-ustun nomini kiriting:</b>\n"
                                                  "<i>(Masalan: F.I.Sh)</i>"
    )

    await SurveyCreateState.column_name.set()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=SurveyCreateState.column_name)
async def process_column_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field_num = len(data.get('fields', [])) + 1

    await state.update_data(
        current_field={'column_name': message.text}
    )

    await message.answer(
        f"📌 <b>{field_num}-ustun:</b> {message.text}\n\n"
        f"Savol matnini kiriting:\n"
        f"<i>(Masalan: Familiya, ism, sharifingizni kiriting)</i>"
    )

    await SurveyCreateState.question_text.set()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=SurveyCreateState.question_text)
async def process_question_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_field = data.get('current_field', {})
    current_field['question_text'] = message.text

    await state.update_data(current_field=current_field)

    await message.answer(
        f"📌 <b>Ustun:</b> {current_field['column_name']}\n"
        f"❓ <b>Savol:</b> {message.text}\n\n"
        "Maydon turini tanlang:",
        reply_markup=get_field_type_keyboard()
    )

    await SurveyCreateState.field_type.set()


@dp.callback_query_handler(text="field_type:text", state=SurveyCreateState.field_type)
async def process_field_type_text(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_field = data.get('current_field', {})
    current_field['field_type'] = 'text'
    current_field['options'] = None

    fields = data.get('fields', [])
    fields.append(current_field)

    await state.update_data(
        fields=fields,
        current_field={},
        current_options=[]
    )

    text = "✅ <b>Ustun qo'shildi!</b>\n\n"
    text += "📋 <b>Qo'shilgan ustunlar:</b>\n"

    for i, f in enumerate(fields, 1):
        if f['field_type'] == 'text':
            field_type = "📝 Matn"
        elif f['field_type'] == 'choice':
            field_type = "🔘 Variantlar"
        elif f['field_type'] == 'photo':
            field_type = "📷 Rasm"
        elif f['field_type'] == 'location':
            field_type = "📍 Lokatsiya"
        else:
            field_type = "❓ Noma'lum"

        text += f"{i}. {f['column_name']} ({field_type})\n"

    text += "\nYana ustun qo'shasizmi?"

    await callback.message.edit_text(text, reply_markup=get_add_more_fields_keyboard())
    await callback.answer()


@dp.callback_query_handler(text="field_type:choice", state=SurveyCreateState.field_type)
async def process_field_type_choice(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_field = data.get('current_field', {})
    current_field['field_type'] = 'choice'

    await state.update_data(
        current_field=current_field,
        current_options=[]
    )

    await callback.message.edit_text(
        f"📌 <b>Ustun:</b> {current_field['column_name']}\n"
        f"❓ <b>Savol:</b> {current_field['question_text']}\n"
        f"📋 <b>Tur:</b> Variantlar\n\n"
        "1-variantni kiriting:"
    )

    await SurveyCreateState.add_option.set()
    await callback.answer()


@dp.callback_query_handler(text="field_type:photo", state=SurveyCreateState.field_type)
async def process_field_type_photo(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_field = data.get('current_field', {})
    current_field['field_type'] = 'photo'
    current_field['options'] = None

    fields = data.get('fields', [])
    fields.append(current_field)

    await state.update_data(
        fields=fields,
        current_field={},
        current_options=[]
    )

    text = "✅ <b>Ustun qo'shildi!</b>\n\n"
    text += "📋 <b>Qo'shilgan ustunlar:</b>\n"

    for i, f in enumerate(fields, 1):
        if f['field_type'] == 'text':
            field_type = "📝 Matn"
        elif f['field_type'] == 'choice':
            field_type = "🔘 Variantlar"
        elif f['field_type'] == 'photo':
            field_type = "📷 Rasm"
        elif f['field_type'] == 'location':
            field_type = "📍 Lokatsiya"
        else:
            field_type = "❓ Noma'lum"

        text += f"{i}. {f['column_name']} ({field_type})\n"

    text += "\nYana ustun qo'shasizmi?"

    await callback.message.edit_text(text, reply_markup=get_add_more_fields_keyboard())
    await callback.answer()


@dp.callback_query_handler(text="field_type:location", state=SurveyCreateState.field_type)
async def process_field_type_location(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_field = data.get('current_field', {})
    current_field['field_type'] = 'location'
    current_field['options'] = None

    fields = data.get('fields', [])
    fields.append(current_field)

    await state.update_data(
        fields=fields,
        current_field={},
        current_options=[]
    )

    text = "✅ <b>Ustun qo'shildi!</b>\n\n"
    text += "📋 <b>Qo'shilgan ustunlar:</b>\n"

    for i, f in enumerate(fields, 1):
        if f['field_type'] == 'text':
            field_type = "📝 Matn"
        elif f['field_type'] == 'choice':
            field_type = "🔘 Variantlar"
        elif f['field_type'] == 'photo':
            field_type = "📷 Rasm"
        elif f['field_type'] == 'location':
            field_type = "📍 Lokatsiya"
        else:
            field_type = "❓ Noma'lum"

        text += f"{i}. {f['column_name']} ({field_type})\n"

    text += "\nYana ustun qo'shasizmi?"

    await callback.message.edit_text(text, reply_markup=get_add_more_fields_keyboard())
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=SurveyCreateState.add_option)
async def process_add_option(message: types.Message, state: FSMContext):
    data = await state.get_data()
    options = data.get('current_options', [])
    options.append(message.text)

    await state.update_data(current_options=options)

    text = f"✅ <b>Variant qo'shildi!</b>\n\n"
    text += f"📋 <b>Variantlar:</b>\n"
    for i, opt in enumerate(options, 1):
        text += f"{i}. {opt}\n"

    text += f"\nYana variant qo'shasizmi?"

    await message.answer(text, reply_markup=get_add_option_keyboard())


@dp.callback_query_handler(text="option:add_more", state=SurveyCreateState.add_option)
async def callback_add_more_option(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get('current_options', [])

    await callback.message.edit_text(
        f"📋 <b>Variantlar:</b> {len(options)} ta\n\n"
        f"{len(options) + 1}-variantni kiriting:"
    )
    await callback.answer()


@dp.callback_query_handler(text="option:finish", state=SurveyCreateState.add_option)
async def callback_finish_options(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_field = data.get('current_field', {})
    options = data.get('current_options', [])

    if not options:
        await callback.answer("Kamida 1 ta variant qo'shing!", show_alert=True)
        return

    current_field['options'] = options

    fields = data.get('fields', [])
    fields.append(current_field)

    await state.update_data(
        fields=fields,
        current_field={},
        current_options=[]
    )

    text = "✅ <b>Ustun qo'shildi!</b>\n\n"
    text += "📋 <b>Qo'shilgan ustunlar:</b>\n"
    for i, f in enumerate(fields, 1):
        if f['field_type'] == 'text':
            text += f"{i}. {f['column_name']} (📝 Matn)\n"
        elif f['field_type'] == 'choice':
            text += f"{i}. {f['column_name']} (🔘 {len(f['options'])} variant)\n"
        elif f['field_type'] == 'photo':
            text += f"{i}. {f['column_name']} (📷 Rasm)\n"
        elif f['field_type'] == 'location':
            text += f"{i}. {f['column_name']} (📍 Lokatsiya)\n"

    text += "\nYana ustun qo'shasizmi?"

    await callback.message.edit_text(text, reply_markup=get_add_more_fields_keyboard())
    await SurveyCreateState.field_type.set()
    await callback.answer()


@dp.callback_query_handler(text="field:add_more", state='*')
async def callback_add_more_field(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fields = data.get('fields', [])

    await callback.message.edit_text(
        f"📋 <b>Ustunlar soni:</b> {len(fields)} ta\n\n"
        f"📌 <b>{len(fields) + 1}-ustun nomini kiriting:</b>"
    )

    await SurveyCreateState.column_name.set()
    await callback.answer()


@dp.callback_query_handler(text="field:finish", state='*')
async def callback_finish_fields(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fields = data.get('fields', [])

    if not fields:
        await callback.answer("Kamida 1 ta ustun qo'shing!", show_alert=True)
        return

    await callback.message.edit_text(
        "📝 <b>So'rovnoma tayyor!</b>\n\n"
        "Excel fayl nomini kiriting:\n"
        "<i>(Masalan: anketa_2024)</i>\n\n"
        "⚠️ .xlsx qo'shiladi avtomatik"
    )

    await SurveyCreateState.file_name.set()
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=SurveyCreateState.file_name)
async def process_file_name(message: types.Message, state: FSMContext):
    file_name = message.text.strip()

    if not file_name.endswith('.xlsx'):
        file_name = file_name + '.xlsx'

    existing = await db.get_survey_by_filename(file_name)
    if existing:
        await message.answer(
            f"⚠️ <b>{file_name}</b> nomli fayl mavjud!\n"
            "Boshqa nom kiriting:"
        )
        return

    await state.update_data(file_name=file_name)

    data = await state.get_data()
    fields = data.get('fields', [])

    wb = Workbook()
    ws = wb.active
    ws.title = "So'rovnoma"

    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    headers = ["№"] + [f['column_name'] for f in fields]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical='center', horizontal='center')
        cell.border = border

        # Ustun kengligini belgilash
        col_letter = cell.column_letter
        ws.column_dimensions[col_letter].width = 20

    file_path = os.path.join(tempfile.gettempdir(), file_name)
    wb.save(file_path)

    with open(file_path, 'rb') as file:
        await message.answer_document(
            file,
            caption=(
                f"📋 <b>So'rovnoma:</b> {data['survey_name']}\n"
                f"📁 <b>Fayl:</b> {file_name}\n"
                f"📊 <b>Ustunlar:</b> {len(fields)} ta\n\n"
                "Tasdiqlaysizmi?"
            ),
            reply_markup=get_survey_confirm_keyboard()
        )

    os.remove(file_path)


@dp.callback_query_handler(text="survey:confirm_create", state=SurveyCreateState.file_name)
async def callback_confirm_create(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    survey = await db.add_survey(
        name=data['survey_name'],
        file_name=data['file_name'],
        created_by=callback.from_user.id
    )

    for i, field in enumerate(data['fields']):
        await db.add_survey_field(
            survey_id=survey['id'],
            field_order=i,
            column_name=field['column_name'],
            question_text=field['question_text'],
            field_type=field['field_type'],
            options=field.get('options')
        )

    await state.finish()

    await callback.message.edit_caption(
        caption=(
            "✅ <b>So'rovnoma muvaffaqiyatli yaratildi!</b>\n\n"
            f"📋 <b>Nomi:</b> {data['survey_name']}\n"
            f"📁 <b>Fayl:</b> {data['file_name']}\n"
            f"📊 <b>Ustunlar:</b> {len(data['fields'])} ta\n\n"
            "So'rovnomani aktiv qilish uchun /admin → So'rovnomalar → Ro'yxat"
        )
    )
    await callback.answer("Saqlandi!")


@dp.callback_query_handler(text="survey:cancel_create", state='*')
async def callback_cancel_create(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    # ✅ Document xabarini o'chirish va yangi xabar yuborish
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "❌ Bekor qilindi.\n\n"
        "/admin - Admin panel"
    )
    await callback.answer()