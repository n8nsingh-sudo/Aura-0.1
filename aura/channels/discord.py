"""Discord channel for Aura."""

import os
import asyncio
import json
from aura.channels.base import Channel


class DiscordChannel(Channel):
    """Discord Bot channel."""

    name = "discord"

    def __init__(self, bot_token: str = None, aura_handler=None):
        self.bot_token = bot_token or os.getenv("DISCORD_BOT_TOKEN", "")
        self.aura_handler = aura_handler
        self.ws_url = None
        self.session_id = None
        self.running = False
        self.intents = 513  # GUILD_MESSAGES + DIRECT_MESSAGES

    def start(self):
        """Start Discord bot."""
        if not self.bot_token:
            print("Discord bot token not set. Set DISCORD_BOT_TOKEN")
            return

        self.running = True
        print("Discord bot starting...")
        asyncio.create_task(self._connect())

    async def _connect(self):
        """Connect to Discord gateway."""
        import websockets

        while self.running:
            try:
                async with websockets.connect(
                    self.ws_url or "wss://gateway.discord.gg/?v=10&encoding=json"
                ) as ws:
                    await self._handle_ws(ws)
            except Exception as e:
                print(f"Discord connection error: {e}")
                await asyncio.sleep(5)

    async def _handle_ws(self, ws):
        """Handle Discord WebSocket messages."""
        import websockets

        async for msg in ws:
            try:
                data = json.loads(msg)
                op = data.get("op")

                if op == 10:  # Hello
                    heartbeat_interval = data.get("d", {}).get(
                        "heartbeat_interval", 45000
                    )
                    asyncio.create_task(self._heartbeat(ws, heartbeat_interval))
                    await self._identify(ws)

                elif op == 0:  # Dispatch
                    t = data.get("t")
                    if t == "MESSAGE_CREATE":
                        await self._handle_message(data)

                elif op == 11:  # Heartbeat ACK
                    pass

            except Exception as e:
                print(f"WS error: {e}")

    async def _heartbeat(self, ws, interval):
        """Send heartbeats."""
        import websockets

        while self.running:
            try:
                await ws.send(json.dumps({"op": 1, "d": None}))
                await asyncio.sleep(interval / 1000)
            except:
                break

    async def _identify(self, ws):
        """Identify with Discord."""
        import websockets

        await ws.send(
            json.dumps(
                {
                    "op": 2,
                    "d": {
                        "token": self.bot_token,
                        "intents": self.intents,
                        "properties": {
                            "os": "Aura",
                            "browser": "Aura",
                            "device": "Aura",
                        },
                    },
                }
            )
        )

    async def _handle_message(self, data):
        """Handle incoming message."""
        msg = data.get("d", {})
        content = msg.get("content", "")
        channel_id = msg.get("channel_id")
        author = msg.get("author", {})

        if author.get("bot") or not content:
            return

        if self.aura_handler:
            response = self.aura_handler(content)
            await self.send(response, channel_id=channel_id)

    def send(self, message: str, channel_id: int = None, **kwargs):
        """Send message."""
        if not channel_id:
            print("No channel_id provided")
            return
        asyncio.create_task(self._send_message(channel_id, message))

    async def _send_message(self, channel_id: int, text: str):
        """Send message via HTTP."""
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {self.bot_token}"},
                json={"content": text[:2000]},
            )

    def stop(self):
        """Stop Discord bot."""
        self.running = False
        print("Discord bot stopped")


def create_discord_channel(bot_token: str = None, aura_handler=None) -> DiscordChannel:
    """Create Discord channel."""
    return DiscordChannel(bot_token, aura_handler)
