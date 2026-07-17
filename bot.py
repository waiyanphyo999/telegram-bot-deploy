import asyncio
import os

# Python Version မြင့်ရင် တက်တတ်တဲ့ စက်ဝိုင်း Error ကို ပြင်ဆင်ခြင်း
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import re
import json
import aiohttp
# ... ကျန်တဲ့ ကူးထားတဲ့ စာကြောင်းတွေ ဒီအတိုင်း ဆက်ထားပါ ...

from aiohttp import web
from PIL import Image, ImageDraw
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= ⚙️ အခြေခံ အချက်အလက်များ =================
import os

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_ID = os.getenv("ADMIN_ID", "waiyanphyo99")
MY_LOGO_FILE = "1000044099.png"

# ================= 🗂 Database (JSON) စနစ် =================
DB_FILE = "channels.json"

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {"sources": [], "targets": []}
        save_db(default_data)
        return default_data
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Dynamic Source Filter
async def is_source(_, __, message):
    if not message.chat or not message.chat.username: return False
    db = load_db()
    return message.chat.username in [s.replace("@", "") for s in db["sources"]]

source_filter = filters.create(is_source)

# =========================================================================

app = Client("advanced_movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

current_target_index = 0
last_media_group_id = None

# (၁) 🖼 Logo ပြောင်းမည့်စနစ်
def replace_logo(photo_path, logo_path, output_path):
    try:
        main_img = Image.open(photo_path).convert("RGBA")
        width, height = main_img.size
        draw = ImageDraw.Draw(main_img)
        box_w = int(width * 0.25)
        box_h = int(height * 0.1)
        x1, y1 = width - box_w - 15, 15
        x2, y2 = width - 15, y1 + box_h
        draw.rectangle([x1, y1, x2, y2], fill=(15, 15, 15, 255))
        
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((box_w - 10, box_h - 10))
            paste_x, paste_y = x1 + (box_w - logo.width) // 2, y1 + (box_h - logo.height) // 2
            main_img.paste(logo, (paste_x, paste_y), logo)
            
        final_img = main_img.convert("RGB")
        final_img.save(output_path)
        return True
    except Exception as e:
        print(f"Logo Error: {e}")
        return False

# (၂) 🤖 AI ဇာတ်လမ်းအကျဉ်း
async def generate_ai_summary(text):
    if not text: return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = (
        f"Analyze this movie description: '{text}'.\n"
        "Write a short, engaging movie summary in Myanmar (Burmese) language. "
        "Remove all promotional links, ads, and other channel usernames. "
        "Keep it concise and output ONLY the summary text."
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except: pass
    clean_text = re.sub(r'http[s]?://\S+', '', text)
    return re.sub(r'@\S+', '', clean_text).strip()

# (၃) 🎛 ခလုတ်များ
def get_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Main Channel ကို Join ရန်", url="https://t.me/yourmainchannel")],
        [InlineKeyboardButton("💬 Group", url="https://t.me/yourgroup"), InlineKeyboardButton("📥 Download", url="https://t.me/yourdownloadlink")]
    ])

# ================= 👑 Admin Control Commands =================# အောက်ပါအတိုင်း 
print(f"DEBUG: API_ID is: {API_ID}")
print(f"DEBUG: BOT_TOKEN is valid: {bool(BOT_TOKEN)}")

app.run()


