#!/usr/bin/env python3
from aura.core.loop import AURALoop
from aura.core.planner import GoalEngine
from aura.memory.fabric import MemoryFabric
from aura.learning.embedder import Embedder
from aura.learning.sources.universal_ingestor import UniversalIngestor
from aura.action.code_executor import CodeExecutor
from aura.action.tool_registry import ToolRegistry
from aura.action.voice import VoiceInterface
from aura.dashboard.server import start_dashboard
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
            # Command to find and kill the process on given port
            cmd = f"lsof -ti:{port} | xargs kill -9 2>/dev/null"
            subprocess.run(cmd, shell=True)
            time.sleep(1)  # Give it a second to release the port
    except Exception:
        pass


def main():
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
    voice = VoiceInterface()
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
    print("\nCommands:")
    print("  quit          - Exit")
    print("  status        - Show stats")
    print("  goal <text>   - Add a goal")
    print("  ingest <url>  - Learn from URL")
    print("  calc <expr>   - Calculate")
    print("  weather <city> - Get weather")
    print("  voice <text>  - Speak text")
    print("-" * 40)

    while True:
        try:
            user_input = input("\n> ").strip()

            if user_input.lower() == "quit":
                voice.stop_listening()
                break
            elif user_input.lower() == "status":
                print(f"Memory: {memory.get_stats()}")
                print(f"Governor: {aura.governor.get_status()}")
                print(f"Goals: {len(goals.goals)} active")
                print(f"Tools: {len(tools.tools)} available")
            elif user_input.lower().startswith("goal "):
                goal_text = user_input[5:]
                goals.add_goal(goal_text, priority=5)
                print(f"Goal added: {goal_text}")
            elif user_input.lower().startswith("ingest "):
                url = user_input[7:]
                result = ingestor.ingest(url)
                print(f"Ingest: {result}")
            elif user_input.lower().startswith("calc "):
                expr = user_input[5:]
                print(tools.call("calculator", expression=expr))
            elif user_input.lower().startswith("weather "):
                city = user_input[9:]
                print(tools.call("get_weather", city=city))
            elif user_input.lower().startswith("voice "):
                text = user_input[6:]
                voice.speak(text)
            elif user_input.lower() == "tools":
                print(tools.list_tools())
            elif user_input:
                result = aura.run_once(user_input)
                print(f"\n{result[:300]}...")
        except KeyboardInterrupt:
            voice.stop_listening()
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\n👋 AURA shutdown complete")


if __name__ == "__main__":
    main()
