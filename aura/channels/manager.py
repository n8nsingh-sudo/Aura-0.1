"""Aura Multi-channel System - Support for multiple messaging platforms."""

from typing import Callable, Optional
import json
import asyncio

from aura.channels.base import Channel


class ChannelManager:
    """Manage multiple channels."""

    def __init__(self, aura_handler: Callable = None):
        self.channels: dict[str, Channel] = {}
        self.handlers: dict[str, Channel] = {}
        self.aura_handler = aura_handler

    def register(self, channel: Channel):
        """Register a channel."""
        self.channels[channel.name] = channel
        self.handlers[channel.name] = channel

    def start_all(self):
        """Start all registered channels."""
        for channel in self.channels.values():
            try:
                channel.start()
                print(f"Started channel: {channel.name}")
            except Exception as e:
                print(f"Failed to start {channel.name}: {e}")

    def stop_all(self):
        """Stop all channels."""
        for channel in self.channels.values():
            try:
                channel.stop()
            except:
                pass

    def send_to(self, channel_name: str, message: str, **kwargs):
        """Send message via specific channel."""
        if channel_name in self.channels:
            self.channels[channel_name].send(message, **kwargs)
        else:
            print(f"Channel not found: {channel_name}")

    def list_channels(self) -> list[dict]:
        """List all channels."""
        return [
            {"name": c.name, "type": type(c).__name__} for c in self.channels.values()
        ]


def create_channel_manager(aura_handler: Callable = None) -> ChannelManager:
    """Create and configure channel manager."""
    return ChannelManager(aura_handler)
