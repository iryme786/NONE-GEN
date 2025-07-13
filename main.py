
from pyrogram import Client, filters
from pyrogram.types import Message
import requests
import random
import string
import time

API_ID = 21601817
API_HASH = "8d0fe8b5ae8149455681681253b2ef17"
BOT_TOKEN = "8159627489:AAELW-QwJTInrSd55f5vZQSJvjzZz7zVvkg"

app = Client("classplus_manual_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_state = {}  # Temporarily stores user interaction states

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("📧 Please enter your email address:")
    user_state[message.chat.id] = {"step": "awaiting_email"}

@app.on_message(filters.text)
async def handle_input(client, message: Message):
    user_id = message.chat.id
    if user_id not in user_state:
        return

    state = user_state[user_id]

    # Step 1: User sent email
    if state["step"] == "awaiting_email":
        email = message.text.strip()
        state["email"] = email
        state["step"] = "awaiting_otp"
        await message.reply_text("📨 OTP sent to your email. Please enter the OTP:")
        user_state[user_id] = state

    # Step 2: User sent OTP
    elif state["step"] == "awaiting_otp":
        otp = ''.join(filter(str.isdigit, message.text.strip()))
        email = state["email"]
        device_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }

        payload = {
            "deviceId": device_id,
            "otp": otp,
            "email": email
        }

        try:
            res = requests.post("https://api.classplusapp.com/v2/user/loginWithEmail", json=payload, headers=headers)
            data = res.json()
            token = data.get("data", {}).get("token")

            if token:
                await message.reply_text(f"🔑 Access Token:
`{token}`")
            else:
                await message.reply_text("❌ Invalid OTP or failed to fetch token. Try again.")
        except Exception as e:
            await message.reply_text(f"⚠️ Error occurred: {e}")

        # Reset state
        user_state.pop(user_id, None)

app.run()
