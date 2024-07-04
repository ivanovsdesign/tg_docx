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
from aiogram.methods import AnswerCallbackQuery

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor

from dotenv import dotenv_values
from openai import OpenAI

from typing import List

from modules.keyboards.menu import start_keyboard, menu_keyboard, model_keyboard

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
    model = State()

def create_word_file(authors, credits, language, text, filename="output.docx"):
    doc = Document()
    
    # Set up the style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    heading = doc.add_heading('РЕФЕРАТ', level=1)
    run = heading.runs[0]
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.bold = False
    run.font.all_caps = True
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

def create_listing(text, filename="listing.docx"):
    doc = Document()
    
    # Set up the style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Courier'
    font.size = Pt(12)

    # Add text
    doc.add_paragraph(text)
    
    # Save the document
    doc.save(filename)

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply('Этот бот сгененрирует Реферат и Листинг для регистрации Вашей программы для ЭВМ. Нажимая "Начать работу", Вы соглашаетесь с условиями использования.', reply_markup=start_keyboard)

@dp.message(Form.menu)
@dp.message(Command('menu'))
async def show_menu(callback_query: types.CallbackQuery):

    await bot.send_message(callback_query.from_user.id, "Выберите поле, которое хотите изменить:", reply_markup=menu_keyboard)

@dp.callback_query(lambda c: c.data.startswith('change_'))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    if action == 'authors':
        await state.set_state(Form.authors)
        await bot.send_message(callback_query.from_user.id, "Введите ФИО авторов через запятую:")
    elif action == 'credits':
        await state.set_state(Form.credits)
        await bot.send_message(callback_query.from_user.id, "Введите название учреждения-правообладателя:")
    elif action == 'language':
        await state.set_state(Form.language)
        await bot.send_message(callback_query.from_user.id, "Введите название языка программирования")
    elif action == 'generate':
        await state.set_state(Form.generate)
        await bot.send_message(callback_query.from_user.id, 'Введите запрос для генерации описания к программе')
    elif action == 'menu':
        await state.set_state(Form.menu)
        await show_menu(callback_query)
    elif action == 'model':
        await state.set_state(Form.model)
        await select_model(callback_query)
    
    await bot.answer_callback_query(callback_query.id)

@dp.message(Form.authors)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(authors = message.text)
    await message.reply("Authors has been updated. Use /start to change another variable or create the document.", reply_markup=menu_keyboard)

@dp.message(Form.credits)
async def process_platform(message: types.Message, state: FSMContext):
    await state.update_data(credits = message.text)
    await message.reply("Credits has been updated. Use /start to change another variable or create the document.", reply_markup=menu_keyboard)

@dp.message(Form.language)
async def process_language(message: types.Message, state: FSMContext):
    await state.update_data(language = message.text)
    await message.reply("Programming language has been updated. Use /start to change another variable or create the document.", reply_markup=menu_keyboard)

@dp.message(Form.model)
async def select_model(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Выберите модель:", reply_markup=model_keyboard)

@dp.callback_query(lambda c: c.data.startswith('model_'))
async def model_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    match action:
        case 'gpt35t':
            await state.update_data(model = 'gpt-3.5-turbo')
            await bot.send_message(callback_query.from_user.id, "Установлена GPT 3.5 Turbo", reply_markup=menu_keyboard)
        case 'gpt4t':
            await state.update_data(model = 'gpt-4-turbo')
            await bot.send_message(callback_query.from_user.id, "Установлена GPT 4 Turbo", reply_markup=menu_keyboard)
        case 'gpt4o':
            await state.update_data(model = 'gpt-4o')
            await bot.send_message(callback_query.from_user.id, "Установлена GPT 4o", reply_markup=menu_keyboard)
    

@dp.message(Form.generate)
async def handle_message(message: types.Message, state: FSMContext):

    data = await state.get_data()

    authors = data.get('authors', 'Default people')
    credits = data.get('credits', 'Default people')
    language = data.get('language', 'Python')

    model = data.get('model', 'gpt-3.5-turbo')

    prompt = message.text
    output = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"Ты ассистент, который генерирует описание для реферата к программе для ЭВМ для ее регистрации в Федеральном институте промышленной собственности. Структура твоего ответа ВСЕГДА должна быть следующей: Программа: (название программы), Аннотация: , Тип ЭВМ: , Язык: {language}, Объем программы: (Кб)",
            "role": "user",
            "content": prompt + f"Ты общаешься на русском языке. Если в запросе не указаны необходимые технологии, постарайся определить их самостоятельно и добавь их в текст. Стиль описания - научно-технический. Постарайся сделать свой ответ максимально похожим на реальный документ. Твой ответ не должен содержать исполняемого кода. Структура ответа следующая: Программа: (название программы, постарайся сформулировать такое название, которое будет наиболее полно отражать суть разработанного решения.), Аннотация: (должна быть емкой, описывать принцип работы, основные технические особенности и отличия от других программ, ДОЛЖНА содержать примерно 200-250 слов), Тип ЭВМ: , Язык: {language}, Объем программы: (Кб)",
        }
    ],
    model=model,
    )
    response = output.choices[0].message.content

    await message.reply('Генерация реферата завершена...\nГенерация листинга (1/2)')

    output = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"Ты ассистент, который генерирует код программы для ЭВМ для его регистрации в Федеральном институте промышленной собственности. Твой ответ должен содержать только код с комментариями",
            "role": "user",
            "content": response + f"Основываясь на данном описании, сгенерируй код для описываемой программы, используя указанные языки/технологии. Твой ответ должен содержать только название исполняемого файла (или нескольких файлов, если потребуется) и код. Код каждого исполняемого файла должен распологаться строго после названия файла. Комментарии должны быть короткими и емкими, на русском языке. Не используй незаконченные фрагменты кода и не указывай, где необходимо дополнить код. Твоя задача - выдать как можно больше кода. Ни в коем случае НЕ ОСТАВЛЯЙ пустые конструкции. Комментарии по поводу файлов, не относящихся к исполняемым, оставляй внутри кода. Не обрамляй код в код-блок, выдавай просто текст.",
        }
    ],
    model=model,
    )
    listing = output.choices[0].message.content

    await message.reply('Генерация листинга (2/2)\nПодготовка файлов')

    output = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"Ты выступаешь в роли программиста, которому необходимо дополнить код. Необходимо дополнить исходную структуру файла.",
            "role": "user",
            "content": f"Ты выступаешь в роли программиста, которому необходимо дополнить код. Необходимо дополнить исходную структуру файла. Постарайся как можно более полно реализовть существующие функции. Не пиши ничего, кроме кода. Сохрани исходну структуру документа. НЕ ОБРАМЛЯЙ код в код-блок, ВЫДАВАЙ ПРОСТО ТЕКСТ. В ответе должен присутствовать ВЕСЬ текст исходного кода с твоими дополнениями. Исходный код: {listing}",
        }
    ],
    model='gpt-4o',
    )

    listing = output.choices[0].message.content

    # Create description
    filename_description = f"{message.from_user.id}_document.docx"
    create_word_file(authors, credits, language, response, filename_description)
    # Create listing 
    filename_listing = f"{message.from_user.id}_listing.docx"
    create_listing(listing, filename_listing)

    # Send the Word file
    await message.reply("Сгенерированные документы:")
    await bot.send_document(message.chat.id, FSInputFile(filename_description))
    await bot.send_document(message.chat.id, FSInputFile(filename_listing))
    await message.reply("Продолжить: ", reply_markup=menu_keyboard)

async def main() -> None:
    await dp.start_polling(bot, skip_updates = True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())