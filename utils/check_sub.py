# from loader import bot
#
# # ============ KANALLAR RO'YXATI ============
# #
# # Yangi kanal qo'shish uchun shu ro'yxatga qo'sh
# # Format: ("Kanal nomi", "kanal_username")
# #
# # MISOL:
# # URL: https://t.me/Samstf      → username: Samstf
# # URL: https://t.me/yiasamyosh  → username: yiasamyosh
# #
# # ⚠️ ESLATMA: Bot har bir kanalda ADMIN bo'lishi kerak!
#
# CHANNELS = [
#     # 1-kanal: https://t.me/Samstf
#     ("Samarqand yoshlar ishlari", "Samstf"),
#
#     # 2-kanal: https://t.me/yiasamyosh
#     ("Yoshlar ilhom akademiyasi", "yiasamyosh"),
#
#     # 3-kanal: https://t.me/...
#     # ("Kanal nomi", "kanal_username"),
#
#     # 4-kanal: https://t.me/...
#     # ("Kanal nomi", "kanal_username"),
#
#     # 5-kanal: https://t.me/...
#     # ("Kanal nomi", "kanal_username"),
# ]
#
#
# async def check_subscription(user_id: int) -> dict:
#     """
#     Foydalanuvchi barcha kanallarga obuna bo'lganini tekshirish
#
#     Qaytaradi:
#         {
#             "is_subscribed": True/False,
#             "not_subscribed": []  # Obuna bo'lmagan kanallar
#         }
#     """
#     not_subscribed = []
#
#     for channel_name, channel_username in CHANNELS:
#         try:
#             # Kanalda foydalanuvchi borligini tekshirish
#             member = await bot.get_chat_member(
#                 chat_id=f"@{channel_username}",
#                 user_id=user_id
#             )
#
#             # Agar obuna bo'lmagan yoki chiqib ketgan bo'lsa
#             if member.status in ["left", "kicked"]:
#                 not_subscribed.append({
#                     "name": channel_name,
#                     "username": channel_username
#                 })
#
#         except Exception as e:
#             # Xatolik bo'lsa (bot admin emas yoki kanal topilmadi)
#             print(f"Kanal tekshirishda xatolik ({channel_username}): {e}")
#             not_subscribed.append({
#                 "name": channel_name,
#                 "username": channel_username
#             })
#
#     return {
#         "is_subscribed": len(not_subscribed) == 0,
#         "not_subscribed": not_subscribed
#     }