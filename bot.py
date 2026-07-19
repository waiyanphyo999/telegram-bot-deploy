import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI

# ==========================================
# 1. Server အတု
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Grok AI Movie Bot is Running!")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# ==========================================
# 2. Configuration & Setup
# ==========================================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

app = Client("ai_movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
client_xai = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

DATA_FILE = "bot_data.json"
user_sessions = {}

# Utility functions
def load_target():
    if not os.path.exists(DATA_FILE): return None
    try:
        with open(DATA_FILE, "r") as f: return json.load(f).get("target_channel")
    except: return None

def save_target(channel):
    with open(DATA_FILE, "w") as f: json.dump({"target_channel": channel}, f)

# ==========================================
# 3. ခလုတ်များပါသော UI
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Channel သတ်မှတ်ရန်", callback_data="cmd_set")],
        [InlineKeyboardButton("🎬 ဇာတ်ကားတင်ရန်", callback_data="cmd_create")],
        [InlineKeyboardButton("✅ ပို့စ်တင်မည် (/done)", callback_data="cmd_done")]
    ])
    await message.reply("🎬 **Grok AI Movie Bot**\n\nခလုတ်များကိုနှိပ်၍ အသုံးပြုနိုင်ပါသည်။", reply_markup=keyboard)

@app.on_callback_query()
async def callback_handler(client, query):
    if query.data == "cmd_set":
        await query.message.reply("ကျေးဇူးပြု၍ `/set_channel @channel_name` ဟု ရိုက်ပေးပါ။")
    elif query.data == "cmd_create":
        await query.message.reply("ကျေးဇူးပြု၍ `/create ဇာတ်ကားနာမည်` ဟု ရိုက်ပေးပါ။")
    elif query.data == "cmd_done":
        await query.message.reply("ဗီဒီယိုများပို့ပြီးပါက `/done` ဟု ရိုက်ပေးပါ။")
    await query.answer()

# ==========================================
# 4. Commands လုပ်ဆောင်ချက်များ
# ==========================================
@app.on_message(filters.command("set_channel") & filters.private)
async def set_channel_cmd(client, message):
    if len(message.command) < 2: return await message.reply("ဥပမာ - `/set_channel @my_movies`")
    save_target(message.command[1])
    await message.reply(f"✅ Target Channel အား {message.command[1]} သို့ သတ်မှတ်ပြီးပါပြီ။")

@app.on_message(filters.command("create") & filters.private)
async def create_post(client, message):
    if len(message.command) < 2: return await message.reply("ဥပမာ - `/create Spider-Man`")
    movie_name = message.text.split(" ", 1)[1]
    user_sessions[message.from_user.id] = {"step": "photo", "movie_name": movie_name, "photo_id": None, "video_msgs": []}
    await message.reply(f"✅ **{movie_name}** အတွက် စတင်ပါပြီ။\n📸 ဇာတ်ကားပုံ (Photo) ကို ပို့ပေးပါ။")

@app.on_message(filters.photo & filters.private)
async def handle_photo(client, message):
    user_id = message.from_user.id
    if user_id in user_sessions and user_sessions[user_id]["step"] == "photo":
        user_sessions[user_id]["photo_id"] = message.photo.file_id
        user_sessions[user_id]["step"] = "videos"
        await message.reply("✅ ပုံရပါပြီ။ Video များကို တစ်ခုချင်းစီပို့ပေးပါ။ အကုန်ပို့ပြီးရင် `/done` ရိုက်ပါ။")

@app.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id
    if user_id in user_sessions and user_sessions[user_id]["step"] == "videos":
        user_sessions[user_id]["video_msgs"].append(message.id)
        await message.reply(f"✅ Video ({len(user_sessions[user_id]['video_msgs'])}) ခု ရရှိပါပြီ။")

@app.on_message(filters.command("done") & filters.private)
async def finish_and_post(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions: return await message.reply("⚠️ လုပ်ဆောင်ဆဲ Post မရှိပါ။ `/create` ဖြင့် အသစ်စပါ။")
    
    target_channel = load_target()
    if not target_channel: return await message.reply("⚠️ Channel မသတ်မှတ်ရသေးပါ။")

    session = user_sessions[user_id]
    status_msg = await message.reply("⏳ Grok AI ဖြင့် တင်နေပါသည်...")

    try:
        video_links = []
        for i, vid_msg_id in enumerate(session["video_msgs"]):
            sent_vid = await client.copy_message(chat_id=target_channel, from_chat_id=user_id, message_id=vid_msg_id)
            video_links.append(f"အပိုင်း ({i+1}) - 🔗 {sent_vid.link}")
            await asyncio.sleep(2)

        formatted_links = "\n".join(video_links)
        prompt = f"Write a Telegram movie post in Burmese for '{session['movie_name']}'. Include this summary and links. Format with <blockquote> tags: {formatted_links}"
        
        completion = client_xai.chat.completions.create(
            model="grok-beta",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_caption = completion.choices[0].message.content.strip()

        await client.send_photo(chat_id=target_channel, photo=session["photo_id"], caption=ai_caption, parse_mode=ParseMode.HTML)
        del user_sessions[user_id]
        await status_msg.edit_text("✅ အောင်မြင်စွာ တင်ပြီးပါပြီ!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")

print("🚀 Grok AI Movie Bot is starting...")
app.run()
