from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import json
import threading

app = FastAPI(title="AURA Interface")

_memory = None
_governor = None
_voice = None
_aura_loop = None
_active_connections = []

import whisper

_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AURA - Autonomous Intelligence</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #00f7ff;
            --secondary: #7b2fff;
            --accent: #ff2d6a;
            --bg-dark: #0a0a12;
            --bg-panel: #12121c;
            --text: #e0e0e0;
            --glow: rgba(0, 247, 255, 0.5);
        }

        body {
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
            overflow-y: auto;
        }

        /* Background Grid */
        .bg-grid {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 247, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 247, 255, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            z-index: -1;
        }

        /* Main Container */
        .container {
            display: grid;
            grid-template-columns: clamp(250px, 20vw, 300px) minmax(0, 1fr) clamp(250px, 20vw, 300px);
            grid-template-rows: auto minmax(0, 1fr);
            height: 100vh;
            min-height: 700px;
            gap: 20px;
            padding: 20px;
        }

        /* Header */
        header {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            background: var(--bg-panel);
            border-radius: 20px;
            border: 1px solid rgba(0, 247, 255, 0.2);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo h1 {
            font-size: 2rem;
            font-weight: 300;
            letter-spacing: 8px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(0, 247, 255, 0.1);
            border-radius: 20px;
            border: 1px solid var(--primary);
        }

        .status-dot {
            width: 10px;
            height: 10px;
            background: var(--primary);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px var(--primary); }
            50% { opacity: 0.5; box-shadow: 0 0 20px var(--primary); }
        }

        /* Side Panels */
        .panel {
            background: var(--bg-panel);
            border-radius: 20px;
            border: 1px solid rgba(0, 247, 255, 0.1);
            padding: 20px;
            overflow-y: auto;
            min-height: 0;
        }

        .panel h2 {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 247, 255, 0.2);
        }

        /* Stats Panel */
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            margin-bottom: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            border-left: 3px solid var(--primary);
        }

        .stat-label { color: #888; font-size: 0.85rem; }
        .stat-value { color: var(--primary); font-weight: bold; }

        /* Main Content - AURA Core */
        main {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            position: relative;
            min-height: 0;
            height: 100%;
            width: 100%;
            padding-top: 20px;
            overflow: hidden;
        }

        /* The AURA Ring */
        .aura-core {
            position: relative;
            width: clamp(200px, 30vh, 300px);
            height: clamp(200px, 30vh, 300px);
            flex-shrink: 0;
        }

        .core-ring {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px solid transparent;
        }

        .ring-1 {
            border-top: 3px solid var(--primary);
            border-bottom: 3px solid var(--secondary);
            animation: rotate 8s linear infinite;
        }

        .ring-2 {
            width: 80%;
            height: 80%;
            top: 10%;
            left: 10%;
            border-left: 3px solid var(--accent);
            border-right: 3px solid var(--primary);
            animation: rotate 6s linear infinite reverse;
        }

        .ring-3 {
            width: 60%;
            height: 60%;
            top: 20%;
            left: 20%;
            border: 2px solid var(--primary);
            animation: pulse-ring 3s ease-in-out infinite;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes pulse-ring {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 1; }
        }

        .core-center {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 120px;
            height: 120px;
            background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: glow 2s ease-in-out infinite;
        }

        @keyframes glow {
            0%, 100% { box-shadow: 0 0 30px var(--glow); }
            50% { box-shadow: 0 0 60px var(--glow), 0 0 100px var(--secondary); }
        }

        .core-text {
            font-size: 2.5rem;
            font-weight: bold;
            letter-spacing: 5px;
            color: white;
            text-shadow: 0 0 20px var(--primary);
            z-index: 2;
        }

        /* State Animations */
        .aura-core.listening .ring-1 { animation: rotate 2s linear infinite; border-color: var(--primary); }
        .aura-core.listening .ring-2 { animation: rotate 1.5s linear infinite reverse; border-color: var(--primary); }
        .aura-core.listening .core-center { animation: core-listening-pulse 1s ease-in-out infinite; }
        
        @keyframes core-listening-pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); box-shadow: 0 0 40px var(--glow); }
            50% { transform: translate(-50%, -50%) scale(1.1); box-shadow: 0 0 80px var(--primary); }
        }

        .aura-core.thinking .ring-1 { animation: rotate 4s linear infinite; border-color: var(--secondary); }
        .aura-core.thinking .ring-2 { animation: rotate 3s linear infinite reverse; border-color: var(--secondary); }
        .aura-core.thinking .core-center { 
            animation: core-thinking-pulse 2s ease-in-out infinite;
            background: radial-gradient(circle, var(--secondary) 0%, transparent 70%);
        }

        @keyframes core-thinking-pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.7; }
            50% { transform: translate(-50%, -50%) scale(1); opacity: 1; box-shadow: 0 0 50px var(--secondary); }
        }

        /* Voice Status */
        .voice-status {
            margin-top: 30px;
            text-align: center;
        }

        .voice-status.active {
            color: var(--primary);
        }

        .voice-wave {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            height: 40px;
            margin-top: 15px;
        }

        .wave-bar {
            width: 4px;
            height: 20px;
            background: var(--primary);
            border-radius: 2px;
            animation: wave 1s ease-in-out infinite;
        }

        .wave-bar:nth-child(2) { animation-delay: 0.1s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.3s; }
        .wave-bar:nth-child(5) { animation-delay: 0.4s; }

        @keyframes wave {
            0%, 100% { height: 10px; }
            50% { height: 40px; }
        }

        /* Chat Area */
        .chat-container {
            flex: 1 1 0%;
            width: 100%;
            margin-top: 20px;
            background: var(--bg-panel);
            border-radius: 20px;
            border: 1px solid rgba(0, 247, 255, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            min-height: 0;
        }

        .chat-messages {
            flex: 1 1 0%;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-height: 0;
        }

        .message {
            max-width: 80%;
            padding: 15px 20px;
            border-radius: 15px;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .message.user {
            background: rgba(123, 47, 255, 0.2);
            border: 1px solid rgba(123, 47, 255, 0.3);
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }

        .message.aura {
            background: rgba(0, 247, 255, 0.1);
            border: 1px solid rgba(0, 247, 255, 0.2);
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }

        .message .time {
            font-size: 0.7rem;
            color: #666;
            margin-top: 5px;
        }

        .chat-input-container {
            padding: 20px;
            border-top: 1px solid rgba(0, 247, 255, 0.1);
            display: flex;
            gap: 10px;
            flex-shrink: 0;
            background: var(--bg-panel);
            z-index: 10;
        }

        .chat-input {
            flex: 1;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 247, 255, 0.2);
            border-radius: 30px;
            color: white;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }

        .chat-input:focus {
            border-color: var(--primary);
        }

        .chat-input::placeholder {
            color: #666;
        }

        .send-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            border-radius: 30px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px var(--glow);
        }

        /* Mic Button */
        .mic-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--accent);
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            transition: all 0.3s;
            pointer-events: auto;
            z-index: 1000;
            position: relative;
        }

        .mic-btn:hover {
            box-shadow: 0 0 20px var(--accent);
            transform: scale(1.1);
        }

        .mic-btn.listening {
            animation: mic-pulse 1s infinite;
            background: #00ff00;
        }

        @keyframes mic-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        /* Chat input container */
        .chat-input-container {
            padding: 20px;
            border-top: 1px solid rgba(0, 247, 255, 0.1);
            display: flex;
            gap: 10px;
            flex-shrink: 0;
            background: var(--bg-panel);
            z-index: 10;
            position: relative;
        }

        .chat-input {
            flex: 1;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 247, 255, 0.2);
            border-radius: 30px;
            color: white;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
            z-index: 1;
        }

        .chat-input:focus {
            border-color: var(--primary);
        }

        .chat-input::placeholder {
            color: #666;
        }

        .send-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            border-radius: 30px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            z-index: 1;
        }

        .send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px var(--glow);
        }

        /* Mic Button */
        .mic-btn {
            width: 50px;
            min-width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #ff2d6a;
            border: 2px solid #ff2d6a;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            transition: all 0.3s;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .mic-btn:hover {
            box-shadow: 0 0 25px #ff2d6a;
            transform: scale(1.1);
            background: #ff4477;
        }

        .mic-btn.listening {
            animation: mic-pulse 1s infinite;
            background: #00ff88;
            border-color: #00ff88;
        }

        @keyframes mic-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.15); }
        }

        /* Goals Panel */
        .goal-item {
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            border-left: 3px solid var(--secondary);
        }

        .goal-item .priority {
            font-size: 0.7rem;
            color: var(--secondary);
            text-transform: uppercase;
        }

        .goal-item .text {
            margin-top: 5px;
            font-size: 0.9rem;
        }

        /* Tools Panel */
        .tool-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        .tool-btn {
            padding: 15px;
            background: rgba(0, 247, 255, 0.1);
            border: 1px solid rgba(0, 247, 255, 0.2);
            border-radius: 10px;
            color: var(--text);
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }

        .tool-btn:hover {
            background: rgba(0, 247, 255, 0.2);
            border-color: var(--primary);
        }

        .tool-btn .icon {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }

        .tool-btn .label {
            font-size: 0.8rem;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-dark);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }

        /* Responsive */
        @media (max-width: 1024px) {
            .container {
                grid-template-columns: 1fr;
                grid-template-rows: auto auto 1fr auto;
                height: auto;
                min-height: 100vh;
            }
            main {
                min-height: 500px;
            }
        }
    </style>
</head>
<body>
    <div class="bg-grid"></div>
    
    <div class="container">
        <!-- Header -->
        <header>
            <div class="logo">
                <div class="aura-core" style="width:50px;height:50px;">
                    <div class="core-ring ring-3" style="width:60%;height:60%;top:20%;left:20%;"></div>
                    <div class="core-center" style="width:30px;height:30px;">
                        <span style="font-size:0.8rem;font-weight:bold;">A</span>
                    </div>
                </div>
                <h1>AURA</h1>
            </div>
            <div class="status-badge">
                <div class="status-dot"></div>
                <span id="systemStatus">Online</span>
            </div>
        </header>

        <!-- Left Panel - Stats -->
        <div class="panel">
            <h2>🧠 Memory</h2>
            <div class="stat-item">
                <span class="stat-label">Working Memory</span>
                <span class="stat-value" id="workingMemory">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Knowledge Base</span>
                <span class="stat-value" id="knowledgeBase">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Tasks Completed</span>
                <span class="stat-value" id="tasksCompleted">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Success Rate</span>
                <span class="stat-value" id="successRate">0%</span>
            </div>
            
            <h2 style="margin-top:30px;">⚡ Governor</h2>
            <div class="stat-item">
                <span class="stat-label">Total Requests</span>
                <span class="stat-value" id="totalRequests">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Cost Today</span>
                <span class="stat-value" id="costToday">$0.00</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Status</span>
                <span class="stat-value" id="governorStatus">Active</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Cost Limit</span>
                <span class="stat-value" id="costLimit">$10.00</span>
            </div>
            
            <h2 style="margin-top:30px;">🔌 Model</h2>
            <div class="stat-item">
                <span class="stat-label">Provider</span>
                <span class="stat-value" id="modelProvider">Local</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Model</span>
                <span class="stat-value" id="modelName">qwen2.5-coder</span>
            </div>
        </div>

        <!-- Main Content -->
        <main>
            <div class="aura-core" id="auraCore">
                <div class="core-ring ring-1"></div>
                <div class="core-ring ring-2"></div>
                <div class="core-ring ring-3"></div>
                <div class="core-center">
                    <span class="core-text">A</span>
                </div>
            </div>
            
            <div class="voice-status" id="voiceStatus">
                <div id="voicePrompt">Click microphone to enable voice</div>
                <div class="voice-wave" id="voiceWave" style="visibility:hidden;">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
            </div>

            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="message aura">
                        Hello! I am AURA. Your autonomous AI assistant. How can I help you today?
                        <div class="time">Just now</div>
                    </div>
                </div>
                <div class="chat-input-container">
                    <input type="text" class="chat-input" id="chatInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                    <button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
                    <button class="send-btn" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </main>

        <!-- Right Panel - Tools -->
        <div class="panel">
            <h2>Quick Tools</h2>
            <div class="tool-grid">
                <div class="tool-btn" onclick="quickAction('weather')">
                    <div class="icon">🌤️</div>
                    <div class="label">Weather</div>
                </div>
                <div class="tool-btn" onclick="quickAction('calc')">
                    <div class="icon">🔢</div>
                    <div class="label">Calculator</div>
                </div>
                <div class="tool-btn" onclick="quickAction('search')">
                    <div class="icon">🔍</div>
                    <div class="label">Search</div>
                </div>
                <div class="tool-btn" onclick="quickAction('code')">
                    <div class="icon">💻</div>
                    <div class="label">Code</div>
                </div>
                <div class="tool-btn" onclick="quickAction('voice')">
                    <div class="icon">🔊</div>
                    <div class="label">Speak</div>
                </div>
                <div class="tool-btn" onclick="quickAction('learn')">
                    <div class="icon">📚</div>
                    <div class="label">Learn</div>
                </div>
            </div>
            
            <h2 style="margin-top:30px;">Recent Activity</h2>
            <div id="activityList">
                <div class="stat-item">
                    <span class="stat-label">No recent activity</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let micActive = false;

        function connect() {
            ws = new WebSocket('ws://' + location.host + '/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function() {
                setTimeout(connect, 3000);
            };
        }

        function handleMessage(data) {
            const core = document.getElementById('auraCore');
            if (data.type === 'response') {
                core.classList.remove('thinking');
                addMessage(data.content, 'aura');
                speakText(data.content);
            } else if (data.type === 'status') {
                updateStatus(data.data);
            } else if (data.type === 'voice') {
                showVoiceIndicator(data.active);
            }
        }

        function showVoiceIndicator(active) {
            const core = document.getElementById('auraCore');
            const wave = document.getElementById('voiceWave');
            if (active) {
                core.classList.add('listening');
                wave.style.visibility = 'visible';
            } else {
                core.classList.remove('listening');
                wave.style.visibility = 'hidden';
            }
        }

        function addMessage(text, sender) {
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = `message ${sender}`;
            div.innerHTML = `${text}<div class="time">${new Date().toLocaleTimeString()}</div>`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function sendMessage() {
            const input = document.getElementById('chatInput');
            const core = document.getElementById('auraCore');
            const text = input.value.trim();
            if (!text) return;
            
            addMessage(text, 'user');
            input.value = '';
            
            // Show thinking state
            core.classList.add('thinking');
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'message', content: text}));
            }
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendMessage();
        }

        let recognition = null;
        let isListening = false;
        let wakeWordDetected = false;
        const WAKE_WORD = "aura";
        
        function toggleMic() {
            const btn = document.getElementById('micBtn');
            
            console.log("Toggle mic clicked, isListening:", isListening);
            
            if (!isListening) {
                // Check for SpeechRecognition API
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    document.getElementById('voicePrompt').innerHTML = '⚠️ Voice not supported. Use Chrome/Edge.';
                    alert("Your browser doesn't support voice recognition. Please use Chrome or Edge.");
                    return;
                }
                
                // Create recognition instance
                if (!recognition) {
                    recognition = new SpeechRecognition();
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.lang = 'en-US';
                    
                    recognition.onresult = function(event) {
                        let finalTranscript = '';
                        let interimTranscript = '';
                        
                        for (let i = event.resultIndex; i < event.results.length; i++) {
                            if (event.results[i].isFinal) {
                                finalTranscript += event.results[i][0].transcript;
                            } else {
                                interimTranscript += event.results[i][0].transcript;
                            }
                        }
                        
                        const transcript = (finalTranscript || interimTranscript).trim().toLowerCase();
                        console.log("Heard:", transcript);
                        
                        if (!wakeWordDetected && transcript.includes(WAKE_WORD)) {
                            wakeWordDetected = true;
                            document.getElementById('voicePrompt').innerHTML = '🎤 AURA activated! Speak now...';
                            document.getElementById('auraCore').classList.add('listening');
                            document.getElementById('voiceWave').style.visibility = 'visible';
                            
                            if (ws && ws.readyState === WebSocket.OPEN) {
                                ws.send(JSON.stringify({type: 'speak', content: "Yes, I'm listening"}));
                            }
                            
                            setTimeout(() => { wakeWordDetected = false; }, 5000);
                            return;
                        }
                        
                        if (wakeWordDetected && finalTranscript) {
                            const command = finalTranscript.toLowerCase().replace(WAKE_WORD, '').trim();
                            if (command) {
                                document.getElementById('chatInput').value = command;
                                sendMessage();
                            }
                            
                            wakeWordDetected = false;
                            document.getElementById('voicePrompt').innerHTML = '🎤 Say "AURA" to activate';
                            document.getElementById('auraCore').classList.remove('listening');
                            document.getElementById('voiceWave').style.visibility = 'hidden';
                        }
                    };
                    
                    recognition.onerror = function(event) {
                        console.error("Speech error:", event.error);
                        if (event.error === 'not-allowed') {
                            document.getElementById('voicePrompt').innerHTML = '⚠️ Mic blocked - check permissions';
                        } else if (event.error !== 'aborted') {
                            document.getElementById('voicePrompt').innerHTML = '⚠️ Error: ' + event.error;
                        }
                    };
                    
                    recognition.onend = function() {
                        console.log("Speech recognition ended");
                        if (isListening && recognition) {
                            try { recognition.start(); } catch(e) { 
                                console.log("Restart failed:", e); 
                            }
                        }
                    };
                }
                
                try {
                    recognition.start();
                    isListening = true;
                    btn.classList.add('listening');
                    document.getElementById('voicePrompt').innerHTML = '🎤 Listening for "AURA"...';
                    document.getElementById('voiceWave').style.display = 'flex';
                } catch (err) {
                    console.error("Start error:", err);
                    document.getElementById('voicePrompt').innerHTML = '⚠️ Click again to enable';
                }
            } else {
                if (recognition) {
                    recognition.stop();
                }
                isListening = false;
                btn.classList.remove('listening');
                document.getElementById('voicePrompt').innerHTML = '🎤 Click mic to start';
                document.getElementById('voiceWave').style.display = 'none';
            }
        }
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const rec = new SpeechRecognition();
            
            rec.continuous = true;
            rec.interimResults = true;
            rec.lang = 'en-US';
            
            rec.onresult = function(event) {
                let interimTranscript = '';
                let finalTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }
                
                const transcript = (finalTranscript || interimTranscript).trim().toLowerCase();
                console.log("Heard:", transcript);
                
                if (!wakeWordDetected && transcript.includes(WAKE_WORD)) {
                    wakeWordDetected = true;
                    document.getElementById('voiceStatus').innerHTML = '🎤 AURA activated! Speak now...';
                    document.getElementById('voiceStatus').classList.add('active');
                    document.getElementById('voiceWave').style.display = 'flex';
                    
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'speak', content: "Yes, I'm listening"}));
                    }
                    
                    setTimeout(() => { wakeWordDetected = false; }, 5000);
                    return;
                }
                
                if (wakeWordDetected && finalTranscript) {
                    const command = finalTranscript.toLowerCase().replace(WAKE_WORD, '').trim();
                    if (command) {
                        document.getElementById('chatInput').value = command;
                        sendMessage();
                    }
                    
                    wakeWordDetected = false;
                    document.getElementById('voiceStatus').innerHTML = '🎤 Say "AURA" to activate';
                    document.getElementById('voiceStatus').classList.remove('active');
                    document.getElementById('voiceWave').style.display = 'none';
                }
            };
            
            rec.onerror = function(event) {
                console.error("Speech error:", event.error);
                document.getElementById('voiceStatus').innerHTML = '⚠️ Mic error: ' + event.error;
                isListening = false;
                document.getElementById('micBtn').classList.remove('listening');
            };
            
            rec.onend = function() {
                console.log("Speech recognition ended");
                if (isListening) {
                    try { rec.start(); } catch(e) { console.log("Restart failed:", e); }
                }
            };
            
            return rec;
        }
        
        function toggleMic() {
            const btn = document.getElementById('micBtn');
            const status = document.getElementById('voiceStatus');
            
            console.log("Toggle mic clicked, isListening:", isListening);
            
            if (!isListening) {
                // Check for SpeechRecognition API
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    status.innerHTML = '⚠️ Voice not supported. Use Chrome/Edge.';
                    alert("Your browser doesn't support voice recognition. Please use Chrome or Edge.");
                    return;
                }
                
                // Create recognition instance
                if (!recognition) {
                    recognition = new SpeechRecognition();
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.lang = 'en-US';
                    
                    recognition.onresult = function(event) {
                        let finalTranscript = '';
                        let interimTranscript = '';
                        
                        for (let i = event.resultIndex; i < event.results.length; i++) {
                            if (event.results[i].isFinal) {
                                finalTranscript += event.results[i][0].transcript;
                            } else {
                                interimTranscript += event.results[i][0].transcript;
                            }
                        }
                        
                        const transcript = (finalTranscript || interimTranscript).trim().toLowerCase();
                        console.log("Heard:", transcript);
                        
                        if (!wakeWordDetected && transcript.includes(WAKE_WORD)) {
                            wakeWordDetected = true;
                            status.innerHTML = '🎤 AURA activated! Speak now...';
                            status.classList.add('active');
                            document.getElementById('voiceWave').style.display = 'flex';
                            
                            if (ws && ws.readyState === WebSocket.OPEN) {
                                ws.send(JSON.stringify({type: 'speak', content: "Yes, I'm listening"}));
                            }
                            
                            setTimeout(() => { wakeWordDetected = false; }, 5000);
                            return;
                        }
                        
                        if (wakeWordDetected && finalTranscript) {
                            const command = finalTranscript.toLowerCase().replace(WAKE_WORD, '').trim();
                            if (command) {
                                document.getElementById('chatInput').value = command;
                                sendMessage();
                            }
                            
                            wakeWordDetected = false;
                            status.innerHTML = '🎤 Say "AURA" to activate';
                            status.classList.remove('active');
                            document.getElementById('voiceWave').style.display = 'none';
                        }
                    };
                    
                    recognition.onerror = function(event) {
                        console.error("Speech error:", event.error);
                        if (event.error === 'not-allowed') {
                            document.getElementById('voicePrompt').innerHTML = '⚠️ Mic blocked - check permissions';
                        } else if (event.error !== 'aborted') {
                            document.getElementById('voicePrompt').innerHTML = '⚠️ Error: ' + event.error;
                        }
                    };
                    
                    recognition.onend = function() {
                        console.log("Speech recognition ended");
                        if (isListening && recognition) {
                            try { recognition.start(); } catch(e) { 
                                console.log("Restart failed:", e); 
                            }
                        }
                    };
                }
                
                try {
                    recognition.start();
                    isListening = true;
                    btn.classList.add('listening');
                    document.getElementById('voicePrompt').innerHTML = '🎤 Listening for "AURA"...';
                    document.getElementById('voiceWave').style.display = 'flex';
                } catch (err) {
                    console.error("Start error:", err);
                    document.getElementById('voicePrompt').innerHTML = '⚠️ Click again to enable';
                }
            } else {
                if (recognition) {
                    recognition.stop();
                }
                isListening = false;
                btn.classList.remove('listening');
                document.getElementById('voicePrompt').innerHTML = '🎤 Click mic to start';
                document.getElementById('voiceWave').style.display = 'none';
            }
        }
                    
                    recognition.start();
                    isListening = true;
                    btn.classList.add('listening');
                    status.innerHTML = '🎤 Listening for "AURA"...';
                    document.getElementById('voiceWave').style.display = 'flex';
                } catch (err) {
                    console.error("Start error:", err);
                    status.innerHTML = '⚠️ Please click to allow mic access';
                    alert("Microphone access is required for voice commands. Please click the mic icon and allow permission in your browser.");
                }
            } else {
                recognition.stop();
                isListening = false;
                btn.classList.remove('listening');
                status.innerHTML = '🎤 Click mic to start';
                document.getElementById('voiceWave').style.display = 'none';
            }
        }
        
        function quickAction(action) {
            const input = document.getElementById('chatInput');
            switch(action) {
                case 'weather':
                    input.value = "What's the weather today?";
                    break;
                case 'calc':
                    input.value = "Calculate ";
                    break;
                case 'search':
                    input.value = "Search for ";
                    break;
                case 'code':
                    input.value = "Write code to ";
                    break;
                case 'voice':
                    input.value = "Speak: ";
                    break;
                case 'learn':
                    input.value = "Learn about ";
                    break;
            }
        }

        function showVoiceIndicator(active) {
            document.getElementById('voiceWave').style.display = active ? 'flex' : 'none';
            document.getElementById('voiceStatus').classList.toggle('active', active);
        }

        function updateStatus(data) {
            if (data.memory) {
                document.getElementById('workingMemory').textContent = data.memory.working_memory_items || 0;
                document.getElementById('knowledgeBase').textContent = data.memory.total_knowledge || 0;
                document.getElementById('tasksCompleted').textContent = data.memory.tasks_completed || 0;
                document.getElementById('successRate').textContent = (data.memory.success_rate || 0).toFixed(1) + '%';
            }
            if (data.governor) {
                document.getElementById('totalRequests').textContent = data.governor.requests_today || 0;
                document.getElementById('costToday').textContent = '$' + (data.governor.daily_cost || 0).toFixed(2);
                document.getElementById('governorStatus').textContent = data.governor.paused ? 'Paused' : 'Active';
                document.getElementById('costLimit').textContent = '$' + (data.governor.cost_limit || 10).toFixed(2);
            }
        }

        function speakText(text) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'speak', content: text}));
            }
        }

        // Auto-refresh status every 5 seconds
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'status'}));
            }
        }, 5000);

        // Removed auto-start of voice listening as browsers block it on load.
        // Users must click the mic button once to grant permission.
        window.onload = function() {
            console.log("AURA Dashboard loaded - waiting for user interaction for mic.");
        };

        connect();
    </script>
</body>
</html>
"""


def set_components(memory, governor, voice=None, aura_loop=None):
    global _memory, _governor, _voice, _aura_loop
    _memory = memory
    _governor = governor
    _voice = voice
    _aura_loop = aura_loop


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTML_PAGE


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "message":
                if _aura_loop:
                    result = _aura_loop.run_once(message["content"])
                    await websocket.send_json(
                        {"type": "response", "content": result[:500]}
                    )
                    if _voice:
                        _voice.speak_background(result[:200])

            elif message.get("type") == "status":
                if _memory and _governor:
                    await websocket.send_json(
                        {
                            "type": "status",
                            "data": {
                                "memory": _memory.get_stats(),
                                "governor": _governor.get_status(),
                            },
                        }
                    )

            elif message.get("type") == "speak":
                if _voice:
                    _voice.speak(message["content"])

            elif message.get("type") == "audio":
                try:
                    import tempfile
                    import os
                    import numpy as np

                    audio_data = bytes(message["data"])

                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".webm"
                    )
                    temp_file.write(audio_data)
                    temp_file.close()

                    model = get_whisper_model()
                    result = model.transcribe(temp_file.name)
                    text = result["text"].strip()

                    os.unlink(temp_file.name)

                    if text and text.lower() != "aura":
                        await websocket.send_json({"type": "transcript", "text": text})

                        if _aura_loop:
                            response = _aura_loop.run_once(text)
                            await websocket.send_json(
                                {"type": "response", "content": response[:500]}
                            )
                            if _voice:
                                _voice.speak_background(response[:200])
                    elif text and text.lower() == "aura":
                        await websocket.send_json({"type": "voice", "active": True})
                        if _voice:
                            _voice.speak("Yes, I'm listening")

                except Exception as e:
                    print(f"Audio error: {e}")

    except WebSocketDisconnect:
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
                        if conn in _active_connections:
                            _active_connections.remove(conn)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Broadcast error: {e}")
            await asyncio.sleep(5)


def start_dashboard(memory, governor, voice=None, aura_loop=None, port=8080):
    """Programmatic entry point for starting the dashboard."""
    set_components(memory, governor, voice, aura_loop)

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    # Run uvicorn and our status broadcaster in the same event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Add the broadcaster to the loop
    loop.create_task(broadcast_status())

    # Run the server
    try:
        loop.run_until_complete(server.serve())
    except Exception as e:
        print(f"Dashboard server stopped: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
