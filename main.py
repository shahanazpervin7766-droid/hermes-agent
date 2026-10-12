import os
import threading
import requests
import asyncio
import discord
from flask import Flask, request, jsonify

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

def ask_openrouter(prompt):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nousresearch/hermes-3-llama-3.1-405b",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error querying OpenRouter: {e}")
        return "Sorry, I couldn't process that request."

@app.route('/')
def home():
    return "Throda AI Agent is Running!"

# --- DISCORD BOT SECTION ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Discord Bot Ready! Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    response_text = ask_openrouter(message.content)
    await message.channel.send(response_text)

def run_discord_bot():
    if not DISCORD_TOKEN:
        print("⚠️ DISCORD_BOT_TOKEN is missing!")
        return
    
    # Create and set event loop for background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(client.start(DISCORD_TOKEN))
    except Exception as e:
        print(f"❌ Discord Bot Error: {e}")

# Start Discord Bot in Background Thread
bot_thread = threading.Thread(target=run_discord_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
