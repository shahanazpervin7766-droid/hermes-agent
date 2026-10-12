import os
import asyncio
import discord
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# OpenRouter API Setup
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

class ChatRequest(BaseModel):
    message: str

def get_ai_response(user_message: str) -> str:
    response = client.chat.completions.create(
        model="nousresearch/hermes-3-llama-3.1-405b",
        messages=[{"role": "user", "content": user_message}]
    )
    return response.choices[0].message.content

@app.post("/chat")
def chat(request: ChatRequest):
    ai_reply = get_ai_response(request.message)
    return {"response": ai_reply}

# --- DISCORD BOT BOT INTEGRATION ---
discord_intents = discord.Intents.default()
discord_intents.message_content = True
discord_client = discord.Client(intents=discord_intents)

@discord_client.event
async def on_ready():
    print(f'Discord Bot Ready: Logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    # Process message via AI function
    try:
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, get_ai_response, message.content)
        await message.channel.send(reply)
    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("Sorry, something went wrong processing that.")

@app.on_event("startup")
async def startup_event():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        asyncio.create_task(discord_client.start(token))
    else:
        print("DISCORD_BOT_TOKEN environment variable not set.")
