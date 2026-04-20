import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(ENV_PATH)

TELEGRAM_API_ID   = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE    = os.getenv("TELEGRAM_PHONE", "")
TELEGRAM_ENABLED  = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

# Public channels known to share leaked Indian data
# Add more as you find them
TARGET_CHANNELS = [
    "indialeaks",
    "databreach_india",
    "indiandataleaks",
]

KEYWORDS = [
    "aadhaar", "aadhar", "pan", "upi", "ifsc",
    "mobile", "leak", "dump", "breach", "india"
]

async def _fetch_messages(channel_username, limit=100):
    from telethon import TelegramClient
    from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError

    results = []
    session_path = os.path.join(os.path.dirname(__file__), "telegram_session")

    async with TelegramClient(session_path, TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
        try:
            await client.start(phone=TELEGRAM_PHONE)
            entity = await client.get_entity(channel_username)

            async for message in client.iter_messages(entity, limit=limit):
                if not message.text:
                    continue

                text_lower = message.text.lower()
                if not any(kw in text_lower for kw in KEYWORDS):
                    continue

                results.append({
                    "url":         f"https://t.me/{channel_username}/{message.id}",
                    "source_type": "telegram",
                    "content":     message.text,
                    "fetched_at":  datetime.now(timezone.utc).isoformat()
                })
                print(f"[Telegram] Matched message from @{channel_username} id={message.id}")

        except ChannelPrivateError:
            print(f"[Telegram] @{channel_username} is private — skipping")
        except UsernameNotOccupiedError:
            print(f"[Telegram] @{channel_username} not found — skipping")
        except Exception as e:
            print(f"[Telegram] Error on @{channel_username}: {e}")

    return results


def scrape_telegram():
    if not TELEGRAM_ENABLED:
        print("[Telegram] Disabled — set TELEGRAM_ENABLED=true in .env when ready")
        return []

    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH or not TELEGRAM_PHONE:
        print("[Telegram] Missing credentials in .env")
        return []

    all_results = []
    for channel in TARGET_CHANNELS:
        try:
            msgs = asyncio.run(_fetch_messages(channel))
            all_results.extend(msgs)
        except Exception as e:
            print(f"[Telegram] Failed for @{channel}: {e}")

    print(f"[Telegram] Total matched messages: {len(all_results)}")
    return all_results