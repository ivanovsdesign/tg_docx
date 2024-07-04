from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start_keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "✍️ Начать работу", callback_data="change_menu")
    ]])

menu_keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text = "👥 Авторы         ", callback_data="change_authors")
    ],
    [
        InlineKeyboardButton(text = "🔏 Правообладатель", callback_data="change_credits")
    ],
    [
        InlineKeyboardButton(text = "🐍 Язык           ", callback_data="change_language")
    ],
    [
        InlineKeyboardButton(text = "🤖 Выбор модели      ", callback_data="change_model")
    ],
    [
        InlineKeyboardButton(text = "💾 Начать генерацию      ", callback_data="change_generate")
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
        InlineKeyboardButton(text = "Назад", callback_data="change_menu")
    ]])