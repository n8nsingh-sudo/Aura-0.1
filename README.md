# AURA - Autonomous Universal Reasoning Agent

**AURA** is an autonomous AI assistant inspired by JARVIS from Iron Man. It combines voice interaction, intelligent reasoning, memory systems, and autonomous operation in a single, self-hosted package.

---

## Features

- 🎙️ **Voice Interface** - Hands-free voice commands with wake-word detection ("AURA")
- 🧠 **Multi-Layer Memory** - Working, episodic, semantic, and long-term memory systems
- 🔍 **Web Intelligence** - Real-time web search, Wikipedia lookup, weather, and news
- 💻 **Code Execution** - Write and run code with automatic retry logic
- 🌐 **Web Dashboard** - Beautiful JARVIS-style UI at `http://localhost:8080`
- 🔊 **Multi-Language TTS** - Natural voice output in 20+ languages using edge-tts
- ⚡ **Smart Rate Limiting** - Governor system prevents overuse and manages costs

---

## Tech Stack

- **Backend**: Python, FastAPI, Ollama (local LLM)
- **Voice**: Whisper (STT), Edge-TTS (TTS)
- **Memory**: SQLite + vector embeddings
- **UI**: Custom HTML/CSS/JS with WebSocket real-time communication

---

## Installation

```bash
# Clone the repository
git clone https://github.com/n8nsingh-sudo/AURA.git
cd AURA

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Start

### Option 1: Run with Dashboard UI
```bash
# Start Ollama (for local AI)
ollama serve

# Run AURA
python main.py
```
Visit `http://localhost:8080` to access the dashboard.

### Option 2: Run Dashboard Only
```bash
python run_dashboard.py
```

---

## Usage

1. Open `http://localhost:8080` in your browser
2. Click the microphone button to enable voice
3. Say "AURA" followed by your command
4. Or type directly in the chat input

### Example Commands
- "What's the weather in Mumbai?"
- "Search for Python tutorials"
- "Who is Elon Musk?"
- "Calculate 2 + 2"

---

## Configuration

Edit `aura/config.py` to customize:
- LLM model selection
- Rate limits
- Memory settings
- API keys

---

## Requirements

- Python 3.10+
- Ollama (for local LLM) - https://ollama.ai
- Microphone for voice input

---

## License

MIT License

---

## Contributing

Contributions welcome! Please open an issue or submit a PR.# Aura-0.1
