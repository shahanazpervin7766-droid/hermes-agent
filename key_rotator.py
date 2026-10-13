import os
import time
from typing import List, Optional
from google import genai
from openai import OpenAI

class KeyRotator:
    """
    Environment Variables ভিত্তিক Gemini Key Rotator.
    কোনো ফাইলে কি রাখার দরকার নেই! 
    Render এর Environment Variables সেকশনে কমা (,) দিয়ে যত ইচ্ছা কি দিতে পারবেন।
    যেমন: GEMINI_API_KEYS=key1,key2,key3,...
    অথবা GEMINI_API_KEY_1, GEMINI_API_KEY_2...
    """
    def __init__(self, openrouter_key: Optional[str] = None):
        self.openrouter_key = openrouter_key
        self.keys: List[str] = []
        self.current_index = 0
        self.exhausted_keys = set()
        self.last_reset = time.time()
        self.load_keys()

    def load_keys(self):
        self.keys = []
        
        # পদ্ধতি ১: GEMINI_API_KEYS ভেরিয়েবলে কমা দিয়ে সেপারেটেড একাধিক কি (key1,key2,key3,...)
        bulk_keys = os.getenv("GEMINI_API_KEYS", "")
        if bulk_keys:
            for k in bulk_keys.split(","):
                clean_k = k.strip()
                if clean_k and clean_k not in self.keys:
                    self.keys.append(clean_k)

        # পদ্ধতি ২: একক GEMINI_API_KEY
        single_key = os.getenv("GEMINI_API_KEY", "").strip()
        if single_key and single_key not in self.keys:
            self.keys.append(single_key)

        # পদ্ধতি ৩: GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3...
        for env_var, val in os.environ.items():
            if env_var.startswith("GEMINI_API_KEY_"):
                clean_val = val.strip()
                if clean_val and clean_val not in self.keys:
                    self.keys.append(clean_val)

        print(f"🔑 KeyRotator Loaded: {len(self.keys)} Gemini API Keys from Environment Variables.", flush=True)

    def get_active_client(self) -> Optional[genai.Client]:
        if time.time() - self.last_reset > 86400:
            self.exhausted_keys.clear()
            self.last_reset = time.time()

        available_indices = [i for i in range(len(self.keys)) if i not in self.exhausted_keys]
        if not available_indices:
            print("⚠️ All Gemini Keys exhausted! Falling back to OpenRouter free models.", flush=True)
            return None

        for i in range(len(self.keys)):
            idx = (self.current_index + i) % len(self.keys)
            if idx not in self.exhausted_keys:
                self.current_index = idx
                try:
                    return genai.Client(api_key=self.keys[idx])
                except Exception as e:
                    print(f"Error initializing client with key #{idx}: {e}", flush=True)
                    self.exhausted_keys.add(idx)

        return None

    def mark_current_exhausted(self):
        print(f"⚡ Gemini Key #{self.current_index} hit quota/error. Auto-rotating to next key...", flush=True)
        self.exhausted_keys.add(self.current_index)
        self.current_index = (self.current_index + 1) % max(1, len(self.keys))

    def generate_content(self, prompt: str, image_bytes: Optional[bytes] = None, system_instruction: str = "") -> str:
        max_attempts = max(3, len(self.keys))
        for _ in range(max_attempts):
            client = self.get_active_client()
            if not client:
                break

            try:
                contents = []
                if system_instruction:
                    contents.append(f"System: {system_instruction}\n")
                if image_bytes:
                    import io
                    from PIL import Image
                    img = Image.open(io.BytesIO(image_bytes))
                    contents.append(img)
                contents.append(prompt)

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "resource" in err_str or "exhausted" in err_str:
                    self.mark_current_exhausted()
                    continue
                else:
                    print(f"Gemini API request error: {e}", flush=True)
                    self.mark_current_exhausted()
                    continue

        # OpenRouter fallback
        if self.openrouter_key:
            try:
                op_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter_key,
                )
                response = op_client.chat.completions.create(
                    model="openrouter/free",
                    messages=[
                        {"role": "system", "content": system_instruction or "You are BullDers, an expert trading AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
            except Exception as e:
                print(f"OpenRouter backup error: {e}", flush=True)

        return "⚠️ দুঃখিত, এই মুহূর্তে এআই মডেল থেকে উত্তর আনা যাচ্ছে না।"
