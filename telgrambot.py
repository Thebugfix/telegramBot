import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json

TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TOGETHER_API_KEY = "your_together_ai_api_key_here"

# Dictionary to store conversation history for each user
conversation_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm your AI assistant. How can I help you today?")
    # Initialize conversation history for the user
    conversation_histories[update.effective_user.id] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text

    # Ensure conversation history exists for this user
    if user_id not in conversation_histories:
        conversation_histories[user_id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    # Add user message to conversation history
    conversation_histories[user_id].append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            'https://api.together.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {TOGETHER_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                "model": "meta-llama/Llama-2-70b-chat-hf",
                "messages": conversation_histories[user_id],
                "max_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "repetition_penalty": 1,
                "stop": ["<|im_end|>"],
                "stream": False
            }
        )

        response.raise_for_status()
        result = response.json()

        if result['choices'] and len(result['choices']) > 0 and 'message' in result['choices'][0]:
            ai_response = result['choices'][0]['message']['content']
            await update.message.reply_text(ai_response)

            # Add AI response to conversation history
            conversation_histories[user_id].append({"role": "assistant", "content": ai_response})
        else:
            raise ValueError('Unexpected response structure')

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Sorry, I'm having trouble understanding you right now.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()