"""Telegram channel for Aura."""

import os
import asyncio
import httpx
from aura.channels.base import Channel


class TelegramChannel(Channel):
    """Telegram Bot channel."""

    name = "telegram"

    def __init__(self, bot_token: str = None, aura_handler=None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.aura_handler = aura_handler
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0
        self.running = False

    def start(self):
        """Start polling for messages."""
        if not self.bot_token:
            print("Telegram bot token not set. Set TELEGRAM_BOT_TOKEN")
            return

        self.running = True
        print(f"Telegram bot started (@{self.get_me().get('username', 'unknown')})")
        asyncio.create_task(self._poll_loop())

    def _poll_loop(self):
        """Poll for updates."""
        asyncio.create_task(self._poll())

    async def _poll(self):
        """Poll Telegram API."""
        async with httpx.AsyncClient() as client:
            while self.running:
                try:
                    response = await client.get(
                        f"{self.api_url}/getUpdates",
                        params={"offset": self.offset, "timeout": 30},
                        timeout=35,
                    )
                    data = response.json()

                    if data.get("ok"):
                        for update in data.get("result", []):
                            self.offset = update["update_id"] + 1
                            message = update.get("message", {})
                            chat_id = message.get("chat", {}).get("id")
                            text = message.get("text", "")

                            if chat_id and text and self.aura_handler:
                                response = self.aura_handler(text)
                                await self.send_message(chat_id, response[:4000])

                    await asyncio.sleep(2)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Poll error: {e}")
                    await asyncio.sleep(5)

    def get_me(self) -> dict:
        """Get bot info."""
        if not hasattr(self, "_me"):
            import requests

            resp = requests.get(f"{self.api_url}/getMe")
            self._me = resp.json().get("result", {})
        return self._me

    def send(self, message: str, chat_id: int = None, **kwargs):
        """Send a message."""
        if not chat_id:
            print("No chat_id provided")
            return
        asyncio.create_task(self.send_message(chat_id, message))

    async def send_message(self, chat_id: int, text: str):
        """Send message to chat."""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.api_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )

    def stop(self):
        """Stop polling."""
        self.running = False
        print("Telegram bot stopped")


def create_telegram_channel(
    bot_token: str = None, aura_handler=None
) -> TelegramChannel:
    """Create Telegram channel."""
    return TelegramChannel(bot_token, aura_handler)
