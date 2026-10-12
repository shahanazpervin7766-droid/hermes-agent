import os
import threading
import asyncio
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Thora AI Bot is active and running!"

def run_discord():
    import bot
    # Run the discord bot inside asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot.bot.start(bot.DISCORD_TOKEN))
    except Exception as e:
        print(f"❌ Discord Bot Error: {e}")

# Start Discord bot thread immediately on import
threading.Thread(target=run_discord, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
