import os
import sys
import threading
import asyncio
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Thora AI Bot is active and running!"

def run_discord():
    print("🚀 Starting Discord bot thread...", flush=True)
    import bot
    
    token = bot.DISCORD_TOKEN
    if not token:
        print("❌ CRITICAL: DISCORD_TOKEN is missing or None!", flush=True)
        return
    
    print(f"🔑 DISCORD_TOKEN found (Length: {len(token)} chars). Running bot...", flush=True)
    try:
        # Use run() inside this dedicated thread, which properly manages the asyncio loop
        bot.bot.run(token)
    except Exception as e:
        print(f"❌ Discord Login/Start Error: {e}", flush=True)

# Start background thread
t = threading.Thread(target=run_discord, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
