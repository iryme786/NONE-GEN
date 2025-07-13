from pyrogram import Client, filters
import os
import threading
from flask import Flask
import requests, random, string, time

API_ID = 21601817
API_HASH = "8d0fe8b5ae8149455681681253b2ef17"
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("classplus_token_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

web = Flask(__name__)

@web.route('/')
def home():
    return "✅ Telegram Bot is Running!"

def run_web():
    web.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web).start()

def generate_temp_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return name, f"{name}@1secmail.com"

def get_messages(username):
    try:
        resp = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain=1secmail.com")
        return resp.json()
    except:
        return []

def read_message(username, message_id):
    try:
        resp = requests.get(
            f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain=1secmail.com&id={message_id}"
        ).json()
        return resp.get("body", "")
    except:
        return ""

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Welcome to Classplus Token Bot!\nUse /gettoken to begin.")

@app.on_message(filters.command("gettoken"))
async def get_token(client, message):
    name, temp_email = generate_temp_email()
    await message.reply_text(f"📨 Use this email to login on Classplus: `{temp_email}`\n\n⏳ Waiting for OTP...")

    otp = None
    for _ in range(30):
        msgs = get_messages(name)
        for m in msgs:
            if "OTP" in m["subject"] or "Login" in m["subject"]:
                body = read_message(name, m["id"])
                otp = ''.join(filter(str.isdigit, body))
                break
        if otp:
            break
        time.sleep(2)

    if not otp:
        await message.reply_text("❌ OTP not received. Try again.")
        return

    await message.reply_text(f"✅ OTP received: `{otp}`\n\n⏳ Generating token...")

    payload = {
        "deviceId": ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
        "otp": otp,
        "email": temp_email
    }
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    try:
        res = requests.post("https://api.classplusapp.com/v2/user/loginWithEmail",
                            json=payload, headers=headers)
        token = res.json().get("data", {}).get("token")
        if token:
            await message.reply_text(f"🔐 Your Token:\n\n`{token}`")
        else:
            await message.reply_text("❌ Token not found. OTP may be invalid or expired.")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

app.run()
