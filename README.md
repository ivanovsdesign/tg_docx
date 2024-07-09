# 📄 CV Generator Bot 🤖

Welcome to the CV Generator Bot! This Telegram bot generates a CV in a `.docx` file based on a user-provided prompt. 🌟

## ✨ Features

- 📝 Generates a CV in `.docx` format.
- 🔍 Uses OpenAI's GPT-4 to create structured CV data.
- 💬 Easy to use with Telegram.

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) for dependency management

### Step 1: Clone the Repository

```sh
git clone https://github.com/yourusername/cv-generator-bot.git
cd cv-generator-bot
```

### Step 2: Install dependencies
Project's dependencies are managed with poetry: 

```sh
poetry install 
```

### Step 3: Setup environment variables
Put your Telegram bot API token and OpenAI API token into .env file:

```.env
TELEGRAM_API_TOKEN="your_telegram_api_token"
OPENAI_API_TOKEN="your_openai_api_token"
```

### Step 4: Update OpenAI API endpoint
Ensure you are using the official OpenAI API endpoint. Update your endpoint in the code if necessary.

### Step 5: Run the bot in polling mode
Run bot with Poetry: 

```sh
poetry run python tg_doc_generator
```

## 🛠️ Usage
- Start a chat with your Telegram bot.
- Send a prompt with the details for your CV.
- Receive a .docx file with your generated CV!

---------------
Made with aiogram, openai, python-docx
