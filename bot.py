import os
import re
import json
import aiohttp
from PIL import Image, ImageDraw
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= ⚙️ အခြေခံ အချက်အလက်များ =================
API_ID = int(os.getenv("API_ID", "38481104"))
API_HASH = os.getenv("API_HASH", "3c7752a29b4cc0ec9daf6e1782c0b4e2")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8967281657:AAESW-r4v_OOc-jcJzSi4PL9Figkaftn4_A")

# 👑 Grok API Key အသစ် (ဒီနေရာမှာ သင့် Key ကိုထည့်ပါ)
GROK_API_KEY = os.getenv("GROK_API_KEY", "xai-သင့်ရဲ့-api-key-အစစ်ကို-ဒီမှာ-ထည့်ပါ")

# 👑 သင့်ရဲ့ Telegram Username (Admin)
ADMIN_ID = os.getenv("ADMIN_ID", "waiyanphyo99")

MY_LOGO_FILE = "my_logo.png"
DB_FILE = "channels.json"

# ================= 🗂 Database (JSON) စနစ် =================
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {"sources": [], "targets": []}
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"sources": [], "targets": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================================================================

app = Client("advanced_movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

# (၂) 🤖 AI ဇာတ်လမ်းအကျဉ်း (Grok API သို့ ပြောင်းလဲထားသည်)
async def generate_ai_summary(text):
    if not text: return ""
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    prompt = (
        f"Analyze this movie description: '{text}'.\n"
        "Write a short, engaging movie summary in Myanmar (Burmese) language. "
        "Remove all promotional links, ads, and other channel usernames. "
        "Keep it concise and output ONLY the summary text."
    )
    
    data = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": "You are a helpful movie summary assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    print(f"Grok API Error: {resp.status}")
    except Exception as e: 
        print(f"Request Error: {e}")
        pass
        
    # AI Error ဖြစ်ပါက မူလစာသားထဲမှ Links များသာ ဖျက်ပေးမည်
    clean_text = re.sub(r'http[s]?://\S+', '', text)
    return re.sub(r'@\S+', '', clean_text).strip()

# (၃) 🎛 ခလုတ်များ
def get_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Main Channel ကို Join ရန်", url="https://t.me/yourmainchannel")],
        [InlineKeyboardButton("💬 Group", url="https://t.me/yourgroup"), InlineKeyboardButton("📥 Download", url="https://t.me/yourdownloadlink")]
    ])

# ================= 🤖 Handlers =================

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "မင်္ဂလာပါ! ကျွန်တော်က Movie Bot ဖြစ်ပါတယ်။\n\n"
        "Admin များအတွက် Commands များ:\n"
        "/add_source @channel - Source channel ထည့်ရန်\n"
        "/add_target @channel - Target channel ထည့်ရန်\n"
        "/list - လက်ရှိ channel များကြည့်ရန်",
        reply_markup=get_buttons()
    )

@app.on_message(filters.command("add_source") & filters.user(ADMIN_ID))
async def add_source(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /add_source @channel")
    channel = message.command[1]
    db = load_db()
    if channel not in db["sources"]:
        db["sources"].append(channel)
        save_db(db)
        await message.reply(f"Added {channel} to sources.")
    else:
        await message.reply("Already in sources.")

@app.on_message(filters.command("add_target") & filters.user(ADMIN_ID))
async def add_target(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /add_target @channel")
    channel = message.command[1]
    db = load_db()
    if channel not in db["targets"]:
        db["targets"].append(channel)
        save_db(db)
        await message.reply(f"Added {channel} to targets.")
    else:
        await message.reply("Already in targets.")

@app.on_message(filters.command("list") & filters.user(ADMIN_ID))
async def list_channels(client, message):
    db = load_db()
    text = f"Sources: {', '.join(db['sources'])}\nTargets: {', '.join(db['targets'])}"
    await message.reply(text)

# Auto Forward and Process
@app.on_message(filters.photo)
async def process_movie(client, message):
    db = load_db()
    # Check if message is from source channel
    if message.chat and message.chat.username:
        username = "@" + message.chat.username
        if username in db["sources"]:
            # Process AI Summary
            caption = message.caption or ""
            summary = await generate_ai_summary(caption)
            
            # Process Logo
            photo = await message.download()
            output_photo = "output_" + photo
            replace_logo(photo, MY_LOGO_FILE, output_photo)
            
            # Forward to all targets
            for target in db["targets"]:
                try:
                    await client.send_photo(
                        chat_id=target,
                        photo=output_photo,
                        caption=summary,
                        reply_markup=get_buttons()
                    )
                except Exception as e:
                    print(f"Forward Error: {e}")
            
            # Cleanup
            if os.path.exists(photo): os.remove(photo)
            if os.path.exists(output_photo): os.remove(output_photo)

# Start Bot
if __name__ == "__main__":
    print("Bot is starting with Grok API...")
    app.run()
