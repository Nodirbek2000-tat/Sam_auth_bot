from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ==================== USER KEYBOARDS ====================

def get_start_keyboard(has_profile: bool = False, is_approved: bool = False, is_rejected: bool = False):
    """Start klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if not has_profile:
        keyboard.add(
            InlineKeyboardButton("📝 Ma'lumotlarni to'ldirish", callback_data="initial:start")
        )
    elif is_rejected:
        keyboard.add(
            InlineKeyboardButton("🔄 Qayta so'rov yuborish", callback_data="initial:start")
        )
    elif is_approved:
        keyboard.add(
            InlineKeyboardButton("📋 So'rovnomani to'ldirish", callback_data="user:register")
        )

    if has_profile:
        keyboard.add(
            InlineKeyboardButton("👤 Profilim", callback_data="profile:view")
        )

    return keyboard


def get_register_keyboard():
    """Ro'yxatdan o'tish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 Ro'yxatdan o'tish", callback_data="user:register"))
    return keyboard


def get_cancel_keyboard(callback_data: str):
    """Bekor qilish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=callback_data))
    return keyboard


def get_send_request_keyboard():
    """So'rov yuborish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ So'rov yuborish", callback_data="initial:send_request"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data="initial:edit")
    )
    return keyboard


def get_additional_options_keyboard(options: list, question_index: int):
    """Qo'shimcha savollar uchun variantlar"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    for idx, option in enumerate(options):
        keyboard.insert(
            InlineKeyboardButton(option, callback_data=f"additional:{question_index}:{idx}")
        )

    keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="initial:cancel"))
    return keyboard


def get_options_keyboard(options: list, field_order: int):
    """So'rovnoma uchun variantlar"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    for idx, option in enumerate(options):
        keyboard.insert(
            InlineKeyboardButton(option, callback_data=f"answer:{field_order}:{idx}")
        )

    return keyboard


def get_confirm_response_keyboard():
    """Javoblarni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="response:confirm"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="response:cancel")
    )
    return keyboard


def get_profile_keyboard(is_approved: bool = False):
    """Profil klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if is_approved:
        keyboard.add(
            InlineKeyboardButton("📋 So'rovnomani to'ldirish", callback_data="user:register")
        )

    return keyboard


# ==================== ADMIN KEYBOARDS ====================

def get_admin_menu():
    """Admin panel asosiy menyu"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👥 Adminlar", callback_data="admin:admins"),
        InlineKeyboardButton("⏳ Tasdiqlar", callback_data="admin:user_approvals"),
    )
    keyboard.add(
        InlineKeyboardButton("📢 Kanallar", callback_data="admin:channels"),
        InlineKeyboardButton("❓ Kirish savollari", callback_data="admin:initial_questions"),
    )
    keyboard.add(
        InlineKeyboardButton("📋 So'rovnomalar", callback_data="admin:surveys"),
        InlineKeyboardButton("📊 Statistika", callback_data="admin:stats"),
    )
    keyboard.add(
        InlineKeyboardButton("📝 Registratsiya", callback_data="admin:registration"),
        InlineKeyboardButton("📢 Reklama yuborish", callback_data="admin:broadcast"),
    )
    keyboard.add(
        InlineKeyboardButton("❌ Yopish", callback_data="admin:close")
    )
    return keyboard


def get_registration_toggle_keyboard(is_enabled: bool):
    """Registratsiya on/off klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    on_text = "✅ On" if is_enabled else "⬜ On"
    off_text = "⬜ Off" if is_enabled else "✅ Off"
    keyboard.add(
        InlineKeyboardButton(on_text, callback_data="registration:on"),
        InlineKeyboardButton(off_text, callback_data="registration:off"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_stats_menu():
    """Statistika menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📥 Excel yuklash", callback_data="stats:download"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


# ==================== ADMIN MANAGE ====================

def get_admins_menu():
    """Adminlar menyu"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin_manage:add"),
        InlineKeyboardButton("👑 Super Admin qo'shish", callback_data="admin_manage:add_super"),
    )
    keyboard.add(
        InlineKeyboardButton("📋 Ro'yxat", callback_data="admin_manage:list"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_admin_list_keyboard(admins: list, current_user_id: int):
    """Adminlar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for admin in admins:
        status = "👑" if admin['is_super'] else "👤"
        name = f"{status} ID: {admin['telegram_id']}"

        keyboard.add(
            InlineKeyboardButton(name, callback_data=f"admin_manage:view:{admin['telegram_id']}")
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:admins")
    )
    return keyboard


def get_admin_actions(admin_id: int, is_super: bool, is_creator: bool = False):
    """Admin harakatlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Faqat oddiy adminni va o'zi qo'shgan adminni o'chirish mumkin
    if not is_super:
        keyboard.add(
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin_manage:delete:{admin_id}")
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin_manage:list")
    )
    return keyboard


def get_admin_delete_confirm(admin_id: int):
    """Adminni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"admin_manage:delete_confirm:{admin_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data="admin_manage:list")
    )
    return keyboard


# ==================== CHANNELS ====================

def get_channels_menu():
    """Kanallar menyu"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Kanal qo'shish", callback_data="channel:add"),
        InlineKeyboardButton("📋 Ro'yxat", callback_data="channel:list"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_channel_list_keyboard(channels: list):
    """Kanallar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel in channels:
        keyboard.add(
            InlineKeyboardButton(
                f"📢 {channel['channel_name']}",
                callback_data=f"channel:view:{channel['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:channels")
    )
    return keyboard


def get_channel_actions(channel_id: int):
    """Kanal harakatlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"channel:delete:{channel_id}"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="channel:list")
    )
    return keyboard


def get_channel_delete_confirm(channel_id: int):
    """Kanalni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"channel:delete_confirm:{channel_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data="channel:list")
    )
    return keyboard


# ==================== INITIAL QUESTIONS ====================

def get_initial_questions_menu():
    """Kirish savollari menyu"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Savol qo'shish", callback_data="initial_q:add"),
        InlineKeyboardButton("📋 Ro'yxat", callback_data="initial_q:list"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_initial_question_type_keyboard():
    """Savol turi tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Matn", callback_data="initial_q_type:text"),
        InlineKeyboardButton("🔘 Variantlar", callback_data="initial_q_type:choice"),
    )
    keyboard.add(
        InlineKeyboardButton("📷 Rasm", callback_data="initial_q_type:photo"),
        InlineKeyboardButton("📍 Lokatsiya", callback_data="initial_q_type:location"),
    )
    return keyboard


def get_add_more_options_keyboard():
    """Yana variant qo'shish"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Yana qo'shish", callback_data="initial_option:add_more"),
        InlineKeyboardButton("✅ Tugallash", callback_data="initial_option:finish")
    )
    return keyboard


def get_initial_question_list_keyboard(questions: list):
    """Kirish savollari ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for q in questions:
        status = "✅" if q['is_active'] else "⏸"
        keyboard.add(
            InlineKeyboardButton(
                f"{status} {q['question_text'][:30]}...",
                callback_data=f"initial_q:view:{q['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:initial_questions")
    )
    return keyboard


def get_initial_question_actions(question_id: int, is_active: bool):
    """Savol harakatlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    status_text = "⏸ Deaktiv qilish" if is_active else "✅ Aktiv qilish"
    keyboard.add(
        InlineKeyboardButton(status_text, callback_data=f"initial_q:toggle:{question_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"initial_q:delete:{question_id}"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="initial_q:list")
    )
    return keyboard


def get_initial_question_delete_confirm(question_id: int):
    """Savolni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"initial_q:delete_confirm:{question_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data="initial_q:list")
    )
    return keyboard


def get_initial_question_toggle_keyboard(question_id: int):
    """Savol holatini o'zgartirish"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔄 O'zgartirish", callback_data=f"initial_q:toggle:{question_id}")
    )
    return keyboard


# ==================== USER APPROVALS ====================

def get_user_approvals_menu():
    """Foydalanuvchilarni tasdiqlash menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("⏳ Kutayotganlar", callback_data="approval:pending_list"),
        InlineKeyboardButton("✅ Hammasini tasdiqlash", callback_data="approval:approve_all"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_pending_users_keyboard(users: list):
    """Kutayotgan foydalanuvchilar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for user in users:
        keyboard.add(
            InlineKeyboardButton(
                f"👤 {user['first_name']} {user['last_name']}",
                callback_data=f"approval:view:{user['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:user_approvals")
    )
    return keyboard


def get_user_detail_keyboard(profile_id: int):
    """Foydalanuvchi ma'lumotlari klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approval:approve:{profile_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"approval:reject:{profile_id}"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="approval:pending_list")
    )
    return keyboard


def get_approval_keyboard(profile_id: int):
    """Tasdiqlash klaviaturasi (admin uchun xabar)"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approval:approve:{profile_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"approval:reject:{profile_id}"),
    )
    return keyboard


def get_bulk_approval_confirm_keyboard():
    """Hammasini tasdiqlashni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha, tasdiqlash", callback_data="approval:approve_all_confirm"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="approval:approve_all_cancel")
    )
    return keyboard


# ==================== SURVEYS ====================

def get_surveys_menu():
    """So'rovnomalar menyu"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Yaratish", callback_data="survey:create"),
        InlineKeyboardButton("📋 Ro'yxat", callback_data="survey:list"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_field_type_keyboard():
    """Maydon turi tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Matn", callback_data="field_type:text"),
        InlineKeyboardButton("🔘 Variantlar", callback_data="field_type:choice"),
    )
    keyboard.add(
        InlineKeyboardButton("📷 Rasm", callback_data="field_type:photo"),
        InlineKeyboardButton("📍 Lokatsiya", callback_data="field_type:location"),
    )
    return keyboard


def get_add_more_fields_keyboard():
    """Yana ustun qo'shish"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Yana ustun", callback_data="field:add_more"),
        InlineKeyboardButton("✅ Tugallash", callback_data="field:finish")
    )
    return keyboard


def get_add_option_keyboard():
    """Yana variant qo'shish"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Yana variant", callback_data="option:add_more"),
        InlineKeyboardButton("✅ Tugallash", callback_data="option:finish")
    )
    return keyboard


def get_survey_confirm_keyboard():
    """So'rovnomani tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Saqlash", callback_data="survey:confirm_create"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="survey:cancel_create")
    )
    return keyboard


def get_survey_list_keyboard(surveys: list):
    """So'rovnomalar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for survey in surveys:
        status = "✅" if survey['is_active'] else "⏸"
        keyboard.add(
            InlineKeyboardButton(
                f"{status} {survey['name']}",
                callback_data=f"survey:view:{survey['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:surveys")
    )
    return keyboard


def get_survey_actions(survey_id: int, is_active: bool):
    """So'rovnoma harakatlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if is_active:
        keyboard.add(
            InlineKeyboardButton("⏸ Deaktiv qilish", callback_data=f"survey:deactivate:{survey_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("✅ Aktiv qilish", callback_data=f"survey:activate:{survey_id}")
        )

    keyboard.add(
        InlineKeyboardButton("📥 Excel yuklash", callback_data=f"survey:excel:{survey_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"survey:delete:{survey_id}"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="survey:list")
    )
    return keyboard


def get_survey_delete_confirm(survey_id: int):
    """So'rovnomani o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"survey:delete_confirm:{survey_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data="survey:list")
    )
    return keyboard