import os
import glob
import io
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

from key_rotator import KeyRotator
from doc_generator import generate_pdf, generate_pptx
from web_search import search_live_web
from image_tools import process_image_command
from image_generator import generate_ai_image
from video_generator import generate_ai_video

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

rotator = KeyRotator(openrouter_key=OPENROUTER_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ক্লাউড মেমোরি চ্যানেল
STRATEGY_CHANNEL = "bullders-strategy"
GENERAL_MEMORY_CHANNEL = "bullders-memory"
recent_history = []

async def get_channel_notes(guild: discord.Guild, channel_name: str, limit: int = 40) -> str:
    if not guild:
        return ""
    ch = discord.utils.get(guild.text_channels, name=channel_name)
    if not ch:
        return ""
    try:
        notes = []
        async for msg in ch.history(limit=limit):
            if msg.content.startswith("📌"):
                notes.append(msg.content.replace("📌", "").strip())
        return "\n".join(reversed(notes))
    except Exception as e:
        return ""

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🐂 BullDers Master Multi-Channel AI Online as {bot.user}", flush=True)

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # চ্যানেলের নাম বোঝা (Auto Channel Detection)
    ch_name = getattr(message.channel, "name", "").lower()
    is_dm = isinstance(message.channel, discord.DMChannel) or message.guild is None
    is_mentioned = bot.user.mentioned_in(message) if bot.user else False

    # মেমোরি স্টোরেজ চ্যানেলগুলোতে কথা বলবে না
    if ch_name in [STRATEGY_CHANNEL, GENERAL_MEMORY_CHANNEL]:
        return

    user_text = message.clean_content.replace(f"@{bot.user.name}", "").strip()
    
    # ইমেজ ফাইল চেক
    image_bytes = None
    if message.attachments:
        for att in message.attachments:
            if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                try:
                    image_bytes = await att.read()
                    break
                except Exception as e:
                    pass

    if not user_text and not image_bytes:
        return

    # গ্রিটিংস স্ট্রিক্ট হ্যান্ডলার
    clean_lower = user_text.lower().strip()
    if clean_lower in ["hi", "hello", "hlw", "hey", "হাই", "হ্যালো"]:
        await message.reply("হ্যালো। বলুন, কী নির্দেশ?")
        return

    async with message.channel.typing():
        # ==========================================================
        # ১. ইমেজ ক্রিয়েশন চ্যানেল (বা ইমেজ কমান্ড)
        # ==========================================================
        if "image" in ch_name or "ইমেজ" in ch_name or "photo" in ch_name or any(w in clean_lower for w in ["image generate", "ছবি বানাও", "generate image", "create image"]):
            prompt = user_text
            for w in ["image generate", "ছবি বানাও", "generate image", "create image", "image"]:
                prompt = prompt.replace(w, "").strip(" :,-")
            img_io = generate_ai_image(prompt or "a futuristic wallstreet golden bull cinematic 8k")
            if img_io:
                await message.reply(file=discord.File(fp=img_io, filename="image.png"))
            else:
                await message.reply("ছবি তৈরিতে সমস্যা হয়েছে।")
            return

        # ==========================================================
        # ২. ভিডিও চ্যানেল (বা ভিডিও কমান্ড)
        # ==========================================================
        if "video" in ch_name or "ভিডিও" in ch_name or any(w in clean_lower for w in ["video generate", "ভিডিও বানাও", "make video"]):
            v_prompt = user_text.replace("video generate", "").replace("ভিডিও বানাও", "").strip(" :,-")
            v_io = generate_ai_video(v_prompt or "cinematic trading chart breakout animation")
            if v_io:
                await message.reply(file=discord.File(fp=v_io, filename="video.gif"))
            else:
                await message.reply("ভিডিও জেনারেট করা সম্ভব হয়নি।")
            return

        # ==========================================================
        # ৩. ইমেজ এডিট চ্যানেল (বা কালার চেঞ্জ কমান্ড)
        # ==========================================================
        if "edit" in ch_name or (image_bytes and any(w in clean_lower for w in ["green", "সবুজ", "color", "রং", "bright", "black and white"])):
            if image_bytes:
                edited_io = process_image_command(image_bytes, user_text)
                if edited_io:
                    await message.reply(file=discord.File(fp=edited_io, filename="edited.png"))
                    return

        # ==========================================================
        # ৪. স্ট্র্যাটেজি চ্যানেল / স্ট্র্যাটেজি লকিং
        # ==========================================================
        if "strategy" in ch_name or "স্ট্র্যাটেজি" in ch_name or "স্ট্র্যাটেজিটা মনে রাখো" in user_text:
            rule_text = user_text.replace("স্ট্র্যাটেজিটা মনে রাখো", "").strip(" :,-")
            if message.guild:
                s_ch = discord.utils.get(message.guild.text_channels, name=STRATEGY_CHANNEL)
                if not s_ch:
                    s_ch = await message.guild.create_text_channel(STRATEGY_CHANNEL)
                await s_ch.send(f"📌 [STRATEGY]: {rule_text}")
            await message.reply(f"ট্রেডিং স্ট্র্যাটেজি সংরক্ষিত:\n> {rule_text}")
            return

        # ==========================================================
        # ৫. PDF / PPT / সিভি চ্যানেল
        # ==========================================================
        if "pdf" in ch_name or "ডকুমেন্ট" in ch_name or "pdf বানাও" in clean_lower:
            topic = user_text.replace("pdf বানাও", "").strip()
            pdf_body = rotator.generate_content(prompt=f"Professional structured documentation for: {topic}", system_instruction="Output clean formatted report.")
            pdf_io = generate_pdf(title=topic.upper() or "DOCUMENT", content=pdf_body)
            await message.reply(file=discord.File(fp=pdf_io, filename="doc.pdf"))
            return

        if "ppt" in ch_name or "slides" in ch_name or "ppt বানাও" in clean_lower:
            topic = user_text.replace("ppt বানাও", "").strip()
            slides = [
                {"title": "Overview", "content": f"Executive summary on {topic}"},
                {"title": "Core Analysis", "content": "1. Strategic Factors\n2. Execution Logic\n3. Risk Assessment"},
                {"title": "Next Steps", "content": "Actionable roadmap and timeline."}
            ]
            ppt_io = generate_pptx(title=topic.upper() or "PRESENTATION", slides_data=slides)
            await message.reply(file=discord.File(fp=ppt_io, filename="presentation.pptx"))
            return

        if "cv" in ch_name or "resume" in ch_name or "সিভি" in clean_lower:
            cv_text = rotator.generate_content(prompt=f"Create a professional modern CV/Resume for: {user_text}", system_instruction="Format as a clean professional CV.")
            cv_io = generate_pdf(title="CURRICULUM VITAE", content=cv_text)
            await message.reply(content="সিভি প্রস্তুত:", file=discord.File(fp=cv_io, filename="CV.pdf"))
            return

        # ==========================================================
        # ৬. ক্লায়েন্ট চ্যানেল
        # ==========================================================
        if "client" in ch_name or "ক্লায়েন্ট" in ch_name:
            client_instruction = (
                "তুমি বুলডার্স। এই চ্যানেলে ক্লায়েন্টদের সংক্রান্ত আলোচনা ও সাপোর্ট পরিচালনা করা হয়। "
                "প্রফেশনাল, টু-দ্য-পয়েন্ট এবং ব্যবসায়িক দৃষ্টিভঙ্গি নিয়ে উত্তর দাও।"
            )
            ans = rotator.generate_content(prompt=user_text, system_instruction=client_instruction)
            await message.reply(ans)
            return

        # ==========================================================
        # ৭. সাধারণ চ্যাট ও ট্রেডিং চার্ট এনালাইসিস
        # ==========================================================
        live_search_data = ""
        if any(w in clean_lower for w in ["news", "নিউজ", "gold", "গোল্ড", "cpi", "nfp", "fomc"]):
            live_search_data = search_live_web(f"forex factory red folder news gold today {user_text}", max_results=4)

        strategies = await get_channel_notes(message.guild, STRATEGY_CHANNEL)
        strict_instruction = (
            "তুমি 'বুলডার্স' (BullDers) — সুপার ইন্টেলিজেন্ট, স্ট্রিক্ট এআই সহকারী।\n"
            "অপ্রয়োজনীয় কোনো কথা বা ভূমিকা বলবে না। যা জিজ্ঞেস করা হয়েছে শুধু টু-দ্য-পয়েন্ট উত্তর দাও।\n"
            f"🔒 লকড স্ট্র্যাটেজি:\n{strategies or 'নেই'}\n"
            f"🌐 লাইভ নিউজ:\n{live_search_data or 'নেই'}"
        )
        prompt = user_text if user_text else "এই চার্টের টেকনিক্যাল অ্যানালাইসিস করো।"
        try:
            reply = rotator.generate_content(prompt=prompt, image_bytes=image_bytes, system_instruction=strict_instruction)
            if len(reply) > 1900:
                chunks = [reply[i:i+1900] for i in range(0, len(reply), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(reply)
        except Exception as e:
            await message.reply(f"ত্রুটি: {str(e)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
