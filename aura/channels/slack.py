"""Slack channel for Aura."""

import os
import asyncio
import httpx
from aura.channels.base import Channel


class SlackChannel(Channel):
    """Slack Bot channel."""

    name = "slack"

    def __init__(self, bot_token: str = None, aura_handler=None):
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN", "")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
        self.aura_handler = aura_handler
        self.running = False

    def start(self):
        """Start Slack bot."""
        if not self.bot_token:
            print("Slack bot token not set. Set SLACK_BOT_TOKEN")
            return

        self.running = True
        print("Slack bot started")
        asyncio.create_task(self._health_check())

    async def _health_check(self):
        """Health check loop."""
        while self.running:
            await asyncio.sleep(60)

    def send(self, message: str, channel: str = None, **kwargs):
        """Send message to Slack."""
        if not channel:
            print("No channel provided")
            return

        asyncio.create_task(self._post_message(channel, message))

    async def _post_message(self, channel: str, text: str):
        """Post message via Slack API."""
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={"channel": channel, "text": text[:3000]},
            )

    def stop(self):
        """Stop Slack bot."""
        self.running = False
        print("Slack bot stopped")


def create_slack_channel(bot_token: str = None, aura_handler=None) -> SlackChannel:
    """Create Slack channel."""
    return SlackChannel(bot_token, aura_handler)
