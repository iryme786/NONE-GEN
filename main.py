from pyrogram import Client, filters
from pyrogram.types import Message
from fastapi import FastAPI
import uvicorn
import threading
import requests
import random
import string

# ================= TELEGRAM CONFIG ====================
API_ID = 21601817
API_HASH = "8d0fe8b5ae8149455681681253b2ef17"
BOT_TOKEN = "8159627489:AAELW-QwJTInrSd55f5vZQSJvjzZz7zVvkg"

# ============== PYROGRAM BOT INIT ====================
bot = Client("classplus_manual_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_state = {}

# ================= FASTAPI SETUP ======================
web = FastAPI()

@web.get("/")
def home():
    return {"status": "✅ Bot is running", "message": "Use this bot on Telegram."}

# ================= TELEGRAM HANDLERS ==================
@bot.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply("📧 Please enter your email address:")
    user_state[message.from_user.id] = "WAITING_FOR_EMAIL"

@bot.on_message(filters.text & ~filters.command("start"))
async def message_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_state:
        return await message.reply("❗ Type /start to begin.")

    if user_state[user_id] == "WAITING_FOR_EMAIL":
        email = message.text.strip()
        user_state[user_id] = {"step": "WAITING_FOR_OTP", "email": email}
        await message.reply("📩 OTP sent to your email. Please enter the OTP:")

    elif isinstance(user_state[user_id], dict):
        otp = message.text.strip()
        email = user_state[user_id]["email"]
        payload = {
            "deviceId": ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
            "otp": otp,
            "email": email
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        try:
            res = requests.post("https://api.classplusapp.com/v2/user/loginWithEmail", json=payload, headers=headers)
            data = res.json()
            token = data.get("data", {}).get("token")
            if token:
                await message.reply(f"🔐 Access Token:\n`{token}`")
            else:
                await message.reply("❌ Invalid OTP or token not received.")
        except Exception as e:
            await message.reply(f"⚠️ Error: {e}")
        user_state.pop(user_id)

# =============== RUN BOTH SERVICES =====================
def run_bot():
    bot.run()

def run_web():
    uvicorn.run(web, host="0.0.0.0", port=10000)

# Run both concurrently
threading.Thread(target=run_bot).start()
threading.Thread(target=run_web).start()
