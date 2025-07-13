from pyrogram import Client, filters
import requests, time, random, string, asyncio
from fastapi import FastAPI
import uvicorn
import threading

# Telegram Bot Config
API_ID = 21601817
API_HASH = "8d0fe8b5ae8149455681681253b2ef17"
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

app = Client("classplus_token_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# FastAPI app
web = FastAPI()

# Web route
@web.get("/")
async def home():
    return {"status": "🟢 Bot is Running", "message": "Use /gettoken email@1secmail.com on Telegram"}

# Temp email functions
def get_username(email): return email.split("@")[0]

def get_messages(username):
    try:
        return requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain=1secmail.com").json()
    except: return []

def read_message(username, msg_id):
    try:
        return requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain=1secmail.com&id={msg_id}").json().get("body", "")
    except: return ""

# Telegram Bot Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Welcome to Classplus Token Bot!\nSend /gettoken your_email@1secmail.com to begin.")

@app.on_message(filters.command("gettoken"))
async def get_token(client, message):
    try:
        parts = message.text.strip().split(" ")
        if len(parts) != 2 or "@1secmail.com" not in parts[1]:
            await message.reply_text("❌ Use: `/gettoken your_email@1secmail.com`")
            return

        email = parts[1]
        username = get_username(email)
        await message.reply_text(f"📨 Login using `{email}`\n⏳ Waiting for OTP...")

        otp = None
        for _ in range(30):
            for msg in get_messages(username):
                if "OTP" in msg["subject"] or "Login" in msg["subject"]:
                    otp = ''.join(filter(str.isdigit, read_message(username, msg["id"])))
                    break
            if otp: break
            time.sleep(2)

        if not otp:
            await message.reply_text("❌ OTP not received.")
            return

        await message.reply_text(f"✅ OTP: `{otp}`\n🔐 Generating token...")

        res = requests.post("https://api.classplusapp.com/v2/user/loginWithEmail", json={
            "deviceId": ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
            "otp": otp,
            "email": email
        }, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})

        token = res.json().get("data", {}).get("token")
        if token:
            await message.reply_text(f"🔓 Your Token:\n\n`{token}`")
        else:
            await message.reply_text("❌ Token not found.")

    except Exception as e:
        await message.reply_text(f"⚠️ Error: `{e}`")

# Run Telegram bot in thread
def run_bot():
    app.run()

# Run FastAPI web server
def run_web():
    uvicorn.run(web, host="0.0.0.0", port=8000)

# Start both
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_web()