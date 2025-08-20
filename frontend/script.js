class WheelOfFortuneGame {
    constructor() {
        this.ws = null;
        this.playerId = null;
        this.playerName = null;
        this.roomId = null;
        this.gameState = 'waiting';
        this.canBuzz = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.initializeMuteState();
        this.showRoomModal();
    }
    
    initializeElements() {
        // Main elements
        this.hostMessage = document.getElementById('host-message');
        this.puzzleCategory = document.getElementById('puzzle-category');
        this.puzzleBoard = document.getElementById('puzzle-board');
        this.gameStatus = document.getElementById('game-status');
        this.roundNumber = document.getElementById('round-number');
        
        // Controls
        this.startGameBtn = document.getElementById('start-game-btn');
        this.buzzBtn = document.getElementById('buzz-btn');
        this.answerSection = document.getElementById('answer-section');
        this.answerInput = document.getElementById('answer-input');
        this.submitAnswerBtn = document.getElementById('submit-answer-btn');
        
        // Sidebar
        this.playersList = document.getElementById('players-list');
        this.gameLog = document.getElementById('game-log');
        
        // Scoreboard
        this.scoreboardBottom = document.getElementById('scoreboard-bottom');
        
        // Timer
        this.timerDisplay = document.getElementById('timer-display');
        this.answerTimerDisplay = document.getElementById('answer-timer-display');
        this.answerTimerCountdown = document.getElementById('answer-timer-countdown');
        
        // Mute controls
        this.muteHostBtn = document.getElementById('mute-host-btn');
        this.muteIcon = document.getElementById('mute-icon');
        this.muteSoundBtn = document.getElementById('mute-sound-btn');
        this.muteSoundIcon = document.getElementById('mute-sound-icon');
        this.isHostMuted = localStorage.getItem('hostMuted') === 'true';
        this.isSoundMuted = localStorage.getItem('soundMuted') === 'true';
        
        // Modal
        this.roomModal = document.getElementById('room-modal');
        this.roomIdInput = document.getElementById('room-id-input');
        this.playerNameInput = document.getElementById('player-name-input');
        this.joinRoomBtn = document.getElementById('join-room-btn');
        
        // Display elements
        this.roomIdDisplay = document.getElementById('room-id-display');
        this.playerNameDisplay = document.getElementById('player-name-display');
    }
    
    attachEventListeners() {
        this.startGameBtn.addEventListener('click', () => this.startGame());
        this.buzzBtn.addEventListener('click', () => this.buzzIn());
        this.submitAnswerBtn.addEventListener('click', () => this.submitAnswer());
        this.joinRoomBtn.addEventListener('click', () => this.joinRoom());
        this.muteHostBtn.addEventListener('click', () => this.toggleHostMute());
        this.muteSoundBtn.addEventListener('click', () => this.toggleSoundMute());
        
        // Enter key handlers
        this.answerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitAnswer();
        });
        
        this.playerNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinRoom();
        });
        
        this.roomIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinRoom();
        });
        
        // Space bar for buzz in
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.canBuzz && !this.answerSection.style.display !== 'none') {
                e.preventDefault();
                this.buzzIn();
            }
        });
    }
    
    initializeMuteState() {
        this.updateMuteButton();
    }
    
    toggleHostMute() {
        this.isHostMuted = !this.isHostMuted;
        localStorage.setItem('hostMuted', this.isHostMuted.toString());
        this.updateMuteButton();
        
        // Add feedback
        this.addLogEntry(
            this.isHostMuted ? 'Host voice muted' : 'Host voice unmuted',
            'game-event'
        );
    }
    
    toggleSoundMute() {
        this.isSoundMuted = !this.isSoundMuted;
        localStorage.setItem('soundMuted', this.isSoundMuted.toString());
        this.updateMuteButton();
        
        // Add feedback
        this.addLogEntry(
            this.isSoundMuted ? 'Sound effects muted' : 'Sound effects unmuted',
            'game-event'
        );
    }
    
    updateMuteButton() {
        // Update host mute button
        if (this.isHostMuted) {
            this.muteIcon.textContent = '🔇';
            this.muteHostBtn.classList.add('muted');
            this.muteHostBtn.title = 'Unmute host voice';
        } else {
            this.muteIcon.textContent = '🔊';
            this.muteHostBtn.classList.remove('muted');
            this.muteHostBtn.title = 'Mute host voice';
        }
        
        // Update sound mute button
        if (this.isSoundMuted) {
            this.muteSoundIcon.textContent = '🔇';
            this.muteSoundBtn.classList.add('muted');
            this.muteSoundBtn.title = 'Unmute sound effects';
        } else {
            this.muteSoundIcon.textContent = '🔊';
            this.muteSoundBtn.classList.remove('muted');
            this.muteSoundBtn.title = 'Mute sound effects';
        }
    }
    
    showRoomModal() {
        this.roomModal.style.display = 'flex';
        // Generate a random room ID suggestion
        this.roomIdInput.value = 'room-' + Math.random().toString(36).substr(2, 6);
        this.playerNameInput.focus();
    }
    
    joinRoom() {
        const roomId = this.roomIdInput.value.trim() || 'room-' + Math.random().toString(36).substr(2, 6);
        const playerName = this.playerNameInput.value.trim() || 'Player' + Math.floor(Math.random() * 1000);
        
        if (playerName.length === 0) {
            alert('Please enter a player name');
            return;
        }
        
        this.roomId = roomId;
        this.playerName = playerName;
        
        this.roomModal.style.display = 'none';
        this.connectToGame();
    }
    
    connectToGame() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const encodedPlayerName = encodeURIComponent(this.playerName);
        // Connect to backend server on port 8001
        const backendHost = window.location.hostname === 'localhost' ? 'localhost:8001' : window.location.host;
        const wsUrl = `${protocol}//${backendHost}/ws/${this.roomId}?name=${encodedPlayerName}`;
        
        console.log(`🔗 Attempting WebSocket connection to: ${wsUrl}`);
        this.updateGameStatus('Connecting to game server...');
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ Connected to game server');
            this.updateGameStatus('Connected to server');
            this.addLogEntry('Connected to game server', 'game-event');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = (event) => {
            console.log(`❌ Disconnected from game server (Code: ${event.code})`);
            
            if (event.code === 1006) {
                this.updateGameStatus('⚠️ Backend server not running - check console');
                this.addLogEntry('Backend server appears to be offline. Make sure it\'s running on port 8001.', 'game-event');
            } else {
                this.updateGameStatus('Disconnected from server');
                this.addLogEntry('Disconnected from server', 'game-event');
            }
            
            // Try to reconnect after 3 seconds
            setTimeout(() => {
                if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
                    console.log('🔄 Attempting to reconnect...');
                    this.connectToGame();
                }
            }, 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateGameStatus('Connection error - check if backend is running');
            this.addLogEntry('WebSocket connection failed. Make sure backend server is running.', 'game-event');
        };
    }
    
    handleMessage(message) {
        console.log('Received message:', message);
        
        switch (message.type) {
            case 'welcome':
                this.handleWelcome(message);
                break;
            case 'player_update':
                this.updatePlayersList(message.players);
                break;
            case 'round_start':
                this.handleRoundStart(message);
                break;
            case 'puzzle_update':
                this.updatePuzzle(message);
                break;
            case 'buzzer_active':
                this.handleBuzzerActive(message);
                break;
            case 'player_buzzed':
                this.handlePlayerBuzzed(message);
                break;
            case 'correct_answer':
                this.handleCorrectAnswer(message);
                break;
            case 'incorrect_answer':
                this.handleIncorrectAnswer(message);
                break;
            case 'round_timeout':
                this.handleRoundTimeout(message);
                break;
            case 'timer_update':
                this.handleTimerUpdate(message);
                break;
            case 'timer_expired':
                this.handleTimerExpired(message);
                break;
            case 'timer_resumed':
                this.handleTimerResumed(message);
                break;
            case 'answer_timer_update':
                this.handleAnswerTimerUpdate(message);
                break;
            case 'answer_timeout':
                this.handleAnswerTimeout(message);
                break;
            case 'answer_received':
                this.handleAnswerReceived(message);
                break;
            case 'host_message':
                this.updateHostMessage(message.message, message.audio);
                if (message.round_complete) {
                    this.handleRoundComplete();
                }
                break;
        }
    }
    
    handleWelcome(message) {
        this.playerId = message.player_id;
        this.playerName = message.player_name;
        
        this.roomIdDisplay.textContent = `Room: ${message.room_id}`;
        this.playerNameDisplay.textContent = `Player: ${this.playerName}`;
        
        this.updateHostMessage(message.message, message.audio);
        this.addLogEntry(`Welcome ${this.playerName}!`, 'game-event');
        
        this.startGameBtn.style.display = 'block';
        this.updateGameStatus('Ready to start');
    }
    
    updatePlayersList(players) {
        this.playersList.innerHTML = '';
        this.scoreboardBottom.innerHTML = ''; // Clear previous scores
        
        players.forEach(player => {
            // Update sidebar list
            const playerElement = document.createElement('div');
            playerElement.className = 'player-item';
            if (player.id === this.playerId) {
                playerElement.classList.add('current-player');
            }
            
            playerElement.innerHTML = `
                <div class="player-name">${player.name}</div>
                <div class="player-score">$${player.score}</div>
            `;
            
            this.playersList.appendChild(playerElement);

            // Update bottom scoreboard
            const scoreboardElement = document.createElement('div');
            scoreboardElement.className = 'scoreboard-player';
            if (player.id === this.playerId) {
                scoreboardElement.classList.add('current-player');
            }

            scoreboardElement.innerHTML = `
                <div class="player-name">${player.name}</div>
                <div class="player-score">$${player.score}</div>
            `;

            this.scoreboardBottom.appendChild(scoreboardElement);
        });
    }
    
    handleRoundStart(message) {
        // Play round start sound effect
        this.playRoundStartSound();
        
        this.roundNumber.textContent = message.round_number;
        this.puzzleCategory.textContent = message.category;
        this.puzzleBoard.textContent = message.puzzle_display;
        
        this.updateHostMessage(message.host_message, message.audio);
        this.addLogEntry(message.host_message, 'host-message');
        
        this.startGameBtn.style.display = 'none';
        this.answerSection.style.display = 'none';
        
        // Hide answer timer
        this.answerTimerDisplay.style.display = 'none';
        
        // Reset timer display
        if (message.time_limit) {
            const minutes = Math.floor(message.time_limit / 60);
            const seconds = message.time_limit % 60;
            this.timerDisplay.textContent = `⏱️ ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            this.timerDisplay.className = 'timer-display';
        }
        
        // Don't disable buzzer - it will be activated immediately
        this.updateGameStatus('Round starting... Buzzer will be active soon!');
    }
    
    updatePuzzle(message) {
        this.puzzleBoard.textContent = message.puzzle_display;
        this.puzzleCategory.textContent = message.category;
    }
    
    handleBuzzerActive(message) {
        this.canBuzz = true;
        this.buzzBtn.disabled = false;
        this.updateGameStatus('BUZZER ACTIVE! Press SPACE or click to buzz in!');
        this.addLogEntry(message.message, 'game-event');
        
        // Add visual indication
        this.buzzBtn.style.animation = 'buzz-pulse 0.5s infinite alternate';
    }
    
    handlePlayerBuzzed(message) {
        this.canBuzz = false;
        this.buzzBtn.disabled = true;
        this.buzzBtn.style.animation = '';
        
        const answerTimeLimit = message.answer_time_limit || 10; // fallback to 10 if not provided
        
        if (message.player_name === this.playerName) {
            // This player buzzed in
            this.answerSection.style.display = 'flex';
            this.answerInput.value = ''; // Clear any previous input
            this.answerInput.focus();
            this.submitAnswerBtn.disabled = false; // Ensure submit button is enabled
            this.updateGameStatus(`You buzzed in! Timer paused. You have ${answerTimeLimit} seconds to answer!`);
        } else {
            // Another player buzzed in
            this.updateGameStatus(`${message.player_name} buzzed in. Timer paused. They have ${answerTimeLimit} seconds to answer...`);
        }
        
        // Show answer timer with dynamic value
        this.answerTimerDisplay.style.display = 'block';
        this.answerTimerCountdown.textContent = answerTimeLimit.toString();
        this.answerTimerDisplay.className = 'answer-timer-display';
        
        this.addLogEntry(message.message, 'player-action');
    }
    
    handleCorrectAnswer(message) {
        this.updateHostMessage(message.host_message, message.audio);
        this.addLogEntry(message.host_message, 'host-message');
        
        this.puzzleBoard.textContent = message.answer;
        this.answerSection.style.display = 'none';
        this.answerInput.value = '';
        
        // Hide answer timer
        this.answerTimerDisplay.style.display = 'none';
        
        // Stop timer display
        this.timerDisplay.textContent = '⏱️ SOLVED!';
        this.timerDisplay.className = 'timer-display';
        
        // Update scores
        const scores = message.scores;
        this.updateScoresDisplay(scores);
        
        this.updateGameStatus(`${message.winner} wins the round!`);
        
        // Celebrate if current player won
        if (message.winner === this.playerName) {
            this.celebrateWin();
        }
    }
    
    handleIncorrectAnswer(message) {
        this.updateHostMessage(message.host_message, message.audio);
        this.addLogEntry(message.host_message, 'host-message');
        
        // Show the wrong answer prominently
        this.showIncorrectAnswerFeedback(message.player_name, message.guess);
        
        this.answerSection.style.display = 'none';
        this.answerInput.value = '';
        this.submitAnswerBtn.disabled = false; // Reset submit button
        
        // Hide answer timer
        this.answerTimerDisplay.style.display = 'none';
        
        // If this player guessed wrong, they can't buzz again
        if (message.player_name === this.playerName) {
            this.canBuzz = false;
            this.buzzBtn.disabled = true;
            this.buzzBtn.style.animation = '';
            this.updateGameStatus(`Your answer "${message.guess}" was incorrect. Timer resumed for other players.`);
        } else {
            this.updateGameStatus(`${message.player_name} guessed "${message.guess}" - incorrect! You can still buzz in.`);
        }
    }
    
    handleRoundTimeout(message) {
        this.updateHostMessage(message.host_message, message.audio);
        this.addLogEntry(message.host_message, 'host-message');
        
        this.puzzleBoard.textContent = message.answer;
        this.answerSection.style.display = 'none';
        this.answerInput.value = '';
        
        this.updateGameStatus('Round complete - no winner');
    }
    
    handleTimerUpdate(message) {
        const minutes = Math.floor(message.remaining_time / 60);
        const seconds = message.remaining_time % 60;
        const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Show paused state
        if (message.is_paused) {
            this.timerDisplay.textContent = `⏸️ ${timeString}`;
        } else {
            this.timerDisplay.textContent = `⏱️ ${timeString}`;
        }
        
        // Change timer appearance based on remaining time
        this.timerDisplay.className = 'timer-display';
        
        if (message.is_paused) {
            this.timerDisplay.classList.add('paused');
        } else if (message.remaining_time <= 10) {
            this.timerDisplay.classList.add('critical');
        } else if (message.remaining_time <= 20) {
            this.timerDisplay.classList.add('warning');
        }
    }
    
    handleTimerExpired(message) {
        this.timerDisplay.textContent = '⏱️ 00:00';
        this.timerDisplay.className = 'timer-display critical';
        
        this.updateHostMessage(message.host_message, message.audio);
        this.addLogEntry(message.message, 'game-event');
        
        this.puzzleBoard.textContent = message.answer;
        this.answerSection.style.display = 'none';
        this.answerInput.value = '';
        
        this.updateGameStatus('Time expired! Next round starting...');
        this.handleRoundComplete();
    }
    
    handleAnswerTimerUpdate(message) {
        this.answerTimerCountdown.textContent = message.remaining_time;
        
        // Change styling based on remaining time and pause state
        if (message.is_paused) {
            this.answerTimerDisplay.className = 'answer-timer-display paused';
        } else if (message.remaining_time <= 3) {
            this.answerTimerDisplay.className = 'answer-timer-display critical';
        } else {
            this.answerTimerDisplay.className = 'answer-timer-display';
        }
    }
    
    handleAnswerTimeout(message) {
        this.updateHostMessage(message.host_message, message.audio);
        this.addLogEntry(message.message, 'game-event');
        
        // Hide answer timer and answer section
        this.answerTimerDisplay.style.display = 'none';
        this.answerSection.style.display = 'none';
        this.answerInput.value = '';
        this.submitAnswerBtn.disabled = false;
        
        // If this player timed out, they can't buzz again
        if (message.player_name === this.playerName) {
            this.canBuzz = false;
            this.buzzBtn.disabled = true;
            this.buzzBtn.style.animation = '';
            this.updateGameStatus('You took too long to answer! Other players can still buzz in.');
        } else {
            this.updateGameStatus(`${message.player_name} took too long. You can still buzz in!`);
        }
    }
    
    handleTimerResumed(message) {
        this.addLogEntry(message.message, 'game-event');
        
        // Hide answer timer
        this.answerTimerDisplay.style.display = 'none';
        
        // Only enable buzzer for players who haven't guessed yet
        if (this.canBuzz) {
            this.buzzBtn.disabled = false;
            this.buzzBtn.style.animation = 'buzz-pulse 0.5s infinite alternate';
            this.updateGameStatus('Timer resumed! You can buzz in.');
        } else {
            this.updateGameStatus('Timer resumed! Waiting for other players...');
        }
    }
    
    handleRoundComplete() {
        this.canBuzz = false;
        this.buzzBtn.disabled = true;
        this.buzzBtn.style.animation = '';
        this.answerSection.style.display = 'none';
        
        // Hide answer timer
        this.answerTimerDisplay.style.display = 'none';
        
        this.updateGameStatus('Preparing next round...');
    }
    
    updateScoresDisplay(scores) {
        // Convert scores object to players array format and update display
        const playersArray = Object.keys(scores).map(playerId => ({
            id: playerId,
            name: scores[playerId].name,
            score: scores[playerId].score
        }));
        
        this.updatePlayersList(playersArray);
        console.log('Scores updated:', scores);
    }
    
    showIncorrectAnswerFeedback(playerName, incorrectGuess) {
        // Create temporary wrong answer display
        const wrongAnswerDiv = document.createElement('div');
        wrongAnswerDiv.className = 'wrong-answer-feedback';
        wrongAnswerDiv.innerHTML = `
            <div class="wrong-answer-content">
                <div class="wrong-answer-icon">❌</div>
                <div class="wrong-answer-text">
                    <strong>${playerName}</strong> guessed:<br>
                    <span class="wrong-guess">"${incorrectGuess}"</span>
                </div>
            </div>
        `;
        
        // Add to the page
        document.body.appendChild(wrongAnswerDiv);
        
        // Remove after animation
        setTimeout(() => {
            if (wrongAnswerDiv && wrongAnswerDiv.parentNode) {
                wrongAnswerDiv.parentNode.removeChild(wrongAnswerDiv);
            }
        }, 3000);
    }
    
    celebrateWin() {
        // Add some celebration effects
        document.body.style.animation = 'celebration 1s ease-in-out';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 1000);
    }
    
    startGame() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'start_game'
            }));
            
            this.startGameBtn.style.display = 'none';
            this.updateGameStatus('Starting game...');
        }
    }
    
    buzzIn() {
        if (this.canBuzz && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'buzz_in'
            }));
            
            this.canBuzz = false;
            this.buzzBtn.disabled = true;
            this.buzzBtn.style.animation = '';
        }
    }
    
    submitAnswer() {
        const answer = this.answerInput.value.trim();
        if (answer && this.ws && this.ws.readyState === WebSocket.OPEN) {
            // Disable button immediately to prevent double-submission
            this.submitAnswerBtn.disabled = true;
            this.updateGameStatus('Submitting answer...');
            
            this.ws.send(JSON.stringify({
                type: 'submit_answer',
                answer: answer
            }));
        }
    }
    
    handleAnswerReceived(message) {
        this.updateGameStatus(message.message);
        this.addLogEntry('Answer submitted successfully', 'game-event');
    }
    
    updateHostMessage(message, audioData = null) {
        this.hostMessage.textContent = message;
        
        // Play AI-generated audio if available and not muted
        if (audioData && !this.isHostMuted) {
            this.playHostAudio(audioData);
        }
        // Fallback to speech synthesis if no AI audio and not muted
        else if ('speechSynthesis' in window && !this.isHostMuted) {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.rate = 0.9;
            utterance.pitch = 1.1;
            utterance.volume = 0.8;
            
            // Use a friendly voice if available
            const voices = speechSynthesis.getVoices();
            const friendlyVoice = voices.find(voice => 
                voice.name.includes('Google') || 
                voice.name.includes('Alex') || 
                voice.name.includes('Samantha')
            );
            if (friendlyVoice) {
                utterance.voice = friendlyVoice;
            }
            
            speechSynthesis.speak(utterance);
        }
    }
    
    playHostAudio(base64Audio) {
        try {
            // Convert base64 to blob
            const audioData = atob(base64Audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const view = new Uint8Array(arrayBuffer);
            for (let i = 0; i < audioData.length; i++) {
                view[i] = audioData.charCodeAt(i);
            }
            
            // Create blob and audio element
            const blob = new Blob([arrayBuffer], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            
            // Play the audio
            audio.play().then(() => {
                console.log('🎤 Playing AI-generated host voice');
                // Clean up the URL after playing
                audio.onended = () => URL.revokeObjectURL(audioUrl);
            }).catch(error => {
                console.error('Failed to play AI audio:', error);
                URL.revokeObjectURL(audioUrl);
            });
            
        } catch (error) {
            console.error('Error processing AI audio:', error);
        }
    }
    
    playRoundStartSound() {
        // Check if sound effects are muted
        if (this.isSoundMuted) {
            console.log('🔇 Round start sound muted');
            return;
        }
        
        try {
            // Create AudioContext for sound generation
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create a game show-style chime sound
            const duration = 1.5; // seconds
            const frequency1 = 523.25; // C5
            const frequency2 = 659.25; // E5
            const frequency3 = 783.99; // G5
            
            // Create oscillators for a chord
            const osc1 = audioContext.createOscillator();
            const osc2 = audioContext.createOscillator();
            const osc3 = audioContext.createOscillator();
            
            // Create gain nodes for volume control
            const gain1 = audioContext.createGain();
            const gain2 = audioContext.createGain();
            const gain3 = audioContext.createGain();
            const masterGain = audioContext.createGain();
            
            // Set frequencies
            osc1.frequency.value = frequency1;
            osc2.frequency.value = frequency2;
            osc3.frequency.value = frequency3;
            
            // Set waveform for a bell-like sound
            osc1.type = 'sine';
            osc2.type = 'sine';
            osc3.type = 'sine';
            
            // Connect oscillators to gain nodes
            osc1.connect(gain1);
            osc2.connect(gain2);
            osc3.connect(gain3);
            
            // Connect gain nodes to master gain
            gain1.connect(masterGain);
            gain2.connect(masterGain);
            gain3.connect(masterGain);
            
            // Connect to destination
            masterGain.connect(audioContext.destination);
            
            // Set initial volumes
            const startTime = audioContext.currentTime;
            const endTime = startTime + duration;
            
            // Create envelope (attack, decay, sustain, release)
            masterGain.gain.setValueAtTime(0, startTime);
            masterGain.gain.linearRampToValueAtTime(0.3, startTime + 0.1); // Attack
            masterGain.gain.exponentialRampToValueAtTime(0.1, startTime + 0.3); // Decay
            masterGain.gain.setValueAtTime(0.1, endTime - 0.5); // Sustain
            masterGain.gain.exponentialRampToValueAtTime(0.01, endTime); // Release
            
            // Individual gain envelopes for chord effect
            gain1.gain.setValueAtTime(1, startTime);
            gain2.gain.setValueAtTime(0.8, startTime);
            gain3.gain.setValueAtTime(0.6, startTime);
            
            // Start oscillators
            osc1.start(startTime);
            osc2.start(startTime + 0.05); // Slight delay for chord effect
            osc3.start(startTime + 0.1);
            
            // Stop oscillators
            osc1.stop(endTime);
            osc2.stop(endTime);
            osc3.stop(endTime);
            
            console.log('🔔 Playing round start chime');
            
        } catch (error) {
            console.error('Error playing round start sound:', error);
            // Fallback to a simple beep
            this.playSimpleBeep();
        }
    }
    
    playSimpleBeep() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            
        } catch (error) {
            console.error('Error playing simple beep:', error);
        }
    }
    
    updateGameStatus(status) {
        this.gameStatus.textContent = status;
    }
    
    addLogEntry(message, type = 'general') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
        
        // Insert at the top (newest first)
        this.gameLog.insertBefore(logEntry, this.gameLog.firstChild);
        
        // Keep only last 50 entries (remove from bottom)
        while (this.gameLog.children.length > 50) {
            this.gameLog.removeChild(this.gameLog.lastChild);
        }
    }
}

// Add celebration CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes celebration {
        0%, 100% { transform: scale(1); }
        25% { transform: scale(1.02) rotate(1deg); }
        75% { transform: scale(1.02) rotate(-1deg); }
    }
`;
document.head.appendChild(style);

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new WheelOfFortuneGame();
});

// Handle page visibility changes to manage WebSocket connections
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, you might want to pause some animations
        console.log('Page is hidden');
    } else {
        // Page is visible again
        console.log('Page is visible');
    }
});
