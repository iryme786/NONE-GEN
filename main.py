from pyrogram import Client, filters
from pyrogram.types import Message
from fastapi import FastAPI
import uvicorn
import threading
import requests, string, random

# Telegram Bot Config
API_ID = 21601817
API_HASH = "8d0fe8b5ae8149455681681253b2ef17"
BOT_TOKEN = "8159627489:AAELW-QwJTInrSd55f5vZQSJvjzZz7zVvkg"

bot = Client("classplus_token_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
web = FastAPI()
user_state = {}

@bot.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text("📧 Please enter your temp mail:")
    user_state[message.from_user.id] = {"step": "email"}

@bot.on_message(filters.text)
async def handle_message(client, message: Message):
    uid = message.from_user.id
    if uid not in user_state:
        return await message.reply("ℹ️ Please type /start first.")
    
    state = user_state[uid]
    if state["step"] == "email":
        user_state[uid] = {"step": "otp", "email": message.text.strip()}
        await message.reply("📩 OTP sent to your email. Please enter the OTP:")
    
    elif state["step"] == "otp":
        otp = message.text.strip()
        email = state["email"]
        device_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        headers = {
            "User-Agent": "okhttp/3.12.1",
            "Content-Type": "application/json"
        }
        payload = {
            "deviceId": device_id,
            "otp": otp,
            "email": email
        }

        try:
            r = requests.post("https://api.classplusapp.com/v2/user/loginWithEmail", json=payload, headers=headers)
            if r.status_code == 200 and "data" in r.json():
                token = r.json()["data"]["token"]
                await message.reply(f"🟢 <b>Your Token has been Generated :</b>\n<code>{token}</code>", parse_mode="html")
            else:
                await message.reply("❌ Invalid OTP or email.")
        except Exception as e:
            await message.reply(f"⚠️ Error: {str(e)}")
        user_state.pop(uid)

@web.get("/")
def home():
    return {"status": "Bot is running", "message": "Visit me on Telegram!"}

def run():
    bot.run()

threading.Thread(target=run).start()
uvicorn.run(web, host="0.0.0.0", port=8000)