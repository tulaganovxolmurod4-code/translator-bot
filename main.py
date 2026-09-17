import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from googletrans import Translator
from gtts import gTTS

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Salom! Men tarjimon botman.\n\n"
        "Menga istalgan o'zbekcha matn yuboring — uni inglizchaga tarjima qilib, ovozli xabar ham tashlab beraman.\n"
        "Yoki inglizcha yozing — o'zbekchaga tarjima qilaman!"
    )

@dp.message()
async def translate_text(message: types.Message):
    text = message.text
    if not text:
        return

    try:
        detection = translator.detect(text)
        src_lang = detection.lang

        if src_lang == 'uz':
            dest_lang = 'en'
            translated = translator.translate(text, src='uz', dest='en')
            audio_lang = 'en'
        else:
            dest_lang = 'uz'
            translated = translator.translate(text, dest='uz')
            audio_lang = 'uz'

        translated_text = translated.text

        tts = gTTS(text=translated_text, lang=audio_lang)
        audio_path = "voice.mp3"
        tts.save(audio_path)

        await message.answer(f"<b>Tarjima:</b> {translated_text}", parse_mode="HTML")
        
        audio_file = types.FSInputFile(audio_path)
        await message.answer_voice(voice=audio_file)

        if os.path.exists(audio_path):
            os.remove(audio_path)

    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
