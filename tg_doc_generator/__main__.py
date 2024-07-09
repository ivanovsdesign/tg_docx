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
from modules.doc_creator import create_cv_template

import json

config = dotenv_values(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = config['TELEGRAM_API_TOKEN']
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
    job = State()
    experience = State()
    skills = State()
    generate = State()
    model = State()

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply('This bot generates CV based on your prompt', reply_markup=start_keyboard)

@dp.message(Form.menu)
@dp.message(Command('menu'))
async def show_menu(callback_query: types.CallbackQuery):

    await bot.send_message(callback_query.from_user.id, "Choose variable to change:", reply_markup=menu_keyboard)

@dp.callback_query(lambda c: c.data.startswith('change_'))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    if action == 'job':
        await state.set_state(Form.job)
        await bot.send_message(callback_query.from_user.id, "Enter your job title:")
    elif action == 'experience':
        await state.set_state(Form.experience)
        await bot.send_message(callback_query.from_user.id, "Enter your experience:")
    elif action == 'language':
        await state.set_state(Form.skills)
        await bot.send_message(callback_query.from_user.id, "Enter your skills:")
    elif action == 'generate':
        await state.set_state(Form.generate)
        await bot.send_message(callback_query.from_user.id, 'If you want, briefly describe your work experience')
    elif action == 'menu':
        await state.set_state(Form.menu)
        await show_menu(callback_query)
    elif action == 'model':
        await state.set_state(Form.model)
        await select_model(callback_query)
    
    await bot.answer_callback_query(callback_query.id)

@dp.message(Form.job)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(authors = message.text)
    await message.reply("Authors has been updated. Use /start to change another variable or create the document.", reply_markup=menu_keyboard)

@dp.message(Form.experience)
async def process_platform(message: types.Message, state: FSMContext):
    await state.update_data(credits = message.text)
    await message.reply("Credits has been updated. Use /start to change another variable or create the document.", reply_markup=menu_keyboard)

@dp.message(Form.skills)
async def process_language(message: types.Message, state: FSMContext):
    await state.update_data(language = message.text)
    await message.reply("Programming language has been updated. Use /start to change another variable or create the document.", reply_markup=menu_keyboard)

@dp.message(Form.model)
async def select_model(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Choose model:", reply_markup=model_keyboard)

@dp.callback_query(lambda c: c.data.startswith('model_'))
async def model_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    match action:
        case 'gpt35t':
            await state.update_data(model = 'gpt-3.5-turbo')
            await bot.send_message(callback_query.from_user.id, "GPT 3.5 Turbo installed", reply_markup=menu_keyboard)
        case 'gpt4t':
            await state.update_data(model = 'gpt-4-turbo')
            await bot.send_message(callback_query.from_user.id, "GPT 4 Turbo installed", reply_markup=menu_keyboard)
        case 'gpt4o':
            await state.update_data(model = 'gpt-4o')
            await bot.send_message(callback_query.from_user.id, "GPT 4o installed", reply_markup=menu_keyboard)
    

@dp.message(Form.generate)
async def handle_message(message: types.Message, state: FSMContext):

    data = await state.get_data()

    job = data.get('job', 'Software Developer')
    experience = data.get('experience', '2 years')
    skills = data.get('skills', 'Python')

    model = data.get('model', 'gpt-3.5-turbo')

    prompt = message.text
    output = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"You're an HR specialist who specialises on creating resumes for clients. You have to create appealing and engaging resume with relevant experience ",
            "role": "user",
            "content": f"You're an HR specialist who specializes on creating resumes to pursue clients' careers. You have to create appealing and engaging professional resume with relevant experience based on this prompt: {prompt}. Try to describe results of work in detail. Also add quantitative results. Make them up if not provided." + "Your output should exactly follow this format (DO NOT USE VALUES FROM THE EXAMPLE! OUTPUT ONLY JSON!): " + 
            """ {
                "personal_details": {
                    "Name": "John Doe",
                    "Address": "1234 Elm Street, Springfield, IL",
                    "Phone": "555-1234",
                    "Email": "john.doe@example.com"
                },
                "professional_experience": [
                    {
                    "title": "Software Engineer",
                    "company": "Tech Company",
                    "dates": "June 2018 - Present",
                    "description": "Developed and maintained web applications using Python and Django."
                    },
                    {
                    "title": "Junior Developer",
                    "company": "Startup Inc.",
                    "dates": "Jan 2016 - May 2018",
                    "description": "Assisted in the development of internal tools and applications."
                    }
                ],
                "education": [
                    {
                    "degree": "BSc in Computer Science",
                    "institution": "University of Springfield",
                    "dates": "2012 - 2016",
                    "description": "Focused on software development and algorithms."
                    }
                ],
                "skills": ["Python", "Django", "JavaScript", "HTML", "CSS"]
                }"""
        }
    ],
    model=model,
    )

    response = output.choices[0].message.content
    response = json.loads(response)

    # Create description
    filename = f"{message.from_user.id}_cv.docx"
    create_cv_template(response, filename)

    # Send the Word file
    await message.reply("Generated CV: ")
    await bot.send_document(message.chat.id, FSInputFile(filename))
    await message.reply("Continue: ", reply_markup=menu_keyboard)

async def main() -> None:
    await dp.start_polling(bot, skip_updates = True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())