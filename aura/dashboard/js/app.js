    <script>
        let ws = null;
        let micActive = false;

        function connect() {
            ws = new WebSocket('ws://' + location.host + '/ws');
            
            let pongReceived = true;
            let pingInterval;
            let reconnectAttempts = 0;
            const MAX_RECONNECT = 2;
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'pong') {
                    pongReceived = true;
                    reconnectAttempts = 0;
                }
                handleMessage(data);
            };
            
            ws.onerror = function(error) {
                console.error("WebSocket error:", error);
                const core = document.getElementById('auraCore');
                core.classList.remove('thinking');
                ws.close();
            };
            
            ws.onopen = function() {
                pongReceived = true;
                reconnectAttempts = 0;
                // Start heartbeat - ping every 15 seconds
                pingInterval = setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        pongReceived = false;
                        ws.send(JSON.stringify({type: 'ping'}));
                        // If no pong for 15s (one heartbeat), reconnect
                        setTimeout(() => {
                            if (!pongReceived) {
                                reconnectAttempts++;
                                console.log("No pong received, attempt:", reconnectAttempts);
                                if (reconnectAttempts >= MAX_RECONNECT) {
                                    console.log("Heartbeat failed, reconnecting...");
                                    ws.close();
                                }
                            }
                        }, 15000);
                    }
                }, 15000);
            };
            
            ws.onclose = function() {
                clearInterval(pingInterval);
                setTimeout(connect, 3000);
            };
        }

        function handleMessage(data) {
            const core = document.getElementById('auraCore');
            if (data.type === 'response') {
                core.classList.remove('thinking');
                core.classList.add('speaking');
                addMessage(data.content, 'aura');
                speakText(data.content);
            } else if (data.type === 'status') {
                updateStatus(data.data);
            } else if (data.type === 'voice') {
                showVoiceIndicator(data.active);
            } else if (data.type === 'speaking_done') {
                core.classList.remove('speaking');
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
            // Use requestAnimationFrame to ensure scroll happens after DOM paint
            requestAnimationFrame(() => {
                container.scrollTop = container.scrollHeight;
            });
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
            } else {
                // Connection not open - remove thinking state
                core.classList.remove('thinking');
            }
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendMessage();
        }

        let recognition = null;
        let isListening = false;
        let wakeWordDetected = false;
        let isSpeaking = false;
        let audioContext = null;
        let analyser = null;
        let micStream = null;
        const WAKE_WORD = "aura";
        
        // Web Audio API for mic visualization
        function startAudioVisualization() {
            if (audioContext) return;
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    micStream = audioContext.createMediaStreamSource(stream);
                    micStream.connect(analyser);
                    visualize();
                })
                .catch(err => console.log("Mic visualization denied:", err));
        }
        
        function visualize() {
            if (!isListening || !analyser) return;
            
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate RMS volume
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / dataArray.length);
            const volume = Math.min(rms / 128, 1);
            
            // Apply to rings - box-shadow intensity and rotation speed
            const core = document.getElementById('auraCore');
            const intensity = Math.floor(volume * 30);
            const speed = 2 - volume * 1.5; // Faster when louder
            
            core.style.setProperty('--ring-glow', `rgba(0, 247, 255, ${volume * 0.5})`);
            core.style.animationDuration = `${speed}s`;
            
            requestAnimationFrame(visualize);
        }
        
        function stopAudioVisualization() {
            if (micStream) {
                micStream.getTracks().forEach(t => t.stop());
                micStream = null;
            }
            if (audioContext) {
                audioContext.close();
                audioContext = null;
                analyser = null;
            }
        }
        
        function toggleMic() {
            const btn = document.getElementById('micBtn');
            const status = document.getElementById('voicePrompt');
            const core = document.getElementById('auraCore');
            const wave = document.getElementById('voiceWave');
            
            if (!isListening) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    status.innerHTML = '⚠️ Voice not supported.';
                    return;
                }
                
                if (!recognition) {
                    recognition = new SpeechRecognition();
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.lang = 'en-US';
                    
                    recognition.onresult = function(event) {
                        let finalTranscript = '';
                        let interimTranscript = '';
                        for (let i = event.resultIndex; i < event.results.length; i++) {
                            if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
                            else interimTranscript += event.results[i][0].transcript;
                        }
                        
                        // Interruption support - stop speaking if user starts talking
                        if (isSpeaking && interimTranscript.trim()) {
                            if (ws && ws.readyState === WebSocket.OPEN) {
                                ws.send(JSON.stringify({type: 'stop_speech'}));
                            }
                            isSpeaking = false;
                            const core = document.getElementById('auraCore');
                            core.classList.remove('speaking');
                        }
                        
                        const transcript = (finalTranscript || interimTranscript).trim().toLowerCase();
                        if (!wakeWordDetected && transcript.includes(WAKE_WORD)) {
                            wakeWordDetected = true;
                            status.innerHTML = '🎤 AURA activated!';
                            core.classList.add('listening');
                            wave.style.visibility = 'visible';
                            if (ws && ws.readyState === WebSocket.OPEN) {
                                ws.send(JSON.stringify({type: 'stop_speech'}));
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
                            core.classList.remove('listening');
                            wave.style.visibility = 'hidden';
                        }
                    };
                    
                    recognition.onend = function() {
                        if (isListening) try { recognition.start(); } catch(e) {}
                    };
                    
                    recognition.onerror = function(event) {
                        console.error("Speech error:", event.error);
                        if (event.error === 'not-allowed') {
                            // Show mic permission recovery UI
                            status.innerHTML = `
                                <div style="text-align:left; padding:10px; background:rgba(255,0,0,0.1); border-radius:8px;">
                                    <strong>⚠️ Mic blocked</strong>
                                    <p style="font-size:0.85rem; margin:8px 0;">To enable:</p>
                                    <ol style="font-size:0.8rem; padding-left:20px; margin:0;">
                                        <li>Click the lock 🔒 icon in browser address bar</li>
                                        <li>Click "Microphone" → "Allow"</li>
                                        <li>Refresh this page</li>
                                    </ol>
                                </div>
                            `;
                        }
                    };
                }
                
                try {
                    recognition.start();
                    isListening = true;
                    btn.classList.add('listening');
                    status.innerHTML = '🎤 Listening for "AURA"...';
                    startAudioVisualization();
                } catch (err) {}
            } else {
                if (recognition) recognition.stop();
                isListening = false;
                btn.classList.remove('listening');
                status.innerHTML = '🎤 Click mic to start';
                core.classList.remove('listening');
                wave.style.visibility = 'hidden';
                stopAudioVisualization();
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
            isSpeaking = true;
            // Remove speaking state after estimated speech time (approx 3 seconds per 100 chars)
            const estimatedTime = Math.max(2000, text.length * 30);
            setTimeout(() => {
                const core = document.getElementById('auraCore');
                core.classList.remove('speaking');
                isSpeaking = false;
            }, estimatedTime);
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
