from aiogram.dispatcher.filters.state import State, StatesGroup


# ==================== USER STATES ====================

class RegisterState(StatesGroup):
    """So'rovnoma to'ldirish uchun state"""
    answering = State()  # Savollarga javob berish


class InitialRegistrationState(StatesGroup):
    """Boshlang'ich ma'lumotlarni to'ldirish"""
    first_name = State()              # Ism
    last_name = State()               # Familiya
    birth_date = State()              # Tug'ilgan sana
    address = State()                 # Manzil
    additional_text = State()         # Qo'shimcha matn javob
    additional_choice = State()       # Qo'shimcha variant javob
    additional_photo = State()        # Qo'shimcha rasm javob
    additional_location = State()     # Qo'shimcha lokatsiya javob
    confirm = State()                 # Tasdiqlash


# ==================== ADMIN STATES ====================

class AdminState(StatesGroup):
    """Admin qo'shish/o'chirish"""
    add_admin = State()
    add_super_admin = State()
    remove_admin = State()


class ChannelState(StatesGroup):
    """Kanal qo'shish/o'chirish"""
    add_channel = State()
    remove_channel = State()


class SurveyCreateState(StatesGroup):
    """So'rovnoma yaratish"""
    name = State()              # So'rovnoma nomi
    column_name = State()       # Ustun nomi
    question_text = State()     # Savol matni
    field_type = State()        # Maydon turi (text/choice/photo/location)
    add_option = State()        # Variant qo'shish
    file_name = State()         # Fayl nomi


class SurveyEditState(StatesGroup):
    """So'rovnomani tahrirlash"""
    edit_name = State()
    edit_field = State()


class InitialQuestionsState(StatesGroup):
    """Boshlang'ich savollarni boshqarish"""
    question_text = State()     # Savol matni
    field_type = State()        # Maydon turi
    add_option = State()        # Variant qo'shish


class BroadcastStates(StatesGroup):
    """Reklama yuborish"""
    waiting_for_text = State()
    waiting_for_files = State()
    waiting_for_images = State()
    waiting_for_link = State()
    waiting_for_link_name = State()
    confirm = State()