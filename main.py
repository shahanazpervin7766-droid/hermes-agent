import os
import threading
from flask import Flask

# Flask web app for Render Web Service health-check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Start Discord bot in a background thread
def start_bot():
    import bot
    bot.bot.run(bot.DISCORD_TOKEN)

if __name__ == "__main__":
    t = threading.Thread(target=start_bot)
    t.daemon = True
    t.start()
    run_flask()
else:
    # When gunicorn runs `gunicorn main:app`
    t = threading.Thread(target=start_bot)
    t.daemon = True
    t.start()
