import urllib.parse
import io
import requests

def generate_ai_image(prompt: str) -> io.BytesIO:
    """
    Pollinations AI ইঞ্জিন দিয়ে যেকোনো প্রম্পটের ওপর ভিত্তি করে 
    সম্পূর্ণ নতুন এবং হাই-রেজুলেশন এআই ছবি ফ্রিতে জেনারেট করে মেমোরিতে রিটার্ন করে।
    কোনো পেইড API Key লাগে না, আনলিমিটেড ফ্রি।
    """
    try:
        encoded_prompt = urllib.parse.quote(prompt.strip())
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            buffer = io.BytesIO(response.content)
            buffer.seek(0)
            return buffer
        else:
            print(f"Image generation failed with status {response.status_code}")
            return None
    except Exception as e:
        print(f"Image generation exception: {e}")
        return None
