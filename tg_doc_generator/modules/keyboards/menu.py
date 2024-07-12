from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start_keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "✍️ Начать работу", callback_data="change_menu")
    ]])

menu_keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "👥  Job Title         ", callback_data="change_job")
    ],
    [
        InlineKeyboardButton(text = "🔏 Experience", callback_data="change_experience")
    ],
    [
        InlineKeyboardButton(text = "🐍 Skills           ", callback_data="change_skills")
    ],
    [
        InlineKeyboardButton(text = "🤖 Choose model      ", callback_data="change_model")
    ],
    [
        InlineKeyboardButton(text = "💾 Start generating     ", callback_data="change_generate")
    ]
    ])

model_keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "GPT 3.5 Turbo", callback_data="model_gpt35t")
    ],
    [
        InlineKeyboardButton(text = "GPT 4 Turbo", callback_data="model_gpt4t")
    ],
    [
        InlineKeyboardButton(text = "GPT 4o", callback_data="model_gpt4o")
    ],
    [
        InlineKeyboardButton(text = "Back", callback_data="change_menu")
    ]])