"""Channel base class - ABC for Aura channels."""

from abc import ABC, abstractmethod
from typing import Callable, Optional
import json
import asyncio


class Channel(ABC):
    """Base class for messaging channels."""

    name: str = "base"

    @abstractmethod
    def start(self):
        """Start the channel listener."""
        pass

    @abstractmethod
    def send(self, message: str, **kwargs):
        """Send a message."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the channel."""
        pass
