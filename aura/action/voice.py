import threading
import asyncio
import tempfile
import os
import platform
import subprocess
import signal
import re

try:
    import whisper_mic

    _WHISPER_MIC_OK = True
except ImportError:
    _WHISPER_MIC_OK = False
    whisper_mic = None

try:
    import edge_tts

    _EDGE_TTS_OK = True
except ImportError:
    _EDGE_TTS_OK = False
    edge_tts = None

from aura import config


LANGUAGE_VOICES = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ar": "ar-SA-ZaidanNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-MeghanaNeural",
    "ml": "ta-IN-MeeraNeural",
    "bn": "bn-IN-BashiraNeural",
    "gu": "gu-IN-DhwaniNeural",
    "kn": "kn-IN-SapnaNeural",
    "mr": "mr-IN-AarohiNeural",
    "pa": "pa-IN-ManpreetiNeural",
}


def detect_language(text: str) -> str:
    """Detect language from text"""
    hindi_pattern = re.compile(r"[\u0900-\u097F]")
    if hindi_pattern.search(text):
        return "hi"

    chinese_pattern = re.compile(r"[\u4e00-\u9fff]")
    if chinese_pattern.search(text):
        return "zh"

    japanese_pattern = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
    if japanese_pattern.search(text):
        return "ja"

    korean_pattern = re.compile(r"[\uac00-\ud7af]")
    if korean_pattern.search(text):
        return "ko"

    arabic_pattern = re.compile(r"[\u0600-\u06ff]")
    if arabic_pattern.search(text):
        return "ar"

    cyrillic_pattern = re.compile(r"[\u0400-\u04ff]")
    if cyrillic_pattern.search(text):
        return "ru"

    return "en"


class VoiceInterface:
    def __init__(
        self,
        model: str = "base",
        english: bool = False,
        wake_word: str = "aura",
        tts_only: bool = False,
    ):
        self.model = model
        self.english = english
        self.default_voice = "en-US-AriaNeural"
        # Use config settings for voice style
        if config.VOICE_STYLE == "jarvis":
            self.rate = "+20%"
            self.pitch = "-10Hz"
        else:
            self.rate = config.VOICE_RATE
            self.pitch = config.VOICE_PITCH
        self.platform = platform.system()
        self.wake_word = wake_word.lower()
        self.is_listening = False
        self._mic = None
        self._playback_proc = None  # Tracking current speech process
        self._current_process = None  # For speech cancellation

        # Only load Whisper mic if not TTS-only mode
        if not tts_only:
            try:
                self._mic = whisper_mic.WhisperMic(model=model, english=english)
                print(
                    f"✓ Voice: Whisper mic ready (model: {model}, multilingual: {not english})"
                )
            except Exception as e:
                print(f"⚠ Voice: Mic error: {e}")
        else:
            print(f"✓ Voice: TTS-only mode (no mic)")

        print(f"✓ Voice TTS ready ({config.VOICE_STYLE} style)")

        try:
            self._mic = whisper_mic.WhisperMic(model=model, english=english)
            print(
                f"✓ Voice: Whisper mic ready (model: {model}, multilingual: {not english})"
            )
        except Exception as e:
            print(f"⚠ Voice: Mic error: {e}")

        print(f"✓ Voice TTS ready")

    def stop_speaking(self):
        """Stop the current audio playback immediately."""
        # Stop _playback_proc
        if self._playback_proc:
            try:
                if self.platform == "Windows":
                    self._playback_proc.kill()
                else:
                    os.kill(self._playback_proc.pid, signal.SIGTERM)
                self._playback_proc = None
            except:
                pass
        # Stop _current_process
        if self._current_process:
            try:
                if self.platform == "Windows":
                    self._current_process.kill()
                else:
                    os.kill(self._current_process.pid, signal.SIGTERM)
                self._current_process = None
            except:
                pass

    def speak(self, text: str, play: bool = True, language: str = None) -> str:
        """Speak text using edge-tts. Handled safely for running event loops."""
        if language is None:
            language = detect_language(text)

        voice = LANGUAGE_VOICES.get(language, self.default_voice)

        # Handle asyncio safely
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If we're already in a loop, we run the coroutine in that loop
            # This avoids the "asyncio.run() cannot be called" error
            temp_path = asyncio.run_coroutine_threadsafe(
                self._speak_async(text, voice), loop
            ).result()
        else:
            temp_path = asyncio.run(self._speak_async(text, voice))

        if play:
            self.stop_speaking()  # Stop previous speech before playing new
            try:
                cmd = []
                if self.platform == "Darwin":
                    cmd = ["afplay", temp_path]
                elif self.platform == "Linux":
                    cmd = ["mpg321", temp_path]

                if cmd:
                    self._playback_proc = subprocess.Popen(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                print(f"Playback error: {e}")

        return temp_path

    async def _speak_async(self, text: str, voice: str = None) -> str:
        if voice is None:
            voice = self.default_voice

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close()

        communicate = edge_tts.Communicate(
            text, voice, rate=self.rate, pitch=self.pitch
        )
        await communicate.save(temp_path)

        return temp_path

    def speak_background(self, text: str):
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()

    def start_listening(self, callback):
        def listen_loop():
            print(f"🎤 Listening for '{self.wake_word}' wake word...")
            while self.is_listening:
                try:
                    result = self._mic.listen()
                    if result:
                        text = result.lower().strip()
                        print(f" Heard: {text}")

                        if self.wake_word in text:
                            # Wake word detected
                            cmd = text.replace(self.wake_word, "").strip()
                            self.speak("Yes, I'm listening")
                            callback(cmd)
                        elif len(text) > 3:
                            # Direct command without wake word
                            callback(text)
                except Exception as e:
                    print(f"Listen error: {e}")

        self.is_listening = True
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
        print(f"✓ AURA voice assistant started")

    def stop_listening(self):
        self.is_listening = False
        print("✓ Voice listening stopped")


def voice_test():
    print("=" * 50)
    print("AURA Voice Test (Whisper)")
    print("=" * 50)

    voice = VoiceInterface()

    print("\nTesting TTS...")
    voice.speak("Hello! I am AURA.")

    print("\nTesting Whisper mic...")
    print("Say 'AURA' followed by your command")

    def handle_command(cmd):
        print(f"Command: {cmd}")

    voice.start_listening(handle_command)

    import time

    time.sleep(30)
    voice.stop_listening()


if __name__ == "__main__":
    voice_test()
