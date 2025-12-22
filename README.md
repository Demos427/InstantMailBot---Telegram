🤖 Telegram TempMail Bot
A fully automated Telegram bot that allows users to generate temporary email addresses and receive emails directly in the chat. The bot features an interactive history explorer and saves all data locally.

🚀 Quick Setup
Everything is automated. You only need to create two files and install the libraries to get started.

1. Get your Bot Token
Open Telegram and search for @BotFather.
Send the command /newbot.
Follow the instructions to name your bot.
Copy the HTTP API Token provided.

2. Install Dependencies
Open your terminal/command prompt and run this single command to install everything needed:

pip install "python-telegram-bot[job-queue]" aiohttp python-dotenv brotli

3. Create the Configuration File
Create a file named .env in your project folder and paste your token inside:

TELEGRAM_BOT_TOKEN= THE TOKEN 

5. Create the Bot Script
Create a file named main.py and paste the full source code of the bot into it.

▶️ How to Run
Simply run the script:

python main.py
That's it! The bot will automatically create the necessary database files (comptes.json and messages.json) the first time it runs.

🎮 Commands
/start - Main menu to generate emails.

/history - View received emails and read their content.

📂 Data Storage
comptes.json: Stores your active email sessions.
messages.json: Stores all received emails in readable text format.
These files are created automatically by the bot.

messages.json: Stores all received emails in readable text format.

These files are created automatically by the bot.
