import asyncio
# Render တွင် Event Loop Error မတက်စေရန် ဖြေရှင်းချက်
asyncio.set_event_loop(asyncio.new_event_loop())

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from PIL import Image

# ==========================================
# 1. Render အား လှည့်စားရန် Web Server အတု
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Movie Bot is alive and running!")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# ==========================================
# 2. Configuration & Admin 
# ==========================================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

ADMIN_USERNAME = "waiyanphyo99" 
CHANNELS_FILE = "channels.json"

app = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
admin_filter = filters.user(ADMIN_USERNAME)

# ==========================================
# 3. Channel များကို သိမ်းဆည်းရန် Helper Functions
# ==========================================
def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ==========================================
# 4. Logo ပေါင်းထည့်သည့် Function (Watermark)
# ==========================================
def add_logo(input_image_path, output_image_path, logo_path="logo.png"):
    try:
        base_image = Image.open(input_image_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")

        # Logo အရွယ်အစားကို မူရင်းပုံ၏ ၂၅% ခန့်ထားရန် ပြင်ဆင်ခြင်း
        logo_width = int(base_image.width * 0.25)
        logo_ratio = logo_width / logo.width
        logo_height = int(logo.height * logo_ratio)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # Logo ထားမည့်နေရာ (ညာဘက် အောက်ထောင့်တွင် သူများ Logo ကို ဖုံးရန်)
        position = (base_image.width - logo_width - 15, base_image.height - logo_height - 15)

        # မူရင်းပုံပေါ်သို့ Logo ကပ်ခြင်း
        transparent = Image.new('RGBA', base_image.size, (0,0,0,0))
        transparent.paste(base_image, (0,0))
        transparent.paste(logo, position, mask=logo)
        
        final_image = transparent.convert("RGB")
        final_image.save(output_image_path, "JPEG")
        return True
    except Exception as e:
        print(f"Logo ကပ်ရာတွင် အမှားတက်နေသည်: {e}")
        return False

# ==========================================
# 5. Bot ၏ အဓိက လုပ်ဆောင်ချက်များ (Commands)
# ==========================================

@app.on_message(filters.command("start") & admin_filter)
async def start_bot(client, message):
    text = (
        "🎬 **Movie Auto-Forward Bot မှ ကြိုဆိုပါသည်!**\n\n"
        "အသုံးပြုနိုင်သော Commands များ -\n"
        "➕ `/add @channel_username` : Channel အသစ်ထည့်ရန်\n"
        "➖ `/remove @channel_username` : Channel ဖြုတ်ရန်\n"
        "🚀 `/forward_movie` : ရုပ်ရှင်ပို့ရန် (ရုပ်ရှင် Post ကို Reply ပြန်၍ အသုံးပြုပါ)"
    )
    await message.reply(text)

@app.on_message(filters.command("add") & admin_filter)
async def add_channel(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ ကျေးဇူးပြု၍ Channel Username ထည့်ပါ။\nဥပမာ - `/add @my_movie_channel`")
    
    new_channel = message.command[1]
    channels = load_channels()
    
    if new_channel not in channels:
        channels.append(new_channel)
        save_channels(channels)
        await message.reply(f"✅ {new_channel} ကို စာရင်းထဲသို့ အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။")
    else:
        await message.reply(f"⚠️ {new_channel} သည် စာရင်းထဲတွင် ရှိပြီးသား ဖြစ်ပါသည်။")

@app.on_message(filters.command("remove") & admin_filter)
async def remove_channel(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ ကျေးဇူးပြု၍ ဖယ်ထုတ်လိုသော Channel Username ထည့်ပါ။\nဥပမာ - `/remove @my_movie_channel`")
    
    remove_ch = message.command[1]
    channels = load_channels()
    
    if remove_ch in channels:
        channels.remove(remove_ch)
        save_channels(channels)
        await message.reply(f"🗑 {remove_ch} ကို စာရင်းမှ ဖယ်ထုတ်ပြီးပါပြီ။")
    else:
        await message.reply(f"⚠️ {remove_ch} သည် စာရင်းထဲတွင် မရှိပါ။")

@app.on_message(filters.command("forward_movie") & admin_filter)
async def forward_movie(client, message):
    if not message.reply_to_message:
        return await message.reply("⚠️ ပေးပို့လိုသော ရုပ်ရှင် Post ကို **Reply ပြန်ပြီးမှ** `/forward_movie` ဟု ရိုက်ပါ။")

    channels = load_channels()
    if not channels:
        return await message.reply("⚠️ Channel စာရင်း အလွတ်ဖြစ်နေပါသည်။ အရင်ဆုံး `/add` ဖြင့် Channel များ ထည့်ပါ။")

    status_msg = await message.reply(f"🚀 Channel စုစုပေါင်း **{len(channels)}** ခုသို့ စတင် ပေးပို့နေပါပြီ...\n(ဓာတ်ပုံဖြစ်ပါက Logo အစားထိုးနေပါသည်)")
    target_msg = message.reply_to_message
    
    success = 0
    failed = 0

    # ဓာတ်ပုံဖြစ်ပါက Logo ကပ်မည်
    if target_msg.photo:
        downloaded_file = await target_msg.download()
        output_file = "watermarked.jpg"
        
        if os.path.exists("logo.png"):
            has_logo = add_logo(downloaded_file, output_file, "logo.png")
            file_to_send = output_file if has_logo else downloaded_file
        else:
            file_to_send = downloaded_file

        for channel in channels:
            try:
                await client.send_photo(
                    chat_id=channel,
                    photo=file_to_send,
                    caption=target_msg.caption if target_msg.caption else ""
                )
                success += 1
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                failed += 1
                
        if os.path.exists(downloaded_file): os.remove(downloaded_file)
        if os.path.exists(output_file): os.remove(output_file)

    # ဗီဒီယို သို့မဟုတ် စာ သီးသန့်ဖြစ်ပါက မူလအတိုင်း Forward လုပ်မည်
    else:
        for channel in channels:
            try:
                await target_msg.copy(chat_id=channel)
                success += 1
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                failed += 1

    await status_msg.edit_text(f"✅ **ပေးပို့ခြင်း ပြီးဆုံးပါပြီ။**\n\nအောင်မြင်: {success} ခု\nမအောင်မြင်: {failed} ခု")

# ==========================================
# 6. Bot ကို စတင် Run ခြင်း
# ==========================================
print("🚀 Movie Bot is starting...")
app.run()
