# AURA - Autonomous Universal Reasoning Agent

**AURA** is an autonomous AI assistant inspired by JARVIS from Iron Man. A production-grade voice assistant with a premium glassmorphism dashboard.

---

## Features

- 🎙️ **Voice Interface** - Hands-free voice commands with wake-word detection ("AURA")
- 🌐 **Web Dashboard** - Beautiful JARVIS-style UI at `http://localhost:8080`
- 🧠 **Multi-Layer Memory** - Working, episodic, semantic, and long-term memory systems
- 🔍 **Web Intelligence** - Real-time web search, Wikipedia lookup, weather, and news
- 💻 **Code Execution** - Write and run code with automatic retry logic
- 🔊 **Multi-Language TTS** - Natural voice output in 20+ languages using edge-tts
- ⚡ **Smart Rate Limiting** - Governor system prevents overuse and manages costs

### Premium Features

- 🎵 **Interruption Support** - AURA stops speaking when you start talking
- 🎨 **Real-time Audio Visualization** - Rings pulse with your voice volume
- 🔄 **WebSocket Heartbeat** - Auto-reconnect on network issues
- 🤖 **JARVIS Voice Mode** - Configurable robotic-style voice option

---

## Tech Stack

- **Backend**: Python, FastAPI, Ollama (local LLM)
- **Voice**: Browser Web Speech API (STT), Edge-TTS (TTS)
- **Memory**: SQLite + vector embeddings
- **UI**: Custom HTML/CSS/JS with WebSocket real-time communication

---

## Installation

```bash
# Clone the repository
git clone https://github.com/n8nsingh-sudo/Aura-0.1.git
cd Aura-0.1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Start

### Option 1: Run with Full Dashboard
```bash
# Start Ollama (for local AI)
ollama serve

# Run AURA
python main.py
```
Visit `http://localhost:8080`

### Option 2: Run Dashboard Only
```bash
python run_dashboard.py
```

---

## Usage

1. Open `http://localhost:8080` in Chrome or Edge
2. Click the microphone button to enable voice
3. Say "AURA" followed by your command
4. Or type directly in the chat input

### Example Commands
- "What's the weather in Mumbai?"
- "Search for Python tutorials"
- "Who is Elon Musk?"
- "Calculate 2 + 2"
- "What's the latest tech news?"

---

## WebSocket Message Types

The dashboard communicates via WebSocket with these message types:

| Type | Direction | Description |
|------|-----------|-------------|
| `message` | Client→Server | Send chat message |
| `response` | Server→Client | AI response |
| `speak` | Client→Server | Request TTS playback |
| `stop_speech` | Client→Server | Stop current speech |
| `status` | Bidirectional | Memory/governor stats |
| `ping` | Client→Server | Heartbeat ping |
| `pong` | Server→Client | Heartbeat pong |

---

## Configuration

Edit `aura/config.py` to customize:

```python
# Voice Settings
VOICE_STYLE = "neural"  # or "jarvis" for robotic voice

# LLM Settings
LOCAL_MODEL = "qwen2.5-coder:14b"

# Rate Limits
MAX_REQUESTS_PER_MINUTE = 30
MAX_COST_PER_DAY_USD = 5.0
```

---

## Requirements

- Python 3.10+
- Ollama (for local LLM) - https://ollama.ai
- Chrome or Edge (for best voice recognition)

---

## Architecture

AURA follows a **UI-first** architecture:

```
Browser (Voice/Chat) ←WebSocket→ FastAPI Backend ←→ Ollama LLM
                                          ↓
                                     Memory Systems
```

The voice assistant lives entirely in the browser for maximum compatibility and visual performance. The backend handles LLM processing, memory management, and tool execution.

---

## License

MIT License - See LICENSE file

---

## Contributing

Contributions welcome! Please open an issue or submit a PR.

For a full list of changes, see CHANGELOG.md.