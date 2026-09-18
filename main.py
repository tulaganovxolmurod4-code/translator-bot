import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from googletrans import Translator
from gtts import gTTS

app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789")) # O'zingizning Telegram ID raqamingizni yozing

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

# Foydalanuvchi holatlari va balanslari uchun xotira
user_states = {}
user_balances = {}
admin_total_revenue = 0.0  # Admin balansi (tushgan pullar)

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Tarjimon", callback_data="menu_translator")
    builder.button(text="📱 Raqam sotib olish", callback_data="menu_numbers")
    builder.button(text="💰 Balans", callback_data="menu_balance")
    builder.button(text="💳 Hisobni to'ldirish", callback_data="menu_topup")
    builder.button(text="⚙️ Admin panel", callback_data="menu_admin")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_states[message.from_user.id] = None
    if message.from_user.id not in user_balances:
        user_balances[message.from_user.id] = 0.0
        
    await message.answer(
        "Assalomu alaykum! Botimizga xush kelibsiz.\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu()
    )

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    global admin_total_revenue
    user_id = callback.from_user.id
    data = callback.data

    if data == "menu_translator":
        user_states[user_id] = "waiting_for_translation"
        await callback.message.answer(
            "🌐 **Tarjimon rejimi yoqildi!**\n\n"
            "Menga istalgan o'zbekcha yoki inglizcha matn yuboring, tarjima qilib ovozli xabar bilan birga beraman.\n\n"
            "Asosiy menyuga qaytish uchun /start buyrug'ini bosing.",
            parse_mode="Markdown"
        )
    elif data == "menu_numbers":
        if user_id == ADMIN_ID:
            await callback.message.answer(
                "📱 **Virtual raqam sotib olish (Admin Rejimi):**\n\n"
                "Siz admin bo'lganingiz uchun bu raqam sizga **tekin** taqdim etiladi! (Tez orada SMS-Activate API ulanadi)",
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(
                "📱 **Virtual raqam sotib olish:**\n\n"
                "Tez orada SMS-Activate API orqali avtomatik raqam sotib olish tizimi ulanadi!",
                parse_mode="Markdown"
            )
    elif data == "menu_balance":
        balance = user_balances.get(user_id, 0.0)
        await callback.message.answer(f"💰 Sizning balansingiz: **{balance:,.2f} so'm / $**", parse_mode="Markdown")
    elif data == "menu_topup":
        await callback.message.answer(
            "💳 **Hisobni to'ldirish:**\n\n"
            "Click, Payme yoki Telegram Stars orqali balansingizni to'ldirish funksiyasi tez kunda qo'shiladi.",
            parse_mode="Markdown"
        )
    elif data == "menu_admin":
        if user_id == ADMIN_ID:
            await callback.message.answer(
                f"⚙️ **Admin Panel**\n\n"
                f"📥 Tushgan umumiy mablag': **{admin_total_revenue:,.2f} so'm**\n\n"
                f"Karta raqamiga o'tkazib olish uchun pastdagi tugmani bosing:",
                reply_markup=InlineKeyboardBuilder()
                .button(text="💸 Karta raqamiga o'tkazish", callback_data="admin_withdraw")
                .as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.answer("Siz admin emassiz!", show_alert=True)
            
    elif data == "admin_withdraw":
        if user_id == ADMIN_ID:
            if admin_total_revenue > 0:
                withdrawn = admin_total_revenue
                admin_total_revenue = 0.0
                await callback.message.answer(f"✅ Muvaffaqiyatli! {withdrawn:,.2f} so'm mablag' kartangizga yechish uchun navbatga qo'yildi.")
            else:
                await callback.message.answer("⚠️ Balansingizda yechib olish uchun mablag' mavjud emas.")
        
    await callback.answer()

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state == "waiting_for_translation":
        text = message.text
        if not text:
            return

        try:
            detection = await translator.detect(text)
            src_lang = detection.lang

            if src_lang == 'uz':
                dest_lang = 'en'
                audio_lang = 'en'
            else:
                dest_lang = 'uz'
                audio_lang = 'uz'

            translation = await translator.translate(text, dest=dest_lang)
            translated_text = translation.text

            tts = gTTS(text=translated_text, lang=audio_lang)
            audio_path = "voice.mp3"
            tts.save(audio_path)

            await message.answer(f"<b>Tarjima:</b> {translated_text}", parse_mode="HTML")

            audio_file = types.FSInputFile(audio_path)
            await message.answer_voice(voice=audio_file)

            if os.path.exists(audio_path):
                os.remove(audio_path)

        except Exception as e:
            logging.error(f"Xatolik: {e}")
            await message.answer(f"Xatolik yuz berdi: {e}")
    else:
        await message.answer(
            "Iltimos, botdan foydalanish uchun quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=get_main_menu()
        )

if __name__ == "__main__":
    keep_alive()
    
    async def main():
        await dp.start_polling(bot)
    
    asyncio.run(main())
