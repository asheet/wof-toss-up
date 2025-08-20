# 🎡 Wheel of Fortune Toss-up Game

A multiplayer web-based game inspired by the "Toss-up" rounds from Wheel of Fortune. Players compete to solve word puzzles as letters are gradually revealed, with the first to buzz in and give the correct answer winning points.

## 🎮 Features

- **Multiplayer Support**: Multiple players can join the same game room
- **Real-time Gameplay**: WebSocket-based real-time communication
- **Game Host**: Interactive host character that announces game events
- **Speech Synthesis**: Host messages are spoken aloud (if browser supports it)
- **Beautiful UI**: Modern, responsive design with smooth animations
- **Puzzle Categories**: Various categories including phrases, things, places, and people
- **Buzz-in Mechanism**: Fair buzzer system with answer validation
- **Scoring System**: Points awarded for correct answers
- **Game Rooms**: Support for multiple concurrent game rooms

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **WebSockets**: Real-time bidirectional communication
- **Python 3.7+**: Backend game logic and server

### Frontend
- **HTML5/CSS3**: Modern web technologies
- **JavaScript**: Game logic and WebSocket communication
- **Responsive Design**: Works on desktop and mobile devices

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd /path/to/wof
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the game server**
   ```bash
   # Option 1: Using the startup script
   python start_server.py
   
   # Option 2: Using uvicorn directly
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Open your web browser**
   - Navigate to `http://localhost:8000`
   - The game interface will load automatically

## 🎯 How to Play

### Starting a Game

1. **Join a Room**
   - Enter a room ID or use the auto-generated one
   - Enter your player name
   - Click "Join Room"

2. **Wait for Players**
   - Multiple players can join the same room using the same Room ID
   - Any player can start the game when ready

3. **Start Playing**
   - Click "Start Game" to begin the first round
   - The host will announce the category and puzzle

### Gameplay

1. **Letter Revelation**
   - Letters are gradually revealed in the puzzle
   - Common letters (E, T, A, O, etc.) appear first
   - The puzzle category is shown at the top

2. **Buzzing In**
   - When the buzzer becomes active, click "BUZZ IN!" or press SPACE
   - First player to buzz gets to answer
   - You have one chance to give the correct answer

3. **Answering**
   - Type your answer when prompted
   - Answers are case-insensitive
   - Correct answers award 1000 points

4. **Round Progression**
   - Correct answers advance to the next round
   - Wrong answers continue the current round (other players can still buzz)
   - Rounds timeout if no one solves the puzzle

### Controls

- **SPACE BAR**: Buzz in (when buzzer is active)
- **ENTER**: Submit answer (when answering)
- **Mouse/Touch**: All game interactions work with clicking/tapping

## 🏗️ Project Structure

```
wof/
├── backend/
│   ├── main.py              # Main FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── start_server.py      # Server startup script
├── frontend/
│   ├── index.html          # Main game interface
│   ├── style.css           # Game styling
│   └── script.js           # Game logic and WebSocket handling
└── README.md               # This file
```

## 🎨 Game Features in Detail

### Game Host
- Interactive host character that guides players
- Announces round starts, correct answers, and game events
- Speech synthesis support for audio announcements
- Personality-driven messages for engagement

### Puzzle System
- 10 built-in puzzles across different categories
- Random puzzle selection for each round
- Smart letter revelation order (common letters first)
- Category hints to help players

### Multiplayer Features
- Real-time synchronization across all players
- Fair buzzer system (first to buzz wins)
- Live score tracking and leaderboard
- Game log with all events and messages

### UI/UX Features
- Modern gradient design with smooth animations
- Responsive layout for mobile and desktop
- Visual feedback for all game states
- Accessibility features (keyboard navigation)

## 🔧 Customization

### Adding New Puzzles
Edit the `PUZZLES` list in `backend/main.py`:

```python
PUZZLES = [
    {"category": "YOUR_CATEGORY", "answer": "YOUR PUZZLE ANSWER", "difficulty": "easy"},
    # Add more puzzles here
]
```

### Adjusting Game Settings
In `backend/main.py`, you can modify:
- Letter revelation timing (change `await asyncio.sleep(2.0)`)
- Scoring values (change `player.score += 1000`)
- Buzzer activation threshold (change `len(unique_letters) * 0.8`)

### Styling Changes
Modify `frontend/style.css` to customize:
- Color schemes
- Animations
- Layout and spacing
- Responsive breakpoints

## 🚀 Deployment

For production deployment:

1. **Environment Setup**
   ```bash
   # Set production environment
   export ENVIRONMENT=production
   ```

2. **HTTPS/WSS Support**
   - Configure reverse proxy (nginx, Apache)
   - Set up SSL certificates
   - Update WebSocket URLs for WSS

3. **Scaling Considerations**
   - Redis for session storage across multiple servers
   - Load balancer for multiple backend instances
   - Database for persistent game statistics

## 🐛 Troubleshooting

### Common Issues

1. **Connection Issues**
   - Ensure the server is running on port 8000
   - Check firewall settings
   - Verify WebSocket support in browser

2. **Audio Not Working**
   - Enable audio in browser settings
   - Check browser speech synthesis support
   - Some browsers require user interaction before audio

3. **Mobile Issues**
   - Ensure responsive design is working
   - Check touch event handling
   - Verify mobile browser compatibility

### Debug Mode
Start the server with debug logging:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
```

## 🤝 Contributing

This is a fun game project! Feel free to:
- Add new puzzle categories and answers
- Improve the UI/UX design
- Add new game features (power-ups, different game modes)
- Optimize performance and add tests
- Add sound effects and music

## 📄 License

This project is created for educational and entertainment purposes. Feel free to use, modify, and distribute as needed.

## 🎉 Credits

Inspired by the classic "Wheel of Fortune" TV show toss-up rounds. Built with modern web technologies for a fun multiplayer experience.

---

**Have fun playing! 🎮🎡**
