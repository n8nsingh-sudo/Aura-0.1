from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import threading
import whisper
import os

app = FastAPI(title="AURA Interface")

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_memory = None
_governor = None
_voice = None
_aura_loop = None
_active_connections = []

_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def set_components(memory, governor, voice=None, aura_loop=None):
    global _memory, _governor, _voice, _aura_loop
    _memory = memory
    _governor = governor
    _voice = voice
    _aura_loop = aura_loop


@app.get("/")
async def get_page():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(html_path, "r") as f:
        return HTMLResponse(f.read())


@app.get("/js/{filename}")
async def get_js(filename):
    js_path = os.path.join(BASE_DIR, "js", filename)
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return {"error": "File not found"}


@app.get("/css/{filename}")
async def get_css(filename):
    css_path = os.path.join(BASE_DIR, "css", filename)
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return {"error": "File not found"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "message":
                content = message.get("content", "")
                print(f"Processing: {content[:50]}")

                if not _aura_loop:
                    await websocket.send_json(
                        {"type": "response", "content": "System not ready"}
                    )
                    continue

                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, _aura_loop.run_once, content
                    )
                    await websocket.send_json({"type": "response", "content": result})
                    if _voice:
                        _voice.speak_background(result[:300])
                except Exception as e:
                    await websocket.send_json(
                        {"type": "response", "content": f"Error: {str(e)}"}
                    )

            elif message.get("type") == "get_models":
                await websocket.send_json(
                    {
                        "type": "models_list",
                        "models": ["qwen2.5-coder", "llama3", "mistral"],
                    }
                )

            elif message.get("type") == "set_model":
                if _aura_loop and hasattr(_aura_loop.router, "set_local_model"):
                    _aura_loop.router.set_local_model(message["content"])
                    await websocket.send_json(
                        {
                            "type": "response",
                            "content": f"Switched to {message['content']}",
                        }
                    )

            elif message.get("type") == "stop_speech":
                if _voice:
                    _voice.stop_speaking()

            elif message.get("type") == "speak":
                if _voice:
                    _voice.speak_background(message["content"])

            elif message.get("type") == "execute":
                code = message.get("content", "")
                try:
                    from aura.action.sandbox import run_code_safely

                    result = run_code_safely(code)
                    output = (
                        result.get("output", "") or result.get("stderr", "") or "Done"
                    )
                    await websocket.send_json(
                        {"type": "response", "content": f"Output: {output}"}
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "response", "content": f"Error: {e}"}
                    )

    except WebSocketDisconnect:
        if websocket in _active_connections:
            _active_connections.remove(websocket)


async def broadcast_status():
    while True:
        try:
            if _memory and _governor:
                status = {
                    "memory": _memory.get_stats(),
                    "governor": _governor.get_status(),
                }
                for conn in _active_connections[:]:
                    try:
                        await conn.send_json({"type": "status", "data": status})
                    except:
                        pass
        except:
            pass
        await asyncio.sleep(5)


def run_server(port=8080):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(broadcast_status())
    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=port, loop=loop)
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())


if __name__ == "__main__":
    run_server(8080)
