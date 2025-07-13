

from pyrogram import Client, filters
import requests
import random
import string
import time

API_ID = 1234567  # Replace with your API_ID
API_HASH = "your_api_hash_here"
BOT_TOKEN = "your_bot_token_here"

app = Client("classplus_token_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def generate_temp_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return name, f"{name}@1secmail.com"


def get_messages(username):
    try:
        resp = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain=1secmail.com")
        return resp.json()
    except Exception as e:
        return []


def read_message(username, message_id):
    try:
        url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain=1secmail.com&id={message_id}"
        resp = requests.get(url).json()
        return resp.get("body", "")
    except:
        return ""


@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Welcome to Classplus Token Bot!
Use /gettoken to begin.")


@app.on_message(filters.command("gettoken"))
async def get_token(client, message):
    name, temp_email = generate_temp_email()
    await message.reply_text(f"📨 Use this email to login on Classplus: `{temp_email}`

⏳ Waiting for OTP...")

    otp = None
    for _ in range(30):  # wait ~60 sec max
        messages = get_messages(name)
        for msg in messages:
            if "OTP" in msg["subject"] or "Login" in msg["subject"]:
                body = read_message(name, msg["id"])
                otp = ''.join(filter(str.isdigit, body))
                break
        if otp:
            break
        time.sleep(2)

    if not otp:
        await message.reply_text("❌ OTP not received. Try again.")
        return

    await message.reply_text(f"✅ OTP received: `{otp}`

⏳ Generating token...")

    # Send OTP to Classplus and extract token
    payload = {
        "deviceId": ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
        "otp": otp,
        "email": temp_email
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
            await message.reply_text(f"🔐 Your Token:

`{token}`")
        else:
            await message.reply_text("❌ Token not found. OTP may be invalid or expired.")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

app.run()
