import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

MY_CARD_NUMBER = "5614681804146078"
MY_CARD_HOLDER = "Tulaganov Xolmurod"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_states = {}
user_balances = {}
admin_total_revenue = 0.0

CUSTOM_NUMBERS_STOCK = {
    "russia": [
        {"phone": "79991234567", "code": "Hali kelmadi"},
        {"phone": "79997654321", "code": "Hali kelmadi"}
    ],
    "kazakhstan": [
        {"phone": "77771112233", "code": "Hali kelmadi"}
    ],
    "usa": [
        {"phone": "19998887766", "code": "Hali kelmadi"}
    ]
}

COUNTRY_PRICES = {
    "russia": {
        "name": "🇷🇺 Rossiya raqami",
        "country_code": "russia",
        "retail_price": 10000.0,
    },
    "kazakhstan": {
        "name": "🇰🇿 Qozog'iston raqami",
        "country_code": "kazakhstan",
        "retail_price": 10000.0,
    },
    "usa": {
        "name": "🇺🇸 AQSh (USA) raqami",
        "country_code": "usa",
        "retail_price": 10000.0,
    }
}

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Raqam sotib olish", callback_data="menu_numbers")
    builder.button(text="💰 Balans", callback_data="menu_balance")
    builder.button(text="💳 Hisobni to'ldirish", callback_data="menu_topup")
    builder.button(text="⚙️ Admin panel", callback_data="menu_admin")
    builder.adjust(2, 2)
    return builder.as_markup()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_states[message.from_user.id] = None
    if message.from_user.id not in user_balances:
        user_balances[message.from_user.id] = 0.0
        
    balance = user_balances.get(message.from_user.id, 0.0)
    await message.answer(
        f"Assalomu alaykum! Virtual raqamlar sotib olish botiga xush kelibsiz.\n"
        f"💰 Sizning balansingiz: **{balance:,.2f} so'm**\n\n"
        f"Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    global admin_total_revenue
    user_id = callback.from_user.id
    data = callback.data

    if data == "menu_numbers":
        builder = InlineKeyboardBuilder()
        for key, conf in COUNTRY_PRICES.items():
            stock_count = len(CUSTOM_NUMBERS_STOCK.get(key, []))
            builder.button(
                text=f"{conf['name']} — {conf['retail_price']:,.0f} so'm (Stokda: {stock_count})",
                callback_data=f"buy_country_{key}"
            )
        builder.button(text="🔙 Ortga", callback_data="menu_back")
        builder.adjust(1)
        
        await callback.message.answer(
            "📱 **Telegram uchun virtual raqam tanlang:**\n\n"
            "Qaysi davlat raqamini sotib olmoqchisiz?",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    elif data.startswith("buy_country_"):
        country_key = data.replace("buy_country_", "")
        conf = COUNTRY_PRICES.get(country_key)
        if not conf:
            await callback.answer("Xatolik yuz berdi!", show_alert=True)
            return

        price = conf["retail_price"]
        balance = user_balances.get(user_id, 0.0)
        
        if user_id != ADMIN_ID and balance < price:
            await callback.message.answer(
                f"⚠️ Balansingiz yetarli emas!\n"
                f"Kerakli mablag': {price:,.2f} so'm\n"
                f"Sizning balansingiz: {balance:,.2f} so'm\n\n"
                "Iltimos, avval hisobingizni to'ldiring.",
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        stock_list = CUSTOM_NUMBERS_STOCK.get(country_key, [])
        if not stock_list:
            await callback.message.answer(
                "❌ Kechirasiz, hozirda bu davlat uchun bo'sh raqamlar qolmagan!\n"
                "Iltimos, admin raqam qo'shishini kuting yoki boshqa davlatni tanlang.",
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        item = stock_list.pop(0)
        phone = item["phone"]

        if user_id != ADMIN_ID:
            user_balances[user_id] -= price
            admin_total_revenue += price
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 SMS kodni olish", callback_data=f"get_sms_{country_key}_{phone}")
        builder.button(text="🔙 Asosiy menyu", callback_data="menu_back")
        builder.adjust(1)

        await callback.message.answer(
            f"✅ Tabriklaymiz! Raqam muvaffaqiyatli olindi.\n\n"
            f"📱 Sizning raqamingiz: `+{phone}`\n\n"
            f"⚠️ **Ko'rsatma:**\n"
            f"1. Telegram'ga kiring va shu raqamni yozing.\n"
            f"2. Kod kelgach, pastdagi **'🔄 SMS kodni olish'** tugmasini bosing!",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

    elif data.startswith("get_sms_"):
        parts = data.split("_")
        country_key = parts[2]
        phone = parts[3]

        found_item = None
        for lst in CUSTOM_NUMBERS_STOCK.values():
            for item in lst:
                if item["phone"] == phone:
                    found_item = item
                    break

        current_code = found_item["code"] if found_item else "Hali kelmadi"
        
        await callback.message.answer(
            f"📱 Raqam: `+{phone}`\n"
            f"📨 Telegram SMS kodi: **{current_code}**\n\n"
            f"*(Agar kod hali 'Hali kelmadi' bo'lsa, ozgina kuting va qayta tugmani bosing)*",
            reply_markup=InlineKeyboardBuilder()
            .button(text="🔄 Yangilash", callback_data=data)
            .button(text="🔙 Asosiy menyu", callback_data="menu_back")
            .adjust(1)
            .as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer("Yangilandi!")

    elif data == "menu_balance":
        balance = user_balances.get(user_id, 0.0)
        await callback.message.answer(f"💰 Sizning balansingiz: **{balance:,.2f} so'm**", parse_mode="Markdown")
        
    elif data == "menu_topup":
        user_states[user_id] = "waiting_for_receipt"
        card_text = (
            f"💳 **Hisobni to'ldirish (Plastik karta orqali):**\n\n"
            f"Quyidagi karta raqamiga kerakli summani o'tkazing (Uzcard / Humo):\n\n"
            f"Karta raqami: `{MY_CARD_NUMBER}`\n"
            f"Karta egasi: **{MY_CARD_HOLDER}**\n\n"
            f"⚠️ **Diqqat:** Karta raqamini ustiga bosib nusxalab olishingiz mumkin.\n\n"
            f"📸 Pulni o'tkazgach, to'lov cheki (skrinshot) yoki rasmini shu chatga yuboring. Shundan so'ng administrator tomonidan tasdiqlanib balansingizga mablag' qo'shiladi!"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Ortga", callback_data="menu_back")
        builder.adjust(1)
        
        await callback.message.answer(card_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        
    elif data.startswith("approve_topup_"):
        if user_id == ADMIN_ID:
            target_user_id = int(data.split("_")[2])
            topup_amount = 10000.0
            
            if target_user_id not in user_balances:
                user_balances[target_user_id] = 0.0
            user_balances[target_user_id] += topup_amount
            
            try:
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n✅ **HOLAT: Tasdiqlandi va mablag' qo'shildi!**",
                    reply_markup=None
                )
            except Exception:
                try:
                    await callback.message.edit_text(
                        text=callback.message.text + "\n\n✅ **HOLAT: Tasdiqlandi va mablag' qo'shildi!**",
                        reply_markup=None
                    )
                except Exception:
                    pass

            try:
                await bot.send_message(
                    target_user_id,
                    f"✅ **To'lov muvaffaqiyatli tasdiqlandi!**\n"
                    f"🟢 Balansingizga **{topup_amount:,.2f} so'm** qo'shildi.\n"
                    f"Joriy balans: **{user_balances[target_user_id]:,.2f} so'm**",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            await callback.answer("To'lov muvaffaqiyatli tasdiqlandi!")
        else:
            await callback.answer("Siz admin emassiz!", show_alert=True)
            
    elif data == "menu_admin":
        if user_id == ADMIN_ID:
            await callback.message.answer(
                f"⚙️ **Admin Panel**\n\n"
                f"📥 Tushgan umumiy mablag': **{admin_total_revenue:,.2f} so'm**\n\n"
                f"Kerakli amalni tanlang:",
                reply_markup=InlineKeyboardBuilder()
                .button(text="➕ Raqam va SMS qo'shish", callback_data="admin_add_number")
                .button(text="🔙 Ortga", callback_data="menu_back")
                .adjust(1)
                .as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.answer("Siz admin emassiz!", show_alert=True)

    elif data == "admin_add_number":
        if user_id == ADMIN_ID:
            user_states[user_id] = "waiting_for_admin_number"
            await callback.message.answer(
                "➕ **Yangi raqam va kod qo'shish:**\n\n"
                "Quyidagi formatda yuboring:\n"
                "`davlat, raqam, sms_kod`\n\n"
                "Namuna:\n"
                "russia, 79991234567, 54321\n\n"
                "*(Davlatlar: russia, kazakhstan, usa)*",
                parse_mode="Markdown"
            )
            
    elif data == "menu_back":
        user_states[user_id] = None
        await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu())
        
    await callback.answer()

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if user_id == ADMIN_ID and state == "waiting_for_admin_number":
        try:
            text = message.text.strip()
            parts = [p.strip() for p in text.split(",")]
            country = parts[0]
            phone = parts[1]
            code = parts[2]

            if country not in CUSTOM_NUMBERS_STOCK:
                CUSTOM_NUMBERS_STOCK[country] = []
            
            CUSTOM_NUMBERS_STOCK[country].append({"phone": phone, "code": code})
            user_states[user_id] = None

            await message.answer(
                f"✅ **Muvaffaqiyatli qo'shildi!**\n"
                f"Davlat: `{country}`\n"
                f"Raqam: `+{phone}`\n"
                f"SMS Kod: `{code}`",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            await message.answer("⚠️ Xatolik! Formatni to'g'ri kiriting:\n`russia, 79991234567, 54321`", parse_mode="Markdown")
        return

    if state == "waiting_for_receipt":
        if message.photo or message.document:
            user_states[user_id] = None
            
            await message.answer("✅ To'lov cheki qabul qilindi! Admin tekshirishi uchun yuborildi. Iltimos kuting...")
            
            caption = (
                f"💳 **Yangi to'lov cheki keldi!**\n\n"
                f"👤 Foydalanuvchi ID: `{user_id}`\n"
                f"🔗 Username: @{message.from_user.username if message.from_user.username else 'mavjud emas'}\n"
                f"Ism: {message.from_user.full_name}"
            )
            
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Tasdiqlash (+10,000 so'm)", callback_data=f"approve_topup_{user_id}")
            builder.adjust(1)
            
            if message.photo:
                await bot.send_photo(
                    ADMIN_ID,
                    message.photo[-1].file_id,
                    caption=caption,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
            else:
                await bot.send_document(
                    ADMIN_ID,
                    message.document.file_id,
                    caption=caption,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
        else:
            await message.answer("⚠️ Iltimos, faqat to'lov chekining skrinshotini (rasm yoki fayl ko'rinishida) yuboring.")
    else:
        balance = user_balances.get(user_id, 0.0)
        await message.answer(
            f"💰 Sizning balansingiz: **{balance:,.2f} so'm**\n\n"
            "Iltimos, botdan foydalanish uchun quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    keep_alive()
    
    async def main():
        await dp.start_polling(bot)
    
    asyncio.run(main())
