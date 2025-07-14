from pyrogram import Client, filters
from pyrogram.types import Message
from fastapi import FastAPI
import uvicorn
import threading
import requests
import random
import string
import time

# Telegram Bot Config
API_ID = 21601817
API_HASH = "8d0fe8b5ae8149455681681253b2ef17"
BOT_TOKEN = "8159627489:AAELW-QwJTInrSd55f5vZQSJvjzZz7zVvkg"  # replace with real one

bot = Client("auto_token_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
web = FastAPI()
user_state = {}

# Generate temp mail
def generate_email():
    login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = "1secmail.com"
    return f"{login}@{domain}", login, domain

# Check inbox
def check_inbox(login, domain):
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
    return requests.get(url).json()

# Read specific message
def read_message(login, domain, msg_id):
    url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}"
    return requests.get(url).json()

# Extract OTP from mail body (simple digits)
def extract_otp(body):
    import re
    found = re.findall(r'\b\d{4,8}\b', body)
    return found[0] if found else None

@bot.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    email, login, domain = generate_email()
    user_state[message.from_user.id] = {
        "email": email,
        "login": login,
        "domain": domain,
        "step": "waiting_otp"
    }
    await message.reply_text(f"📧 Use this temp email:\n`{email}`\n\nNow request OTP and wait...", parse_mode="markdown")

    # Start checking inbox
    for _ in range(30):  # check for 30 * 3 sec = 90 sec
        inbox = check_inbox(login, domain)
        if inbox:
            msg = read_message(login, domain, inbox[0]["id"])
            otp = extract_otp(msg["body"])
            if otp:
                await message.reply_text(f"🔢 OTP Received: `{otp}`", parse_mode="markdown")
                # Send token request
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
                        await message.reply_text(f"🟢 <b>Access Token:</b>\n<code>{token}</code>", parse_mode="html")
                    else:
                        await message.reply_text("❌ Failed to get token. Wrong OTP or expired.")
                except Exception as e:
                    await message.reply_text(f"⚠️ Error: {str(e)}")
                break
        time.sleep(3)
    else:
        await message.reply("⌛ Timeout: OTP not received in 90 seconds.")

@web.get("/")
def root():
    return {"status": "Bot is running ✅"}

def run():
    bot.run()

threading.Thread(target=run).start()
uvicorn.run(web, host="0.0.0.0", port=8000)
