import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from openai import OpenAI  # OpenAI library ကို သုံးပြီး Grok နဲ့ ချိတ်ပါမည်

# ==========================================
# 1. Server အတု
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Grok Movie Bot is Running!")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# ==========================================
# 2. Configuration & Grok Setup
# ==========================================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

app = Client("ai_movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Grok (x.ai) API ကို ချိတ်ဆက်ခြင်း
client_xai = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

DATA_FILE = "bot_data.json"
user_sessions = {}

# (load_target, save_target function များ အရင်အတိုင်းထားပါ)
def load_target():
    if not os.path.exists(DATA_FILE): return None
    try:
        with open(DATA_FILE, "r") as f: return json.load(f).get("target_channel")
    except: return None

def save_target(channel):
    with open(DATA_FILE, "w") as f: json.dump({"target_channel": channel}, f)

# ==========================================
# 3. Bot Commands & Workflow (အရင်အတိုင်း)
# ==========================================
# /start, /set_channel, /create, /done function များ အားလုံး အရင်အတိုင်းပဲထားပါ
# အောက်ပါ finish_and_post function ထဲက AI ခေါ်တဲ့အပိုင်းကိုသာ ပြင်ပါမည်

@app.on_message(filters.command("done") & filters.private)
async def finish_and_post(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions: return await message.reply("⚠️ လုပ်ဆောင်ဆဲ Post မရှိပါ။")
    
    target_channel = load_target()
    session = user_sessions[user_id]
    
    status_msg = await message.reply("⏳ Grok AI ဖြင့် ဇာတ်ညွှန်းရေးဆွဲကာ တင်နေပါသည်...")

    try:
        video_links = []
        for i, vid_msg_id in enumerate(session["video_msgs"]):
            sent_vid = await client.copy_message(chat_id=target_channel, from_chat_id=user_id, message_id=vid_msg_id)
            video_links.append(f"အပိုင်း ({i+1}) - 🔗 {sent_vid.link}")
            await asyncio.sleep(2)

        formatted_links = "\n".join(video_links)

        # Grok AI ကို ဇာတ်ညွှန်းရေးခိုင်းခြင်း
        prompt = f"Write a movie post in Burmese for '{session['movie_name']}'. Use <blockquote> for summary and links. Keep it short and engaging."
        
        # Grok API Call
        completion = client_xai.chat.completions.create(
            model="grok-beta", # x.ai ရဲ့ model နာမည်
            messages=[
                {"role": "system", "content": "You are a helpful movie channel bot assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_caption = completion.choices[0].message.content

        # Channel သို့ ပို့ခြင်း
        await client.send_photo(chat_id=target_channel, photo=session["photo_id"], caption=ai_caption, parse_mode=ParseMode.HTML)
        del user_sessions[user_id]
        await status_msg.edit_text("✅ Grok AI ဖြင့် အောင်မြင်စွာ တင်ပြီးပါပြီ!")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")

# အခြား function များ (start, set_channel, create, handle_photo, handle_video) ကို အရင် Code အတိုင်းပဲ အကုန်ထည့်ပါ
print("🚀 Grok AI Movie Bot is starting...")
app.run()
