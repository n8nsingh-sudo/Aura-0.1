"""Aura built-in channels."""

from aura.channels.base import Channel
from aura.channels.manager import ChannelManager, create_channel_manager
from aura.channels.telegram import TelegramChannel, create_telegram_channel
from aura.channels.discord import DiscordChannel, create_discord_channel
from aura.channels.slack import SlackChannel, create_slack_channel

__all__ = [
    "Channel",
    "ChannelManager",
    "create_channel_manager",
    "create_telegram_channel",
    "create_discord_channel",
    "create_slack_channel",
    "TelegramChannel",
    "DiscordChannel",
    "SlackChannel",
]
