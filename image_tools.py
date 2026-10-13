import io
from PIL import Image, ImageEnhance, ImageOps

def process_image_command(image_bytes: bytes, command: str):
    """
    ব্যবহারকারী ছবিতে কোনো পরিবর্তন করতে বললে (যেমন: সবুজ করা, উজ্জ্বল করা, সাদা-কালো করা)
    এটি কোড দিয়ে ছবির ওপর পরিবর্তন এনে নতুন ছবি তৈরি করে।
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        cmd = command.lower()

        # ১. সবুজ ফিল্টার / গ্রিন টিন্ট (যেমন: হালকা সবুজ করো)
        if any(w in cmd for w in ["green", "সবুজ", "halka green"]):
            overlay = Image.new("RGBA", img.size, (34, 197, 94, 80)) # Light Green tint with alpha
            img = Image.alpha_composite(img, overlay)

        # ২. সাদা-কালো (Black & White / Grayscale)
        elif any(w in cmd for w in ["black and white", "bw", "সাদা কালো", "grayscale"]):
            img = ImageOps.grayscale(img).convert("RGBA")

        # ৩. ব্রাইটনেস বৃদ্ধি (Brighten)
        elif any(w in cmd for w in ["bright", "উজ্জ্বল", "আলো"]):
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.4)

        # ৪. কনট্রাস্ট বৃদ্ধি
        elif any(w in cmd for w in ["contrast", "কনট্রাস্ট"]):
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)

        # আউটপুট বাইটস
        out_io = io.BytesIO()
        img.save(out_io, format="PNG")
        out_io.seek(0)
        return out_io
    except Exception as e:
        print(f"Image processing error: {e}")
        return None
