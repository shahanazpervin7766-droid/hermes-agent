import os
import glob
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# এনভায়রনমেন্ট ভেরিয়েবল লোড করা (.env ফাইল থেকে)
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini কনফিগারেশন
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# OpenRouter (OpenAI-compatible) কনফিগারেশন
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ডিসকর্ড বট ইনিশিয়ালাইজেশন
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BASE_CLIENTS_DIR = "./clients"

# ক্লায়েন্ট ফোল্ডার থেকে ফাইল পড়ার ফাংশন (PDF, DOCX, TXT, MD ইত্যাদি)
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
                pdf_text = "\n".join([page.extract_text() or "" for page in reader.pages])
                combined_text += f"\n--- File: {file_name} (PDF) ---\n" + pdf_text
            elif ext == ".docx":
                doc = Document(file_path)
                docx_text = "\n".join([p.text for p in doc.paragraphs])
                combined_text += f"\n--- File: {file_name} (DOCX) ---\n" + docx_text
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return combined_text

# AI থেকে উত্তর নেওয়ার ফাংশন
def ask_ai(prompt: str, context: str, model_type: str = "gemini") -> str:
    system_instruction = (
        "তুমি একজন পেশাদার এবং বুদ্ধিমান ব্যক্তিগত এআই সহকারী। "
        "নিচে দেওয়া ক্লায়েন্টের ফাইলগুলোর তথ্যের ভিত্তিতে বাংলায় সুন্দর ও পরিষ্কার উত্তর দাও। "
        "যদি তথ্যে উত্তর না থাকে, তবে বানিয়ে না বলে সরাসরি বলো যে তথ্যে এটি উল্লেখ নেই।\n\n"
        f"ক্লায়েন্ট ডকুমেন্টস:\n{context}"
    )

    if model_type == "openrouter":
        response = openrouter_client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    else:
        # Default: Gemini 1.5 Flash
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ বট সফলভাবে চালু হয়েছে: {bot.user}")

# ডিসকর্ড স্ল্যাশ কমান্ড: /ask
@bot.tree.command(name="ask", description="ক্লায়েন্টের ডকুমেন্ট পড়ে এআই উত্তর দেবে")
@app_commands.describe(
    client="ক্লায়েন্ট ফোল্ডারের নাম (যেমন: demo_client)",
    question="আপনার প্রশ্ন",
    model="মডেল বেছে নিন (gemini অথবা openrouter)"
)
@app_commands.choices(model=[
    app_commands.Choice(name="Gemini 1.5 Flash (Google)", value="gemini"),
    app_commands.Choice(name="Llama 3.3 70B (OpenRouter Free)", value="openrouter")
])
async def ask(interaction: discord.Interaction, client: str, question: str, model: app_commands.Choice[str] = None):
    await interaction.response.defer()

    selected_model = model.value if model else "gemini"
    client_name = client.strip().lower()
    
    docs_text = read_client_documents(client_name)
    if not docs_text:
        await interaction.followup.send(f"⚠️ `{client_name}` নামের কোনো ফোল্ডার বা ফাইল পাওয়া যায়নি `./clients/{client_name}` তে।")
        return

    try:
        answer = ask_ai(question, docs_text, selected_model)
        
        # ডিসকর্ডের ২০০০ অক্ষরের মেসেজ লিমিট হ্যান্ডলিং
        if len(answer) > 1900:
            chunks = [answer[i:i+1900] for i in range(0, len(answer), 1900)]
            await interaction.followup.send(f"**প্রশ্ন:** {question} *(মডেল: {selected_model})*\n")
            for chunk in chunks:
                await interaction.channel.send(chunk)
        else:
            await interaction.followup.send(f"**প্রশ্ন:** {question} *(মডেল: {selected_model})*\n\n{answer}")
    except Exception as e:
        await interaction.followup.send(f"❌ এরর হয়েছে: {str(e)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
