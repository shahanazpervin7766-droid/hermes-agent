import discord
import requests
import os
import asyncio

# Render API URL
RENDER_API_URL = "https://hermes-agent-g3ch.onrender.com/chat"

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    try:
        response = requests.post(RENDER_API_URL, json={"message": message.content})
        if response.status_code == 200:
            reply_text = response.json().get("response", "No response received.")
            await message.channel.send(reply_text)
        else:
            await message.channel.send("Error processing request.")
    except Exception as e:
        await message.channel.send("Failed to connect to AI server.")

# Run Discord Bot
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
