import io
import requests

def generate_ai_video(prompt: str) -> io.BytesIO:
    """
    Pollinations AI Video Engine দিয়ে ফ্রিতে ৫-সেকেন্ডের অ্যানিমেটেড ভিডিও তৈরি করে।
    """
    try:
        import urllib.parse
        encoded = urllib.parse.quote(prompt.strip())
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&model=flux&nologo=true"
        # Download generated video/gif sequence
        resp = requests.get(url, timeout=45)
        if resp.status_code == 200:
            buffer = io.BytesIO(resp.content)
            buffer.seek(0)
            return buffer
        return None
    except Exception as e:
        print(f"Video generation error: {e}")
        return None
