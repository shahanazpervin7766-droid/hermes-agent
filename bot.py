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

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Environment Variables ভিত্তিক Gemini Key Rotator
rotator = KeyRotator(
    openrouter_key=OPENROUTER_API_KEY
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BASE_CLIENTS_DIR = "./clients"

# ইন-মেমোরি মেমোরি ক্যাশ (VPS স্টোরেজ খরচ = 0 MB)
discord_memory_cache = []

# ডিসকর্ড মেমোরি চ্যানেল নাম (বট এই চ্যানেলকে ক্লাউড ব্রেন বানাবে)
MEMORY_CHANNEL_NAME = "bullders-brain"

# ক্লায়েন্ট ফাইল পড়ার মেথড
def read_client_documents(client_name: str) -> str:
    client_dir = os.path.join(BASE_CLIENTS_DIR, client_name)
    if not os.path.exists(client_dir):
        return ""

    combined_text = ""
    for file_path in glob.glob(os.path.join(client_dir, "**/*.*"), recursive=True):
        ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        try:
            if ext in [".txt", ".md", ".json", ".csv"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    combined_text += f"\n--- File: {file_name} ---\n" + f.read()
            elif ext == ".pdf":
                reader = PdfReader(file_path)
                combined_text += f"\n--- File: {file_name} (PDF) ---\n" + "\n".join([p.extract_text() or "" for p in reader.pages])
            elif ext == ".docx":
                doc = Document(file_path)
                combined_text += f"\n--- File: {file_name} (DOCX) ---\n" + "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"File read error: {e}")
    return combined_text

# ডিসকর্ড থেকে পার্মানেন্ট মেমোরি রিড করার ফাংশন
async def get_discord_memory(guild: discord.Guild) -> str:
    if not guild:
        return "\n".join(discord_memory_cache[-15:])

    # মেমোরি চ্যানেল খোঁজা
    mem_channel = discord.utils.get(guild.text_channels, name=MEMORY_CHANNEL_NAME)
    if not mem_channel:
        return "\n".join(discord_memory_cache[-15:])

    try:
        memories = []
        async for msg in mem_channel.history(limit=50):
            if msg.content.startswith("🧠 [MEMORY]:"):
                memories.append(msg.content.replace("🧠 [MEMORY]:", "").strip())
        return "\n".join(reversed(memories))
    except Exception as e:
        print(f"Memory channel fetch error: {e}")
        return "\n".join(discord_memory_cache[-15:])

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🐂 BullDers Trading AI Online as {bot.user}", flush=True)

    # মেমোরি চ্যানেল না থাকলে স্বয়ংক্রিয়ভাবে তৈরি করে নেওয়া
    for guild in bot.guilds:
        mem_channel = discord.utils.get(guild.text_channels, name=MEMORY_CHANNEL_NAME)
        if not mem_channel:
            try:
                # এডমিন/বট চ্যানেল ক্রিয়েশন
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                await guild.create_text_channel(MEMORY_CHANNEL_NAME, overwrites=overwrites, topic="BullDers Cloud Memory Bank")
                print(f"Created dedicated memory channel #{MEMORY_CHANNEL_NAME} in {guild.name}")
            except Exception as e:
                print(f"Could not auto-create memory channel: {e}")

# মেসেজ হ্যান্ডলার (অন-স্ক্রিন চ্যাট এবং চার্ট ইমেজ এনালাইসিস)
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # যদি মেমোরি চ্যানেলে কিছু আসে, প্রসেস না করা
    if message.channel.name == MEMORY_CHANNEL_NAME:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user.mentioned_in(message)

    if is_dm or is_mentioned or not message.guild:
        user_text = message.clean_content.replace(f"@{bot.user.name}", "").strip()
        
        # ছবি/চার্ট আপলোড করা হয়েছে কি না চেক
        image_bytes = None
        if message.attachments:
            for att in message.attachments:
                if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                    try:
                        image_bytes = await att.read()
                        break
                    except Exception as e:
                        print(f"Image read error: {e}")

        if not user_text and not image_bytes:
            return

        async with message.channel.typing():
            # ডিসকর্ড মেমোরি পড়া
            memory_rules = await get_discord_memory(message.guild)
            
            system_instruction = (
                "তুমি 'বুলডার্স' (BullDers) — একজন প্রফেশনাল, ধারালো এবং বিশ্বস্ত এআই ট্রেডিং মেন্টর ও রিস্ক ম্যানেজার। "
                "ব্যবহারকারী একজন ট্রেডার। তার শেখানো স্ট্র্যাটেজি ও নিয়মের ভিত্তিতে সব সময় প্রফেশনাল উত্তর দাও। "
                "ট্রেডিং সাইকোলজি, রিস্ক-রিওয়ার্ড (RR), টেকনিক্যাল চার্ট প্যাটার্ন এবং ডিসিপ্লিন বজায় রাখতে সাহায্য করো।\n\n"
                f"🧠 ব্যবহারকারীর স্থায়ী স্ট্র্যাটেজি ও মেমোরি রুলস:\n{memory_rules or 'এখনও কোনো বিশেষ রুল সেভ করা নেই।'}"
            )

            prompt = user_text if user_text else "এই চার্টের টেকনিক্যাল অ্যানালাইসিস করো। ট্রেন্ড, কী-লেভেল এবং এন্ট্রি লজিক ব্যাখ্যা করো।"
            
            try:
                reply = rotator.generate_content(
                    prompt=prompt,
                    image_bytes=image_bytes,
                    system_instruction=system_instruction
                )

                # ইন-মেমোরি ক্যাশে যোগ করা
                discord_memory_cache.append(f"User: {prompt[:100]} | BullDers: {reply[:100]}")

                if len(reply) > 1900:
                    chunks = [reply[i:i+1900] for i in range(0, len(reply), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(reply)
            except Exception as e:
                await message.reply(f"❌ এরর: {str(e)}")

    await bot.process_commands(message)

# ১. মেমোরি শেখানোর স্ল্যাশ কমান্ড: /remember
@bot.tree.command(name="remember", description="বুলডার্সকে আপনার কোনো ট্রেডিং স্ট্র্যাটেজি বা নিয়ম আজীবনের জন্য মনে রাখতে বলুন")
@app_commands.describe(rule="যে নিয়ম বা স্ট্র্যাটেজিটি বুলডার্স আজীবন মনে রাখবে")
async def remember(interaction: discord.Interaction, rule: str):
    await interaction.response.defer()

    # মেমোরি চ্যানেলে সেভ করা (VPS-এ ০ মেগাবাইট ডিস্ক খরচ)
    saved_to_channel = False
    if interaction.guild:
        mem_channel = discord.utils.get(interaction.guild.text_channels, name=MEMORY_CHANNEL_NAME)
        if not mem_channel:
            try:
                mem_channel = await interaction.guild.create_text_channel(MEMORY_CHANNEL_NAME)
            except:
                pass
        
        if mem_channel:
            await mem_channel.send(f"🧠 [MEMORY]: {rule}")
            saved_to_channel = True

    discord_memory_cache.append(f"Rule: {rule}")
    await interaction.followup.send(f"✅ **বুলডার্স মনে রেখেছে:**\n> {rule}\n\n*(ডিসকর্ড ক্লাউড মেমোরিতে নিরাপদে সংরক্ষিত হয়েছে)*")

# ২. চার্ট এনালাইসিস স্ল্যাশ কমান্ড: /analyze
@bot.tree.command(name="analyze", description="ট্রেডিং চার্ট এনালাইসিস করুন (ছবি আপলোড করুন)")
@app_commands.describe(chart="চার্টের স্ক্রিনশট ছবি", notes="অতিরিক্ত কোনো প্রশ্ন বা নোটস")
async def analyze(interaction: discord.Interaction, chart: discord.Attachment, notes: str = ""):
    await interaction.response.defer()

    if not any(chart.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        await interaction.followup.send("⚠️ অনুগ্রহ করে একটি সঠিক ইমেজ ফাইল (.png, .jpg) আপলোড করুন।")
        return

    try:
        img_bytes = await chart.read()
        memory_rules = await get_discord_memory(interaction.guild)

        system_instruction = (
            "তুমি 'বুলডার্স' — একজন হাইলি এক্সপেরিয়েন্সড ট্রেডিং টেকনিক্যাল এনালাইসিস এআই। "
            "চার্টটি নিখুঁতভাবে পর্যবেক্ষণ করো: ট্রেন্ড, সাপোর্ট/রেজিস্ট্যান্স লেভেল, লিকুইডিটি, ক্যান্ডেলস্টিক প্যাটার্ন এবং রিস্ক-রিওয়ার্ড। "
            f"\n🧠 ট্রেডারের পার্সোনাল স্ট্র্যাটেজি রুলস:\n{memory_rules}"
        )

        prompt = f"চার্টটি পুঙ্খানুপুঙ্খ এনালাইসিস করে এন্ট্রি, স্টপলস (SL) এবং পটেনশিয়াল টার্গেট (TP) এর মতামত দাও। নোটস: {notes}"
        analysis = rotator.generate_content(prompt=prompt, image_bytes=img_bytes, system_instruction=system_instruction)

        if len(analysis) > 1900:
            chunks = [analysis[i:i+1900] for i in range(0, len(analysis), 1900)]
            await interaction.followup.send(f"📊 **BullDers Chart Analysis:**\n")
            for chunk in chunks:
                await interaction.channel.send(chunk)
        else:
            await interaction.followup.send(f"📊 **BullDers Chart Analysis:**\n\n{analysis}")
    except Exception as e:
        await interaction.followup.send(f"❌ চার্ট এনালাইসিসে এরর: {str(e)}")

# ৩. ক্লায়েন্ট ফাইল পড়ার স্ল্যাশ কমান্ড: /ask
@bot.tree.command(name="ask", description="ক্লায়েন্টের ডকুমেন্ট পড়ে উত্তর দিন")
@app_commands.describe(client="ক্লায়েন্ট ফোল্ডারের নাম", question="আপনার প্রশ্ন")
async def ask(interaction: discord.Interaction, client: str, question: str):
    await interaction.response.defer()
    client_name = client.strip().lower()
    docs = read_client_documents(client_name)
    if not docs:
        await interaction.followup.send(f"⚠️ `{client_name}` ফোল্ডারে কোনো ডকুমেন্ট পাওয়া যায়নি।")
        return

    sys_inst = f"তুমি বুলডার্স। ক্লায়েন্টের এই তথ্যের ভিত্তিতে উত্তর দাও:\n{docs}"
    ans = rotator.generate_content(prompt=question, system_instruction=sys_inst)
    await interaction.followup.send(f"**প্রশ্ন:** {question}\n\n{ans}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
