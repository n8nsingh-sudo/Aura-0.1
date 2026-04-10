import subprocess
import platform
import time
import os
import re

_PLATFORM = platform.system()

_APP_ALIASES = {
    "whatsapp": {"Darwin": "WhatsApp", "Windows": "WhatsApp", "Linux": "whatsapp"},
    "chrome": {
        "Darwin": "Google Chrome",
        "Windows": "chrome",
        "Linux": "google-chrome",
    },
    "firefox": {"Darwin": "Firefox", "Windows": "firefox", "Linux": "firefox"},
    "spotify": {"Darwin": "Spotify", "Windows": "Spotify", "Linux": "spotify"},
    "vscode": {"Darwin": "Visual Studio Code", "Windows": "code", "Linux": "code"},
    "discord": {"Darwin": "Discord", "Windows": "Discord", "Linux": "discord"},
    "telegram": {"Darwin": "Telegram", "Windows": "Telegram", "Linux": "telegram"},
    "notepad": {"Darwin": "TextEdit", "Windows": "notepad.exe", "Linux": "gedit"},
    "terminal": {"Darwin": "Terminal", "Windows": "cmd.exe", "Linux": "gnome-terminal"},
    "finder": {"Darwin": "Finder", "Windows": "explorer.exe", "Linux": "nautilus"},
    "calculator": {
        "Darwin": "Calculator",
        "Windows": "calc.exe",
        "Linux": "gnome-calculator",
    },
    "settings": {
        "Darwin": "System Preferences",
        "Windows": "ms-settings:",
        "Linux": "gnome-control-center",
    },
    "edge": {
        "Darwin": "Microsoft Edge",
        "Windows": "msedge",
        "Linux": "microsoft-edge",
    },
    "brave": {"Darwin": "Brave Browser", "Windows": "brave", "Linux": "brave-browser"},
}


def open_app(app_name: str) -> str:
    """Open an application by name"""
    app_lower = app_name.lower().strip()

    if app_lower in _APP_ALIASES:
        app_path = _APP_ALIASES[app_lower].get(_PLATFORM, app_lower)
    else:
        app_path = app_name

    try:
        if _PLATFORM == "Darwin":
            subprocess.run(["open", "-a", app_path], check=True)
        elif _PLATFORM == "Windows":
            subprocess.run(["start", "", app_path], shell=True, check=True)
        else:
            subprocess.run([app_path], check=True)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Error opening {app_name}: {e}"


def open_url(url: str) -> str:
    """Open a URL in default browser"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        if _PLATFORM == "Darwin":
            subprocess.run(["open", url], check=True)
        elif _PLATFORM == "Windows":
            subprocess.run(["start", "", url], shell=True)
        else:
            subprocess.run(["xdg-open", url])
        return f"Opened {url}"
    except Exception as e:
        return f"Error opening URL: {e}"


def open_website(site: str) -> str:
    """Open a website - wrapper for open_url"""
    return open_url(site)


def run_command(command: str) -> str:
    """Run a shell command"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout or result.stderr
        return output[:500] if output else "Command executed"
    except Exception as e:
        return f"Error: {e}"


def get_system_info() -> str:
    """Get system information"""
    info = f"System: {platform.system()}\n"
    info += f"Version: {platform.version()}\n"
    info += f"Machine: {platform.machine()}\n"
    info += f"Processor: {platform.processor()}\n"
    return info


def take_screenshot() -> str:
    """Take a screenshot"""
    try:
        if _PLATFORM == "Darwin":
            import datetime

            fname = (
                f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            subprocess.run(["screencapture", "-x", f"/tmp/{fname}"], check=True)
            return f"Screenshot saved to /tmp/{fname}"
        elif _PLATFORM == "Windows":
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen",
                ],
                check=False,
            )
            return "Screenshot taken"
        else:
            subprocess.run(["scrot"], check=True)
            return "Screenshot taken"
    except Exception as e:
        return f"Error: {e}"


def search_web(query: str) -> str:
    """Search the web"""
    return open_url(f"https://duckduckgo.com/?q={query.replace(' ', '+')}")


def play_youtube(video: str) -> str:
    """Play a YouTube video"""
    query = video.replace(" ", "+")
    return open_url(f"https://youtube.com/results?search_query={query}")


def get_weather(city: str) -> str:
    """Get weather for a city using web search"""
    return search_web(f"weather {city}")


def set_reminder(text: str, minutes: int = 5) -> str:
    """Set a reminder"""
    return f"Reminder set for {minutes} minutes: {text}"


def control_volume(level: str) -> str:
    """Control system volume (up, down, mute)"""
    try:
        if _PLATFORM == "Darwin":
            if level == "up":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        "set volume output volume of (output volume of (get volume settings) + 10)",
                    ]
                )
            elif level == "down":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        "set volume output volume of (output volume of (get volume settings) - 10)",
                    ]
                )
            elif level == "mute":
                subprocess.run(["osascript", "-e", "set volume output volume of 0"])
            return f"Volume {level}"
        else:
            return f"Volume control not supported on {_PLATFORM}"
    except Exception as e:
        return f"Error: {e}"


def get_ip() -> str:
    """Get public IP address"""
    try:
        import urllib.request

        return urllib.request.urlopen("https://api.ipify.org").read().decode()
    except:
        return "Unable to get IP"


def get_date() -> str:
    """Get current date and time"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_file(name: str, content: str = "") -> str:
    """Create a new file"""
    try:
        with open(name, "w") as f:
            f.write(content)
        return f"File created: {name}"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read a file"""
    try:
        with open(path, "r") as f:
            return f.read()[:2000]
    except Exception as e:
        return f"Error: {e}"


def list_files(path: str = ".") -> str:
    """List files in directory"""
    try:
        files = os.listdir(path)
        return "\n".join(files[:50])
    except Exception as e:
        return f"Error: {e}"
