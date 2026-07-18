import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters

# Server အတု (Render အတွက်)
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# Config
app = Client("movie_bot", 
             api_id=int(os.environ.get("API_ID")), 
             api_hash=os.environ.get("API_HASH"), 
             bot_token=os.environ.get("BOT_TOKEN"))

# စမ်းသပ်ရန်အတွက် admin_filter မပါဘဲ Run ကြည့်မယ်
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ Bot အလုပ်လုပ်နေပါပြီ!")

app.run()
