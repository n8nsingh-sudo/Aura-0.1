#!/usr/bin/env python3
from aura.core.loop import AURALoop
from aura.core.planner import GoalEngine
from aura.memory.fabric import MemoryFabric
from aura.learning.embedder import Embedder
from aura.learning.sources.universal_ingestor import UniversalIngestor
from aura.action.code_executor import CodeExecutor
from aura.action.tool_registry import ToolRegistry
from aura.action.voice import VoiceInterface
from aura.dashboard.server import start_dashboard, set_components
import threading
import time
import sys
import os
import subprocess
import signal


def cleanup_port(port=8080):
    """Cleanup any existing processes on the dashboard port to avoid zombies."""
    try:
        if sys.platform != "win32":
            cmd = f"lsof -ti:{port} | xargs kill -9 2>/dev/null"
            subprocess.run(cmd, shell=True)
            time.sleep(1)
    except Exception:
        pass


def signal_handler(signum, frame):
    """Handle SIGTERM for clean shutdown."""
    print("\n⚠️ Received shutdown signal, cleaning up...")
    cleanup_port(8080)
    sys.exit(0)


def main():
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Pre-start cleanup to avoid zombies
    cleanup_port(8080)

    print("=" * 60)
    print("🎯 AURA - Autonomous Universal Reasoning Agent")
    print("=" * 60)

    print("\n[1] Initializing components...")
    memory = MemoryFabric()
    embedder = Embedder()
    aura = AURALoop(memory)
    router = aura.router
    goals = GoalEngine(router, memory)
    ingestor = UniversalIngestor(memory, embedder)
    tools = ToolRegistry()
    # Use TTS-only mode to skip Whisper mic loading (browser handles voice)
    voice = VoiceInterface(tts_only=True)
    executor = CodeExecutor(router)
    print("✅ All components ready")

    print("\n[2] Starting Web Dashboard on port 8080...")
    dashboard_thread = threading.Thread(
        target=start_dashboard,
        args=(memory, aura.governor, voice, aura, 8080),
        daemon=True,
    )
    dashboard_thread.start()

    print("\n[4] Starting Whisper Voice Assistant...")

    def handle_voice_command(cmd):
        print(f"\n🔊 Voice Command: {cmd}")
        result = aura.run_once(cmd)
        print(f"AURA: {result[:200]}...")
        voice.speak(result[:200])

    # voice.start_listening(handle_voice_command)

    print("\n" + "=" * 60)
    print("🌐 AURA Dashboard: http://localhost:8080")
    print("🎤 Say 'AURA' to activate voice")
    print("=" * 60)
    print("\nDashboard is running. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print("\n👋 AURA shutdown complete")


if __name__ == "__main__":
    main()
