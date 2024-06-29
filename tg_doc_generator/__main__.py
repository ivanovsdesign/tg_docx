import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from aiogram.types import ContentType
from aiogram import F

from docx import Document
from docx.shared import Pt

from dotenv import dotenv_values
from openai import OpenAI

config = dotenv_values(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = config['API_TOKEN']
OPEANAI_API_TOKEN = config['OPENAI_API_TOKEN']
dp = Dispatcher()
router = Router()

bot = Bot(token=API_TOKEN)

client = OpenAI(
    # This is the default and can be omitted
    api_key=OPEANAI_API_TOKEN,
    base_url="https://api.proxyapi.ru/openai/v1" # For usage from Russian Federation
)

def create_word_file(text, filename="output.docx"):
    doc = Document()
    
    # Set up the style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(12)

    # Add text
    doc.add_paragraph(text)
    
    # Save the document
    doc.save(filename)

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply('Hello! This bot will generate .docx file based on your prompt')

@dp.message()
async def handle_message(message: types.Message):
    prompt = message.text
    output = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    model="gpt-3.5-turbo",
    )
    response = output.choices[0].message.content

    # Create the Word file
    filename = f"{message.from_user.id}_document.docx"
    create_word_file(response, filename)

    # Send the Word file
    await message.reply("Here's your Word file!")
    await bot.send_document(message.chat.id, FSInputFile(filename))

async def main() -> None:
    await dp.start_polling(bot, skip_updates = True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())