import os
import threading
import requests
import discord
from flask import Flask, request, jsonify

app = Flask(__name__)

# OpenRouter API Setup
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

# Flask Route for API testing
@app.route('/')
def home():
    return "Throda AI Agent is Running!"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    bot_response = ask_openrouter(user_message)
    return jsonify({"response": bot_response})

# --- DISCORD BOT BOT SECTION ---
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

    # Reply in discord channel using OpenRouter API
    response_text = ask_openrouter(message.content)
    await message.channel.send(response_text)

def run_discord_bot():
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print("⚠️ DISCORD_BOT_TOKEN is not set in Environment Variables.")

# Run Discord Bot in a background thread
bot_thread = threading.Thread(target=run_discord_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
