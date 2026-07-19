import os
import re
import json
import aiohttp
from PIL import Image, ImageDraw
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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

# Admin တွေ ဘာလုပ်နေလဲဆိုတာ မှတ်သားရန်
admin_steps = {}

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
        
    clean_text = re.sub(r'http[s]?://\S+', '', text)
    return re.sub(r'@\S+', '', clean_text).strip()

# (၃) 🎛 User များမြင်ရမည့် Movie ခလုတ်များ
def get_movie_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Main Channel ကို Join ရန်", url="https://t.me/yourmainchannel")],
        [InlineKeyboardButton("💬 Group", url="https://t.me/yourgroup"), InlineKeyboardButton("📥 Download", url="https://t.me/yourdownloadlink")]
    ])

# ================= 🎛 Admin Menu ခလုတ်များ =================
def get_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Source Channel ထည့်ရန်", callback_data="add_source")],
        [InlineKeyboardButton("➕ Target Channel ထည့်ရန်", callback_data="add_target")],
        [InlineKeyboardButton("📊 လက်ရှိ Channels များကြည့်ရန်", callback_data="list_channels")],
        [InlineKeyboardButton("ℹ️ Bot ဘာတွေလုပ်နိုင်လဲ?", callback_data="bot_info")]
    ])

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 နောက်သို့", callback_data="back_to_main")]])


# ================= 🤖 Handlers =================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if message.from_user.username == ADMIN_ID:
        # Admin အနေနဲ့ Start ခေါ်လျှင် ခလုတ်တွေပြမည်
        if message.chat.id in admin_steps:
            del admin_steps[message.chat.id]
            
        await message.reply_text(
            "👋 မင်္ဂလာပါ Admin!\n\nBot ကို အောက်ပါ ခလုတ်များမှ တစ်ဆင့် လွယ်ကူစွာ ထိန်းချုပ်နိုင်ပါသည်။",
            reply_markup=get_admin_menu()
        )
    else:
        # သာမန် User ဆိုလျှင်
        await message.reply_text("မင်္ဂလာပါ! ကျွန်တော်က Movie Channel များအတွက် အထူးပြုလုပ်ထားသော Bot ဖြစ်ပါသည်။")

# ခလုတ်နှိပ်ခြင်းများကို လက်ခံမည့် နေရာ
@app.on_callback_query(filters.user(ADMIN_ID))
async def button_handler(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    
    if data == "add_source":
        admin_steps[chat_id] = "waiting_for_source"
        await callback_query.message.edit_text(
            "📝 **Source Channel ထည့်ရန်**\n\nသင် ဇာတ်ကားများ ကူးယူလိုသော Channel ရဲ့ Username ကို ရိုက်ထည့်ပါ။\n(ဥပမာ - `@my_movies_source`)",
            reply_markup=get_back_button()
        )
        
    elif data == "add_target":
        admin_steps[chat_id] = "waiting_for_target"
        await callback_query.message.edit_text(
            "📝 **Target Channel ထည့်ရန်**\n\nBot ကနေ ဇာတ်ကားတွေ အလိုအလျောက် တင်ပေးရမယ့် Channel ရဲ့ Username ကို ရိုက်ထည့်ပါ။\n(ဥပမာ - `@my_movies_target`)",
            reply_markup=get_back_button()
        )
        
    elif data == "list_channels":
        db = load_db()
        src_list = "\n".join([f"• {c}" for c in db['sources']]) if db['sources'] else "မရှိသေးပါ"
        tgt_list = "\n".join([f"• {c}" for c in db['targets']]) if db['targets'] else "မရှိသေးပါ"
        
        text = f"📊 **လက်ရှိ ချိတ်ဆက်ထားသော Channels များ**\n\n**📥 Source (ယူမည့်နေရာများ):**\n{src_list}\n\n**📤 Target (တင်မည့်နေရာများ):**\n{tgt_list}"
        await callback_query.message.edit_text(text, reply_markup=get_back_button())
        
    elif data == "bot_info":
        info_text = (
            "**🤖 Bot ရဲ့ လုပ်ဆောင်နိုင်စွမ်းများ**\n\n"
            "၁။ **Auto Forward:** Source channel ကနေ Target ကို အလိုအလျောက် ပို့ပေးပါတယ်။\n"
            "၂။ **AI Summary:** Grok AI ကိုသုံးပြီး ဇာတ်လမ်းအကျဉ်းကို မြန်မာလို အလိုအလျောက် ပြန်ရေးပေးပါတယ်။\n"
            "၃။ **Auto Watermark:** မူလ Logo ကို ဖျက်ပြီး သင့်ရဲ့ ကိုယ်ပိုင် Logo နဲ့ အစားထိုးပေးပါတယ်။\n"
            "၄။ **Auto Buttons:** Target ကိုပို့တဲ့အခါ 'Main Channel', 'Group', 'Download' စတဲ့ ခလုတ်တွေ အလိုအလျောက် တပ်ပေးပါတယ်။"
        )
        await callback_query.message.edit_text(info_text, reply_markup=get_back_button())
        
    elif data == "back_to_main":
        if chat_id in admin_steps:
            del admin_steps[chat_id]
        await callback_query.message.edit_text(
            "👋 မင်္ဂလာပါ Admin!\n\nBot ကို အောက်ပါ ခလုတ်များမှ တစ်ဆင့် လွယ်ကူစွာ ထိန်းချုပ်နိုင်ပါသည်။",
            reply_markup=get_admin_menu()
        )

# Admin မှ Channel နာမည်များ ရိုက်ထည့်သောအခါ ဖမ်းယူမည့် နေရာ
@app.on_message(filters.text & filters.user(ADMIN_ID) & filters.private)
async def process_admin_input(client, message):
    chat_id = message.chat.id
    
    if chat_id in admin_steps:
        step = admin_steps[chat_id]
        channel_name = message.text.strip()
        
        # @ နဲ့စ/မစ စစ်ဆေးခြင်း
        if not channel_name.startswith("@"):
            await message.reply("⚠️ ကျေးဇူးပြု၍ **@** ဖြင့်စသော Username ကိုသာ ထည့်ပါ။\n(ဥပမာ - `@channelname`)", reply_markup=get_back_button())
            return
            
        db = load_db()
        
        if step == "waiting_for_source":
            if channel_name not in db["sources"]:
                db["sources"].append(channel_name)
                save_db(db)
                await message.reply(f"✅ **{channel_name}** ကို Source အဖြစ် အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။", reply_markup=get_admin_menu())
            else:
                await message.reply("⚠️ ဤ Channel သည် Source စာရင်းထဲတွင် ရှိပြီးသားဖြစ်ပါသည်။", reply_markup=get_admin_menu())
                
        elif step == "waiting_for_target":
            if channel_name not in db["targets"]:
                db["targets"].append(channel_name)
                save_db(db)
                await message.reply(f"✅ **{channel_name}** ကို Target အဖြစ် အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။", reply_markup=get_admin_menu())
            else:
                await message.reply("⚠️ ဤ Channel သည် Target စာရင်းထဲတွင် ရှိပြီးသားဖြစ်ပါသည်။", reply_markup=get_admin_menu())
                
        # အဆင့်ပြီးဆုံးသွားသဖြင့် မှတ်သားထားတာကို ဖျက်မည်
        del admin_steps[chat_id]

# ================= Auto Forward & Process လုပ်မည့်အပိုင်း =================
@app.on_message(filters.photo)
async def process_movie(client, message):
    db = load_db()
    
    if message.chat and message.chat.username:
        username = "@" + message.chat.username
        
        if username in db["sources"]:
            caption = message.caption or ""
            summary = await generate_ai_summary(caption)
            
            photo = await message.download()
            output_photo = "output_" + photo
            replace_logo(photo, MY_LOGO_FILE, output_photo)
            
            for target in db["targets"]:
                try:
                    await client.send_photo(
                        chat_id=target,
                        photo=output_photo,
                        caption=summary,
                        reply_markup=get_movie_buttons()
                    )
                except Exception as e:
                    print(f"Forward Error to {target}: {e}")
            
            # ပုံများကို ဖျက်ပစ်မည်
            if os.path.exists(photo): os.remove(photo)
            if os.path.exists(output_photo): os.remove(output_photo)

# Start Bot
if __name__ == "__main__":
    print("Bot is starting with Interactive Buttons...")
    # အရင်က app.run() နေရာကို ဖျက်ပြီး အောက်ပါအတိုင်း ပြင်ပါ
from pyrogram import idle

async def main():
    await app.start()
    print("Bot is running...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

