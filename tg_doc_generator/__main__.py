import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.types import FSInputFile
from aiogram.types import ContentType
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from dotenv import dotenv_values
from openai import OpenAI

from typing import List

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

class Form(StatesGroup):
    menu = State()
    authors = State()
    credits = State()
    language = State()
    generate = State()

def create_word_file(authors, credits, language, text, filename="output.docx"):
    doc = Document()
    
    # Set up the style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    heading = doc.add_heading('РЕФЕРАТ', level=1)
    heading.font = style.font
    heading.font.all_caps = True
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    doc.add_paragraph(f'Авторы: {authors}')
    doc.add_paragraph(f'')
    doc.add_paragraph(f'Правообладатель: {credits}')
    doc.add_paragraph()

    # Add text
    doc.add_paragraph(text)
    
    # Save the document
    doc.save(filename)

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "✍️ Начать работу", callback_data="change_menu")
    ]])
    await message.reply('Этот бот сгененрирует Реферат и Листинг для регистрации Вашей программы для ЭВМ. Нажимая "Начать работу", Вы соглашаетесь с условиями использования.', reply_markup=keyboard)

@dp.message(Form.menu)
async def show_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "👥 Авторы         ", callback_data="change_authors")
    ],
    [
        InlineKeyboardButton(text = "🔏 Правообладатель", callback_data="change_credits")
    ],
    [
        InlineKeyboardButton(text = "🐍 Язык           ", callback_data="change_language")
    ],
    [
        InlineKeyboardButton(text = "💾 Начать генерацию      ", callback_data="change_generate")
    ]])
    
    await message.reply("Choose which variable to change:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('change_'))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    if action == 'authors':
        await state.set_state(Form.authors)
        await bot.send_message(callback_query.from_user.id, "What is the new name of the program?")
    elif action == 'credits':
        await state.set_state(Form.credits)
        await bot.send_message(callback_query.from_user.id, "What is the new platform?")
    elif action == 'language':
        await state.set_state(Form.language)
        await bot.send_message(callback_query.from_user.id, "What is the new programming language?")
    elif action == 'generate':
        await state.set_state(Form.generate)
        await bot.send_message(callback_query.from_user.id, 'Введите запрос для генерации описания к программе')
    elif action == 'menu':
        await state.set_state(Form.menu)
        await callback_query.answer('/menu')
    
    await bot.answer_callback_query(callback_query.id)

@dp.message(Form.authors)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(authors = message.text)
    await message.reply("Authors has been updated. Use /start to change another variable or create the document.")

@dp.message(Form.credits)
async def process_platform(message: types.Message, state: FSMContext):
    await state.update_data(credits = message.text)
    await message.reply("Credits has been updated. Use /start to change another variable or create the document.")

@dp.message(Form.language)
async def process_language(message: types.Message, state: FSMContext):
    await state.update_data(language = message.text)
    await message.reply("Programming language has been updated. Use /start to change another variable or create the document.")

@dp.message(Form.generate)
async def handle_message(message: types.Message, state: FSMContext):

    data = await state.get_data()

    authors = data['authors']
    credits = data['credits']
    language = data['language']

    prompt = message.text
    output = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"Ты ассистент, который генерирует описание для реферата к программе для ЭВМ для ее регистрации в Федеральном институте промышленной собственности. Структура твоего ответа ВСЕГДА должна быть следующей: Программа: (название программы), Аннотация: , Тип ЭВМ: , Язык: {language}, Объем программы: (Кб)",
            "role": "user",
            "content": prompt + f"Ты общаешься на русском языке. Если в запросе не указаны необходимые технологии, постарайся определить их самостоятельно и добавь их в текст. Стиль описания - научно-технический. Постарайся сделать свой ответ максимально похожим на реальный документ. Твой ответ не должен содержать исполняемого кода. Структура ответа следующая: Программа: (название программы, постарайся сформулировать такое название, которое будет наиболее полно отражать суть разработанного решения.), Аннотация: (должна быть емкой, описывать принцип работы, основные технические особенности и отличия от других программ, должна содержать примерно 200-250 слов), Тип ЭВМ: , Язык: {language}, Объем программы: (Кб)",
        }
    ],
    model="gpt-3.5-turbo",
    )
    response = output.choices[0].message.content

    # Create the Word file
    filename = f"{message.from_user.id}_document.docx"
    create_word_file(authors, credits, language, response, filename)

    # Send the Word file
    await message.reply("Here's your Word file!")
    await bot.send_document(message.chat.id, FSInputFile(filename))

async def main() -> None:
    await dp.start_polling(bot, skip_updates = True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())