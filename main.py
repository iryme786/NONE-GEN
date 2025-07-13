from pyrogram import Client, filters
from fastapi import FastAPI
import uvicorn
import threading
import requests, time, random, string
import os

# 🔐 Using environment variables for token and credentials
API_ID = int(os.environ.get("API_ID", "21601817"))
API_HASH = os.environ.get("API_HASH", "8d0fe8b5ae8149455681681253b2ef17")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("classplus_token_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
web = FastAPI()

# Healthcheck route
@web.get("/")
async def root():
    return {"status": "✅ Bot is running", "bot": "Classplus Token Bot"}

# Telegram handlers
@bot.on_message(filters.command("start"))
async def handle_start(client, message):
    await message.reply_text("👋 Welcome to Classplus Token Bot!\nSend /gettoken your_email@1secmail.com")

@bot.on_message(filters.command("gettoken"))
async def handle_gettoken(client, message):
    parts = message.text.strip().split()
    if len(parts) != 2 or "@1secmail.com" not in parts[1]:
        return await message.reply_text("❌ Use `/gettoken your_email@1secmail.com`")
    email = parts[1]
    user = email.split("@")[0]
    await message.reply_text(f"📨 Waiting for OTP on `{email}`...")

    otp = None
    for _ in range(30):
        try:
            msgs = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain=1secmail.com").json()
        except:
            msgs = []
        for m in msgs:
            sub = m.get("subject", "")
            if "OTP" in sub or "Login" in sub:
                body = requests.get(
                    f"https://www.1secmail.com/api/v1/?action=readMessage&login={user}&domain=1secmail.com&id={m['id']}"
                ).json().get("body", "")
                otp = ''.join(filter(str.isdigit, body))
                break
        if otp:
            break
        time.sleep(2)

    if not otp:
        return await message.reply_text("❌ OTP not received. Try again.")
    await message.reply_text(f"✅ OTP received: `{otp}`\n🔐 Generating token...")

    payload = {
        "deviceId": ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
        "otp": otp,
        "email": email
    }
    headers = {"Content-Type": "application/json"}
    res = requests.post("https://api.classplusapp.com/v2/user/loginWithEmail", json=payload, headers=headers)
    token = res.json().get("data", {}).get("token")

    if token:
        await message.reply_text(f"🎉 Here is your token:\n`{token}`")
    else:
        await message.reply_text("❌ Token not found. OTP expired or invalid.")

def run_web():
    uvicorn.run(web, host="0.0.0.0", port=8000)

def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_web()
