from aiogram import types
from aiogram.dispatcher import FSMContext
import json
import os
import tempfile
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image
import io

from loader import dp, db, bot
from states.states import RegisterState
from utils.subscription import check_and_request_subscription
from keyboards.inline.buttons import get_options_keyboard, get_confirm_response_keyboard


@dp.callback_query_handler(text="user:register", state='*')
async def start_register(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await check_and_request_subscription(bot, db, callback.message):
        await callback.answer()
        return

    profile = await db.get_user_profile(callback.from_user.id)

    if not profile:
        await callback.message.edit_text(
            "⚠️ Avval ma'lumotlaringizni to'ldiring!\n\n"
            "/start - Boshlash"
        )
        await callback.answer()
        return

    if not profile['is_approved']:
        await callback.message.edit_text(
            "⚠️ Sizning profilingiz hali tasdiqlanmagan!\n\n"
            "Admin tasdiqlashini kuting."
        )
        await callback.answer()
        return

    survey = await db.get_active_survey()

    if not survey:
        await callback.message.edit_text(
            "⚠️ Hozirda aktiv so'rovnoma yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        await callback.answer()
        return

    fields = await db.get_survey_fields(survey['id'])

    if not fields:
        await callback.message.edit_text(
            "⚠️ So'rovnomada savollar yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        await callback.answer()
        return

    await state.update_data(
        survey_id=survey['id'],
        survey_name=survey['name'],
        fields=[dict(f) for f in fields],
        current_field=0,
        answers={}
    )

    await send_question(callback.message, state, edit=True)
    await RegisterState.answering.set()
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['register'], state='*')
async def cmd_register(message: types.Message, state: FSMContext):
    await state.finish()

    if not await check_and_request_subscription(bot, db, message):
        return

    profile = await db.get_user_profile(message.from_user.id)

    if not profile:
        await message.answer(
            "⚠️ Avval ma'lumotlaringizni to'ldiring!\n\n"
            "/start - Boshlash"
        )
        return

    if not profile['is_approved']:
        await message.answer(
            "⚠️ Sizning profilingiz hali tasdiqlanmagan!\n\n"
            "Admin tasdiqlashini kuting."
        )
        return

    survey = await db.get_active_survey()

    if not survey:
        await message.answer(
            "⚠️ Hozirda aktiv so'rovnoma yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        return

    fields = await db.get_survey_fields(survey['id'])

    if not fields:
        await message.answer(
            "⚠️ So'rovnomada savollar yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        return

    await state.update_data(
        survey_id=survey['id'],
        survey_name=survey['name'],
        fields=[dict(f) for f in fields],
        current_field=0,
        answers={}
    )

    await send_question(message, state, edit=False)
    await RegisterState.answering.set()


async def send_question(message: types.Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    fields = data['fields']
    current = data['current_field']

    if current >= len(fields):
        await show_confirmation(message, state, edit)
        return

    field = fields[current]
    question_num = current + 1
    total = len(fields)

    text = (
        f"📋 <b>{data['survey_name']}</b>\n\n"
        f"❓ Savol {question_num}/{total}:\n\n"
        f"<b>{field['question_text']}</b>"
    )

    if field['field_type'] == 'choice' and field['options']:
        keyboard = get_options_keyboard(field['options'], current)
        if edit:
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    elif field['field_type'] == 'photo':
        text += "\n\n📷 Rasm yuboring:"
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)

    elif field['field_type'] == 'location':
        text += "\n\n📍 Lokatsiyani yuboring:"
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
    else:
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)


async def show_confirmation(message: types.Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    fields = data['fields']
    answers = data['answers']

    text = f"📋 <b>{data['survey_name']}</b>\n\n"
    text += "✅ <b>Javoblaringizni tekshiring:</b>\n\n"

    for i, field in enumerate(fields):
        answer = answers.get(str(i))

        if field['field_type'] == 'photo':
            text += f"<b>{field['column_name']}:</b> 📷 Rasm\n"
        elif field['field_type'] == 'location':
            if answer:
                loc = json.loads(answer) if isinstance(answer, str) else answer
                link = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
                text += f"<b>{field['column_name']}:</b> <a href='{link}'>📍 Xaritada ko'rish</a>\n"
            else:
                text += f"<b>{field['column_name']}:</b> —\n"
        else:
            text += f"<b>{field['column_name']}:</b> {answer if answer else '—'}\n"

    text += "\n❓ Tasdiqlaysizmi?"

    if edit:
        await message.edit_text(text, reply_markup=get_confirm_response_keyboard(), disable_web_page_preview=False)
    else:
        await message.answer(text, reply_markup=get_confirm_response_keyboard(), disable_web_page_preview=False)


@dp.callback_query_handler(lambda c: c.data.startswith("answer:"), state=RegisterState.answering)
async def process_choice_answer(callback: types.CallbackQuery, state: FSMContext):
    _, field_order, option_index = callback.data.split(":")
    field_order = int(field_order)
    option_index = int(option_index)

    data = await state.get_data()
    fields = data['fields']

    field = fields[field_order]
    answer = field['options'][option_index]

    answers = data.get('answers', {})
    answers[str(field_order)] = answer

    await state.update_data(
        answers=answers,
        current_field=field_order + 1
    )

    await send_question(callback.message, state, edit=True)
    await callback.answer()


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=RegisterState.answering,
                    content_types=types.ContentTypes.TEXT)
async def process_text_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current = data['current_field']
    fields = data['fields']
    field = fields[current]

    if field['field_type'] != 'text':
        await message.answer("⚠️ Iltimos, to'g'ri formatda javob bering!")
        return

    answers = data.get('answers', {})
    answers[str(current)] = message.text

    await state.update_data(
        answers=answers,
        current_field=current + 1
    )

    await send_question(message, state, edit=False)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=RegisterState.answering,
                    content_types=types.ContentTypes.PHOTO)
async def process_photo_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current = data['current_field']
    fields = data['fields']
    field = fields[current]

    if field['field_type'] != 'photo':
        await message.answer("⚠️ Iltimos, to'g'ri formatda javob bering!")
        return

    answers = data.get('answers', {})
    answers[str(current)] = message.photo[-1].file_id

    await state.update_data(
        answers=answers,
        current_field=current + 1
    )

    await send_question(message, state, edit=False)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=RegisterState.answering,
                    content_types=types.ContentTypes.LOCATION)
async def process_location_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current = data['current_field']
    fields = data['fields']
    field = fields[current]

    if field['field_type'] != 'location':
        await message.answer("⚠️ Iltimos, to'g'ri formatda javob bering!")
        return

    answers = data.get('answers', {})
    location = {
        'latitude': message.location.latitude,
        'longitude': message.location.longitude
    }
    answers[str(current)] = json.dumps(location)

    await state.update_data(
        answers=answers,
        current_field=current + 1
    )

    await send_question(message, state, edit=False)


async def generate_word_document(user_id: int, response_data: dict, fields: list):
    """WORD fayl yaratish - IDEAL VERSION"""

    doc = Document()

    # Sarlavha - QORA RANG
    title = doc.add_heading("MA'LUMOTNOMA", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(12)

    # Ma'lumotlarni olish
    rahbar = 'Suyunboyev Alisher Isakboevich'
    tuman = 'Toyloq tumani'
    mahalla = 'U. mahallasi'
    yosh_fish = ''

    # Jadvaldan Rahbar, Tuman, Mahalla, F.I.Sh topish
    for field in fields:
        column_name = field['column_name']
        answer = response_data.get(column_name, "")

        if column_name == 'Rahbar' and answer:
            rahbar = answer

        if column_name == 'Tuman/Shahar nomi' and answer:
            tuman = answer

        if column_name == 'Mahalla nomi' and answer:
            mahalla = answer

        if column_name == 'Biriktirilgan Vakilning F.I.Sh' and answer:
            yosh_fish = answer

    # Rahbar (comment olingan)
    # p_rahbar = doc.add_paragraph()
    # p_rahbar.add_run("Rahbar: ").bold = True
    # p_rahbar.add_run(rahbar)
    # p_rahbar.paragraph_format.space_after = Pt(8)

    # Hudud - TUMAN, MAHALLA
    p_hudud = doc.add_paragraph()
    p_hudud.add_run("Hudud: ").bold = True
    p_hudud.add_run(f"{tuman}, {mahalla}")
    p_hudud.paragraph_format.space_after = Pt(8)

    # Skip qilinadigan ustunlar
    skip_columns = ['Rahbar', 'Tuman/Shahar nomi', 'Mahalla nomi', 'Biriktirilgan Yoshning F.I.Sh']

    # Dinamik ma'lumotlar
    temp_images = []

    for i, field in enumerate(fields):
        column_name = field['column_name']

        if column_name in skip_columns:
            continue

        answer = response_data.get(column_name, "")

        if field['field_type'] == 'location':
            continue

        # Savol
        p = doc.add_paragraph()
        run = p.add_run(f"{field['column_name']}: ")
        run.bold = True
        p.paragraph_format.space_after = Pt(4)

        # Rasm
        if field['field_type'] == 'photo' and answer:
            try:
                file = await bot.get_file(answer)
                downloaded_file = await bot.download_file(file.file_path)

                img = Image.open(io.BytesIO(downloaded_file.read()))
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)

                temp_path = os.path.join(tempfile.gettempdir(), f"temp_word_img_{i}.png")
                img.save(temp_path, "PNG")
                temp_images.append(temp_path)

                doc.add_picture(temp_path, width=Inches(4))
                last_p = doc.paragraphs[-1]
                last_p.paragraph_format.space_after = Pt(10)

            except Exception as e:
                p.add_run("📷 Rasm yuklanmadi")
                print(f"Rasm yuklashda xato: {e}")

        # Oddiy javob
        elif field['field_type'] != 'photo':
            p.add_run(str(answer) if answer else "—")

    # Statik matn
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Ko'rsatilgan yordam (comment olingan)
    # h1 = doc.add_paragraph()
    # h1.add_run("Ko'rsatilgan yordam").bold = True
    # h1.paragraph_format.space_after = Pt(8)
    #
    # p1 = doc.add_paragraph(
    #     "Mazkur murojaat asosida yoshning masalasi belgilangan tartibda ko'rib chiqilib, "
    #     "uni Tartibli migratsiya dasturlari doirasida yo'naltirish bo'yicha tegishli amaliy choralar ko'rildi."
    # )
    # p1.paragraph_format.space_after = Pt(12)
    #
    # h2 = doc.add_paragraph()
    # h2.add_run("Natija").bold = True
    # h2.paragraph_format.space_after = Pt(8)
    #
    # p2 = doc.add_paragraph(
    #     "Ko'rilgan chora-tadbirlar natijasida yoshning murojaati ijobiy hal etilib, "
    #     "u belgilangan tartibda tartibli migratsiya yo'nalishiga yo'naltirildi hamda barqaror daromad manbaiga ega bo'ldi."
    # )
    # p2.paragraph_format.space_after = Pt(12)
    #
    # p3 = doc.add_paragraph(
    #     "Mazkur ma'lumotnoma rahbarlar va yoshlar o'rtasida o'tkazilgan uchrashuv natijalari yuzasidan "
    #     "rasmiy axborot sifatida tuzildi."
    # )
    # p3.paragraph_format.space_after = Pt(12)

    h3 = doc.add_paragraph()
    h3.add_run("Tasdiqlaymiz:").bold = True
    h3.paragraph_format.space_after = Pt(12)

    # Imzolar - YOSH F.I.SH QO'SHILGAN
    p_imzo1 = doc.add_paragraph()
    p_imzo1.add_run("Biriktirilgan rahbar: ").bold = True

    if yosh_fish:
        p_imzo1.add_run(yosh_fish)
    else:
        p_imzo1.add_run(rahbar)

    p_imzo1.paragraph_format.space_after = Pt(6)

    p_imzo1_sign = doc.add_paragraph("(imzo)")
    p_imzo1_sign.paragraph_format.space_after = Pt(20)

    # Tuman, Mahalla yetakchisi
    p_imzo2 = doc.add_paragraph()
    p_imzo2.add_run(f"{tuman}, {mahalla} yetakchisi: ").bold = True
    p_imzo2.add_run("__________________________")
    p_imzo2.paragraph_format.space_after = Pt(6)

    p_imzo2_sign = doc.add_paragraph("(imzo)")
    p_imzo2_sign.paragraph_format.space_after = Pt(20)

    # Sana
    current_date = datetime.now()
    p_sana = doc.add_paragraph()
    p_sana.add_run("Sana: «___» __________ ").bold = True
    p_sana.add_run(f"{current_date.year}-yil")
    p_sana.paragraph_format.space_after = Pt(20)

    doc.add_paragraph("Asoslovchi xujjatlar ilova qilinadi")

    # Faylni saqlash
    file_path = os.path.join(tempfile.gettempdir(),
                             f"malumotnoma_{user_id}_{current_date.strftime('%Y%m%d_%H%M%S')}.docx")
    doc.save(file_path)

    # Temp rasmlarni o'chirish
    for temp_img in temp_images:
        try:
            os.remove(temp_img)
        except:
            pass

    return file_path


@dp.callback_query_handler(text="response:confirm", state=RegisterState.answering)
async def confirm_response(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    response_data = {}
    for i, field in enumerate(data['fields']):
        response_data[field['column_name']] = data['answers'].get(str(i), "")

    await db.add_survey_response(
        survey_id=data['survey_id'],
        user_id=callback.from_user.id,
        response_data=response_data
    )

    try:
        await callback.message.edit_text("⏳ Ma'lumotnoma tayyorlanmoqda...")

        word_file = await generate_word_document(
            user_id=callback.from_user.id,
            response_data=response_data,
            fields=data['fields']
        )

        with open(word_file, 'rb') as file:
            await bot.send_document(
                callback.from_user.id,
                file,
                caption=(
                    "✅ <b>Rahmat!</b>\n\n"
                    "Sizning javoblaringiz muvaffaqiyatli saqlandi!\n\n"
                    "📄 Ma'lumotnoma tayyor! 🎉"
                )
            )

        os.remove(word_file)

    except Exception as e:
        print(f"WORD yaratishda xato: {e}")
        await callback.message.edit_text(
            "✅ <b>Rahmat!</b>\n\n"
            "Sizning javoblaringiz muvaffaqiyatli saqlandi! 🎉"
        )

    await state.finish()
    await callback.answer("Muvaffaqiyatli saqlandi!")


@dp.callback_query_handler(text="response:cancel", state=RegisterState.answering)
async def cancel_response(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await callback.message.edit_text(
        "❌ Bekor qilindi.\n\n"
        "Qaytadan boshlash uchun /register buyrug'ini bosing."
    )
    await callback.answer()