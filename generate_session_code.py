"""Create a Telegram StringSession using Telegram's supported code flow."""

import getpass
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from telethon.errors import PasswordHashInvalidError, SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.auth import ResendCodeRequest

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

phone = input("Telegram phone number (include country code): ").strip()
client = TelegramClient(
    StringSession(), int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"]
)

try:
    client.connect()
    sent = client.send_code_request(phone)

    for attempt in range(2):
        next_type = getattr(sent, "next_type", None)
        timeout = getattr(sent, "timeout", None)
        print(f"Telegram delivery type: {type(sent.type).__name__}")
        print(f"Next available method: {type(next_type).__name__ if next_type else 'none'}")
        if timeout:
            print(f"Telegram says to wait {timeout} seconds before trying the next method.")
        code = input("Enter the Telegram code, or press Enter if it did not arrive: ").strip()
        if code:
            break
        if attempt or not next_type:
            print("Telegram did not offer another code delivery method. Stop here; do not keep requesting codes.")
            raise SystemExit(2)
        if timeout:
            time.sleep(timeout)
        sent = client(ResendCodeRequest(phone_number=phone, phone_code_hash=sent.phone_code_hash))

    try:
        client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
    except SessionPasswordNeededError:
        for attempt in range(3):
            password = getpass.getpass("Telegram two-step verification password: ")
            try:
                client.sign_in(password=password)
                break
            except PasswordHashInvalidError:
                if attempt == 2:
                    print("Telegram rejected the password three times. Stop and check/reset the two-step password in Telegram.")
                    raise
                print("Telegram says that password is incorrect. Check Caps Lock and keyboard layout, then try again.")

    session = client.session.save()
    data = ENV_PATH.read_text(encoding="utf-8-sig")
    if re.search(r"(?m)^TG_SESSION_STRING=.*$", data):
        data = re.sub(
            r"(?m)^TG_SESSION_STRING=.*$",
            lambda _: "TG_SESSION_STRING=" + session,
            data,
        )
    else:
        data += "\nTG_SESSION_STRING=" + session + "\n"
    ENV_PATH.write_text(data, encoding="utf-8")
    print("Telegram session saved to .env (value hidden).")
finally:
    client.disconnect()

