from keep_alive import keep_alive
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from googletrans import Translator
from gtts import gTTS

keep_alive()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Salom! Men tarjimon botman.\n\n"
        "Menga istalgan o'zbekcha matn yuboring — inglizchaga tarjima qilaman.\n"
        "Yoki inglizcha yozing — o'zbekchaga tarjima qilaman!"
    )

@dp.message()
async def translate_text(message: types.Message):
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

if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot)
    
    asyncio.run(main())
