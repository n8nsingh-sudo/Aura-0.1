import whisper_mic
import threading
import asyncio
import edge_tts
import tempfile
import os
import platform
import re


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
        self, model: str = "base", english: bool = False, wake_word: str = "aura"
    ):
        self.model = model
        self.english = english
        self.default_voice = "en-US-AriaNeural"
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.platform = platform.system()
        self.wake_word = wake_word.lower()
        self.is_listening = False
        self._mic = None

        try:
            self._mic = whisper_mic.WhisperMic(model=model, english=english)
            print(
                f"✓ Voice: Whisper mic ready (model: {model}, multilingual: {not english})"
            )
        except Exception as e:
            print(f"⚠ Voice: Mic error: {e}")

        print(f"✓ Voice TTS ready")

    def speak(self, text: str, play: bool = True, language: str = None) -> str:
        if language is None:
            language = detect_language(text)

        voice = LANGUAGE_VOICES.get(language, self.default_voice)

        temp_path = asyncio.run(self._speak_async(text, voice))

        if play:
            try:
                if self.platform == "Darwin":
                    os.system(f"afplay '{temp_path}' &")
                elif self.platform == "Linux":
                    os.system(f"mpg321 '{temp_path}' &")
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
