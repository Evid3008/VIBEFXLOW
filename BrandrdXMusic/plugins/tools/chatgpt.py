import requests
from BrandrdXMusic import app  # Assuming this is your bot's main app instance
import time
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters
from MukeshAPI import api  # Assuming this is the API module you're using

# Command handler for chatGPT-like functionality
@app.on_message(filters.command(["chatgpt", "ai", "ask", "", "iri"], prefixes=[".", "J", "j", "s", "", "/"]))
async def chat_gpt(bot, message):
    try:
        # Show typing action in chat
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        # Get user's first name or default to "User"
        name = message.from_user.first_name if message.from_user else "User"

        # Check if there's a query after the command
        if len(message.command) < 2:
            await message.reply_text(f"**Hello {name}, How can I help you today?**")
        else:
            # Extract query from the message
            query = message.text.split(" ", 1)[1]
            print(f"Query from {name}: {query}")  # Debugging: Log the query

            # Call the MukeshAPI gemini method
            raw_response = api.gemini(query)
            print(f"Raw API Response: {raw_response}")  # Debugging: Log the raw response

            # Handle the API response
            if raw_response is None:
                await message.reply_text("**API currently unavailable. Please try again later.**")
            elif isinstance(raw_response, dict) and "results" in raw_response:
                response = raw_response["results"]
                await message.reply_text(f"{response}", parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply_text("**Unexpected response from API. Contact support if this persists.**")
                
    except Exception as e:
        # Catch and display any errors
        await message.reply_text(f"**Error: {str(e)}**")
        print(f"Error occurred: {str(e)}")  # Debugging: Log the error

# Start the bot (assuming this is handled in BrandrdXMusic)
if __name__ == "__main__":
    print("Bot is starting...")
    app.run()  # This starts the bot polling
