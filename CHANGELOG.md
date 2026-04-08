# Changelog - AURA

All notable changes to AURA will be documented in this file.

---

## [2.0.0] - 2024-04-08

### 🚀 Major Changes

- **UI-First Architecture**: Voice assistant now lives entirely in the browser for maximum compatibility
- **Removed Terminal Mic**: No more "device busy" errors from Whisper loading in backend
- **WebSocket Heartbeat**: Client pings every 15s, auto-reconnect on network issues

### 🐛 Bug Fixes

- **Fixed duplicate toggleMic()** - Removed orphaned code block that was breaking mic
- **Fixed broadcast_status() asyncio bug** - Uses `call_soon(ensure_future())` for Python 3.10+ compatibility
- **Fixed WebSocketDisconnect crash** - Added guard for duplicate connection removal
- **Fixed asyncio.run() crash** - Uses `run_coroutine_threadsafe()` in async context
- **Fixed hardcoded shebang** - Now uses `#!/usr/bin/env python3`
- **Fixed scroll race condition** - Uses `requestAnimationFrame()` for reliable scrolling
- **Fixed thinking state** - Now properly removed on both success and error paths

### ✨ New Features

- **Interruption Support**: AURA stops speaking when you start talking
- **Web Audio API Visualization**: Rings pulse with your voice volume in real-time
- **Mic Permission Recovery UI**: Step-by-step instructions when browser blocks mic
- **JARVIS Voice Mode**: Configurable robotic voice style (rate +20%, pitch -10Hz)
- **Speaking State CSS**: Visual feedback when AURA is talking

### 🎨 UI Improvements

- **Deduplicated CSS**: Fixed chat input disappearing issue
- **State Machine**: IDLE, LISTENING, THINKING, SPEAKING states properly wired
- **WebSocket Error Handler**: Removes thinking state on connection errors

### 🔧 Backend Changes

- **TTS-Only Voice Mode**: New `VoiceInterface(tts_only=True)` skips Whisper loading
- **Signal Handling**: Proper cleanup on SIGTERM/SIGINT
- **LLM in Executor**: WebSocket handler uses `run_in_executor()` to keep event loop free

---

## [1.0.0] - 2024-03-xx

### Added
- Initial AURA implementation
- Multi-layer memory system
- Web dashboard with glassmorphism UI
- Voice interface with Whisper + edge-tts
- Tool registry (weather, calculator, wikipedia, news)
- Code execution with retry logic

---

## Migration Notes

### Upgrading to 2.0

1. Browser-based voice now requires Chrome or Edge (best compatibility)
2. Terminal voice listener is disabled by default
3. Config file now has `VOICE_STYLE` option for voice selection
4. WebSocket message types expanded - see README for details

### Breaking Changes

- `VoiceInterface()` now requires `tts_only=True` for dashboard use
- Removed `voice.start_listening()` from main.py (handled by browser)
- WebSocket ping/pong for heartbeat (backward compatible)