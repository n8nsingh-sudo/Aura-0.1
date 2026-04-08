#!/usr/bin/env python3
import os

os.environ["TERM"] = "dumb"

from aura.dashboard.server import app, set_components
from aura.memory.fabric import MemoryFabric
from aura.core.loop import AURALoop
from aura.action.voice import VoiceInterface
import uvicorn

print("Starting AURA Dashboard...")

memory = MemoryFabric()
aura = AURALoop(memory)
voice = VoiceInterface()

set_components(memory, aura.governor, voice, aura)

print("AURA is ready at http://localhost:8080")
print("Click 🎤 to use voice input!")

uvicorn.run(app, host="127.0.0.1", port=8080, log_level="error", access_log=False)
