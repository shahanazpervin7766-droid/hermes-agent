# Discord AI Client Assistant Bot

এই বটটি আপনার VPS-এ চলবে, ডিসকর্ড থেকে কমান্ড নেবে এবং `clients/` ফোল্ডারের ভেতর থাকা নির্দিষ্ট ক্লায়েন্টের ফাইল (PDF, DOCX, TXT) পড়ে Gemini বা Llama (OpenRouter) দিয়ে বাংলায় উত্তর দেবে।

## ফোল্ডার স্ট্রাকচার
```text
.
├── bot.py                  # বটের মূল কোড
├── requirements.txt        # প্রয়োজনীয় লাইব্রেরি
├── .env.example            # Environment variables টেমপ্লেট
├── .gitignore              # সিক্রেট ফাইল গিটহাবে যাওয়া আটকায়
└── clients/
    └── demo_client/        # টেস্ট ক্লায়েন্ট ফোল্ডার
        └── info.txt
```

## সেটআপ ও রান করার নিয়ম:

### ১. লাইব্রেরি ইনস্টল:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ২. Environment Variables সেটআপ:
```bash
cp .env.example .env
nano .env
```
`.env` ফাইলের ভেতর আপনার আসল টোকেন ও এপিআই কি বসিয়ে সেভ করুন।

### ৩. বট রান করা:
```bash
python3 bot.py
```

### ৪. ডিসকর্ড থেকে ব্যবহার:
ডিসকর্ডে গিয়ে টাইপ করুন:
```text
/ask client:demo_client question:ক্লায়েন্টের বাজেট কত?
```
*(মডেল হিসেবে Gemini 1.5 Flash অথবা OpenRouter Llama 3.3 সিলেক্ট করতে পারেন)*
