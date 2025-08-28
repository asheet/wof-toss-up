from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import asyncio
import random
import aiohttp
from typing import Dict, List, Set, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import base64
from dotenv import load_dotenv

# Try to import OpenAI (optional dependency)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. Install with: pip install openai")

# Load environment variables
load_dotenv()

app = FastAPI(title="Wheel of Fortune Toss-up Game")

# Game state and player management
class Player:
    def __init__(self, player_id: str, name: str, websocket: WebSocket):
        self.id = player_id
        self.name = name
        self.websocket = websocket
        self.score = 0
        self.can_buzz = True

class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[str, Player] = {}
        self.current_puzzle = None
        self.revealed_positions: Set[int] = set()  # Track revealed character positions
        self.game_state = "waiting"  # waiting, revealing, buzzer_active, round_over, paused
        self.current_revealer_task = None
        self.current_timer_task = None
        self.current_answer_timer_task = None
        self.buzzed_player = None
        self.round_number = 1
        self.round_time_limit = 45  # seconds
        self.answer_time_limit = 10  # seconds to answer after buzzing
        self.remaining_time = 0
        self.answer_remaining_time = 0
        self.answer_received = asyncio.Event()

    async def broadcast(self, message: dict):
        """Send message to all players in the room"""
        disconnected_players = []
        for player_id, player in self.players.items():
            try:
                await player.websocket.send_text(json.dumps(message))
            except:
                disconnected_players.append(player_id)
        
        # Remove disconnected players
        for player_id in disconnected_players:
            del self.players[player_id]

# Load puzzles from JSON file
def load_puzzles():
    try:
        with open("puzzles.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback in case the file is missing
        return [
            {"category": "PHRASE", "answer": "A DIME A DOZEN", "difficulty": "easy"},
            {"category": "THING", "answer": "LAPTOP COMPUTER", "difficulty": "medium"},
        ]

PUZZLES = load_puzzles()

# Global game rooms
game_rooms: Dict[str, GameRoom] = {}

class AIGameHost:
    def __init__(self):
        self.client = None
        api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "llama3.2-3b")
        self.base_url = os.getenv("AI_BASE_URL", "http://localhost:8000/v1")
        
        # TTS Configuration for Higgs Audio v2 via vLLM
        self.tts_enabled = os.getenv("TTS_ENABLED", "false").lower() == "true"
        self.tts_model = os.getenv("TTS_MODEL", "higgs-audio-v2-generation-3B-base")
        self.tts_base_url = os.getenv("TTS_BASE_URL", "http://localhost:8000")
        self.tts_api_key = os.getenv("TTS_API_KEY") or api_key
        self.tts_voice = os.getenv("TTS_VOICE", "game_host")
        
        print(f"🔧 AI Host Debug Info:")
        print(f"   - OpenAI Available: {OPENAI_AVAILABLE}")
        print(f"   - API Key Found: {'Yes' if api_key else 'No'}")
        print(f"   - API Key (first 8 chars): {api_key[:8] if api_key else 'None'}...")
        print(f"   - Base URL: {self.base_url}")
        print(f"   - Model: {self.model}")
        print(f"   - TTS Enabled: {self.tts_enabled}")
        print(f"   - TTS Model: {self.tts_model}")
        print(f"   - TTS Base URL: {self.tts_base_url}")
        print(f"   - TTS Voice: {self.tts_voice}")
        
        self.ai_enabled = OPENAI_AVAILABLE and api_key is not None
        
        if self.ai_enabled:
            try:
                # Create OpenAI client with custom base URL for Llama server (for text generation)
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=self.base_url
                )
                print(f"🤖 AI Game Host enabled with {self.model} at {self.base_url}")
                
                # TTS setup for Higgs Audio v2 via vLLM
                if self.tts_enabled:
                    print(f"🎤 TTS enabled with Higgs Audio v2: {self.tts_model}")
                    print(f"🎤 TTS vLLM server: {self.tts_base_url}")
                    print(f"🎤 TTS voice profile: {self.tts_voice}")
                    print(f"🎤 TTS features: Expressive speech, 75.7% win rate over GPT-4o-mini")
                
            except Exception as e:
                print(f"❌ Failed to initialize AI client: {e}")
                self.ai_enabled = False
                print("📢 Falling back to static game host")
        else:
            reasons = []
            if not OPENAI_AVAILABLE:
                reasons.append("OpenAI library not available")
            if not api_key:
                reasons.append("No API key found")
            print(f"📢 Using static game host ({', '.join(reasons)})")
    
    def _get_system_prompt(self):
        return """You are a friendly, natural game show host for "Wheel of Fortune Toss-up". Sound like a real person, not a robot!

        Your personality:
        - Talk like you're having a conversation with friends
        - Use casual, natural language (like "Hey there!" "Nice job!" "Ooh, close one!")
        - Be genuinely excited but not over-the-top
        - Use contractions (don't, you're, that's, let's)
        - Add little personal touches and reactions
        - Sometimes use filler words like "well", "alright", "okay"
        - React naturally to what happens in the moment

        Examples of your style:
        - Instead of "Congratulations on your victory!" say "Hey, nice work! You nailed it!"
        - Instead of "The round continues!" say "Ooh, not quite, but don't worry - keep going!"
        - Instead of "Welcome contestants!" say "Alright everybody, let's see what we've got today!"

        Keep it short (1-2 sentences), sound natural and conversational. Never reveal puzzle answers."""
    
    async def _generate_ai_message(self, prompt: str, context: dict = None) -> str:
        """Generate AI response with context about the game state"""
        if not self.ai_enabled:
            print("🔍 AI call skipped (AI disabled)")
            return None
            
        try:
            full_prompt = prompt
            if context:
                context_str = f"Game context: Round {context.get('round', 1)}, Players: {context.get('players', [])}, Current scores: {context.get('scores', {})}"
                full_prompt = f"{context_str}\n\n{prompt}"
            
            print(f"🤖 AI Request to {self.base_url}:")
            print(f"   Model: {self.model}")
            print(f"   Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            if context:
                print(f"   Context: {context}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.8
                )
            )
            
            ai_message = response.choices[0].message.content.strip()
            print(f"✅ AI Response: {ai_message}")
            return ai_message
            
        except Exception as e:
            print(f"❌ AI Host error: {e}")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Falling back to static message")
            return None
    
    async def get_intro_message(self, context: dict = None):
        ai_msg = await self._generate_ai_message(
            "Greet the new player like you're meeting a friend. Be warm and welcoming, but keep it natural and conversational.", 
            context
        )
        return ai_msg or "Hey there! Welcome to Wheel of Fortune Toss-up! Ready to solve some puzzles?"
    
    async def get_round_start_message(self, round_num: int, category: str, context: dict = None):
        ai_msg = await self._generate_ai_message(
            f"It's round {round_num} and the category is '{category}'. Let the players know they can buzz in right away if they think they know it. Sound excited but natural!",
            context
        )
        return ai_msg or f"Alright, round {round_num}! Your category is {category}. You can buzz in anytime - even just from the category alone!"
    
    async def get_correct_answer_message(self, player_name: str, answer: str, context: dict = None):
        ai_msg = await self._generate_ai_message(
            f"{player_name} just got '{answer}' right! React naturally like you're genuinely excited for them. Be enthusiastic but sound like a real person talking to a friend.",
            context
        )
        return ai_msg or f"Yes! Nice job {player_name}, you got it - '{answer}'!"
    
    async def get_incorrect_answer_message(self, player_name: str, guess: str, context: dict = None):
        ai_msg = await self._generate_ai_message(
            f"{player_name} guessed '{guess}' but that's not right. Be supportive and encouraging, like a friend would be. Keep the game going!",
            context
        )
        return ai_msg or f"Ooh, not quite {player_name}! '{guess}' isn't it, but don't worry - keep trying!"
    
    async def get_round_complete_message(self, answer: str, context: dict = None):
        ai_msg = await self._generate_ai_message(
            f"Time's up! The answer was '{answer}'. React naturally to the time running out - maybe a little disappointed but ready to move on to the next round.",
            context
        )
        return ai_msg or f"Aww, time's up! It was '{answer}' - but hey, let's keep going with the next round!"
    
    async def generate_speech_audio(self, text: str) -> Optional[str]:
        """Generate speech audio using higgs-audio-v2-generation-3B-base model via vLLM and return base64 encoded audio data"""
        if not self.tts_enabled:
            return None
            
        try:
            print(f"🎤 Generating TTS with Higgs Audio v2 for: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # Higgs Audio v2 system prompt optimized for game show hosting
            system_prompt = (
                "Generate expressive game show host audio following instruction.\n\n"
                "<|scene_desc_start|>\n"
                "Audio is recorded in a professional game show studio with good acoustics. "
                "The speaker is an enthusiastic, friendly game show host with natural speech patterns, "
                "appropriate pacing, and engaging intonation suitable for a TV game show audience.\n"
                "<|scene_desc_end|>"
            )
            
            # Prepare the request payload for Higgs Audio v2 via vLLM
            payload = {
                "model": self.tts_model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": text
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 50,
                "stop": ["<|end_of_text|>", "<|eot_id|>"],
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tts_api_key}" if self.tts_api_key else ""
            }
            
            # Make async HTTP request to vLLM server using chat completions endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.tts_base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)  # Increased timeout for audio generation
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        print(f"🔍 Higgs Audio v2 response keys: {list(response_data.keys())}")
                        
                        # Extract audio data from the response
                        # Note: The exact response format may vary depending on vLLM configuration
                        if 'choices' in response_data and len(response_data['choices']) > 0:
                            choice = response_data['choices'][0]
                            print(f"🔍 Choice keys: {list(choice.keys())}")
                            
                            # Check different possible locations for audio data
                            audio_data = None
                            if 'audio' in choice:
                                audio_data = choice['audio']
                            elif 'message' in choice and 'audio' in choice['message']:
                                audio_data = choice['message']['audio']
                            elif 'content' in choice and 'audio' in choice['content']:
                                audio_data = choice['content']['audio']
                            elif 'message' in choice and 'content' in choice['message']:
                                # Sometimes the audio might be embedded in the content
                                content = choice['message']['content']
                                if isinstance(content, dict) and 'audio' in content:
                                    audio_data = content['audio']
                            
                            if audio_data:
                                if isinstance(audio_data, str):
                                    # Audio data is already base64 encoded
                                    print(f"✅ TTS generated successfully with Higgs Audio v2 ({len(audio_data)} chars base64)")
                                    return audio_data
                                elif isinstance(audio_data, (bytes, bytearray)):
                                    # Audio data needs to be encoded
                                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                                    print(f"✅ TTS generated successfully with Higgs Audio v2 ({len(audio_data)} bytes)")
                                    return audio_base64
                                else:
                                    print(f"⚠️  Audio data in unexpected format: {type(audio_data)}")
                                    return None
                            else:
                                print(f"⚠️  No audio data found in response")
                                print(f"🔍 Full response structure: {response_data}")
                                return None
                        else:
                            print(f"❌ Invalid response format from Higgs Audio v2")
                            print(f"🔍 Response keys: {list(response_data.keys()) if response_data else 'None'}")
                            return None
                    else:
                        error_text = await response.text()
                        print(f"❌ Higgs Audio v2 API error {response.status}: {error_text}")
                        return None
            
        except asyncio.TimeoutError:
            print(f"❌ Higgs Audio v2 generation timeout")
            return None
        except Exception as e:
            print(f"❌ Higgs Audio v2 generation failed: {e}")
            return None

# Initialize AI Game Host
ai_host = AIGameHost()

async def add_audio_to_message(message_data: dict, text: str) -> dict:
    """Add TTS audio to a message if enabled"""
    if ai_host.tts_enabled:
        audio = await ai_host.generate_speech_audio(text)
        if audio:
            message_data["audio"] = audio
            message_data["audio_format"] = "mp3"
    return message_data

async def reveal_letters_gradually(room: GameRoom):
    """Gradually reveal letters one position at a time"""
    if not room.current_puzzle:
        return
        
    answer = room.current_puzzle["answer"]
    
    # Find all letter positions in the puzzle
    letter_positions = []
    for i, char in enumerate(answer):
        if char.isalpha():
            letter_positions.append(i)
    
    # Shuffle positions for random revelation
    random.shuffle(letter_positions)
    
    # Sort by letter frequency (common letters first)
    def get_letter_priority(pos):
        char = answer[pos].upper()
        priority_letters = ['E', 'T', 'A', 'O', 'I', 'N', 'S', 'H', 'R']
        if char in priority_letters:
            return priority_letters.index(char)
        return len(priority_letters) + ord(char)
    
    # Sort positions by letter priority, but maintain some randomness within same letter
    letter_positions.sort(key=get_letter_priority)
    
    positions_revealed = 0
    
    try:
        for position in letter_positions:
            # Stop if someone buzzed in or game state changed
            if room.game_state not in ["buzzer_active", "revealing"]:
                break
            
            room.revealed_positions.add(position)
            positions_revealed += 1
            
            # Send updated puzzle state
            puzzle_display = get_puzzle_display(answer, room.revealed_positions)
            await room.broadcast({
                "type": "puzzle_update",
                "puzzle_display": puzzle_display,
                "revealed_positions": list(room.revealed_positions),
                "category": room.current_puzzle["category"]
            })
            
            # Check if enough positions revealed to make puzzle solvable
            total_positions = len(letter_positions)
            if positions_revealed >= max(3, total_positions * 0.4):
                # Give more time for players to think after decent revelation
                await asyncio.sleep(3.0)
            else:
                # Normal revelation pace
                await asyncio.sleep(2.0)
            
        # If we revealed all positions and no one buzzed, end the round
        if room.game_state == "buzzer_active":
            room.game_state = "round_over"
            context = {
                "round": room.round_number,
                "players": [p.name for p in room.players.values()],
                "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
            }
            host_message = await ai_host.get_round_complete_message(answer, context)
            await room.broadcast({
                "type": "host_message",
                "message": host_message,
                "round_complete": True
            })
            
    except asyncio.CancelledError:
        pass

async def countdown_timer(room: GameRoom):
    """Handle the countdown timer for the round"""
    room.remaining_time = room.round_time_limit
    
    try:
        while room.remaining_time > 0 and room.game_state not in ["round_over", "waiting"]:
            if room.game_state == "waiting_answer":
                # Timer is "paused" while waiting for an answer
                await room.broadcast({
                    "type": "timer_update",
                    "remaining_time": room.remaining_time,
                    "is_paused": True
                })
                # Check less frequently when paused
                await asyncio.sleep(2.0)
            else:
                # Timer is running
                await room.broadcast({
                    "type": "timer_update",
                    "remaining_time": room.remaining_time,
                    "is_paused": False
                })
                await asyncio.sleep(1.0)
                room.remaining_time -= 1
        
        # Timer expired
        if room.remaining_time <= 0 and room.game_state not in ["round_over", "waiting_answer"]:
            room.game_state = "round_over"
            context = {
                "round": room.round_number,
                "players": [p.name for p in room.players.values()],
                "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
            }
            host_message = await ai_host.get_round_complete_message(room.current_puzzle["answer"], context)
            await room.broadcast({
                "type": "timer_expired",
                "message": "Time's up!",
                "host_message": host_message,
                "answer": room.current_puzzle["answer"]
            })
            
            # Wait a bit then start next round
            await asyncio.sleep(3)
            room.round_number += 1
            await start_new_round(room)
            
    except asyncio.CancelledError:
        pass

async def answer_countdown_timer(room: GameRoom):
    """Handle the 10-second countdown for answering after buzzing in"""
    room.answer_remaining_time = room.answer_time_limit
    
    try:
        while room.answer_remaining_time > 0 and room.game_state == "waiting_answer":
            # Send answer timer update
            await room.broadcast({
                "type": "answer_timer_update",
                "remaining_time": room.answer_remaining_time,
                "total_time": room.answer_time_limit,
                "is_paused": False
            })
            
            # Wait 1 second
            await asyncio.sleep(1.0)
            room.answer_remaining_time -= 1
        
        # Answer timer expired
        if room.answer_remaining_time <= 0 and room.game_state == "waiting_answer":
            # Player took too long to answer
            buzzed_player = room.players.get(room.buzzed_player)
            if buzzed_player:
                buzzed_player.can_buzz = False  # They lose their chance
                
                host_message = f"{buzzed_player.name} took too long to answer! Time's up."
                
                await room.broadcast({
                    "type": "answer_timeout",
                    "player_name": buzzed_player.name,
                    "host_message": host_message,
                    "message": "Answer time expired!"
                })
                
                # Reset buzzer state and continue game
                room.buzzed_player = None
                room.game_state = "buzzer_active"
                
                # Notify that timer has resumed
                await room.broadcast({
                    "type": "timer_resumed",
                    "message": "Main timer resumed! Other players can still buzz in."
                })
                
                # Check if anyone can still buzz
                can_buzz_players = [p for p in room.players.values() if p.can_buzz]
                if not can_buzz_players:
                    # No one left to buzz, end round
                    room.game_state = "round_over"
                    context = {
                        "round": room.round_number,
                        "players": [p.name for p in room.players.values()],
                        "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
                    }
                    host_message = await ai_host.get_round_complete_message(room.current_puzzle["answer"], context)
                    await room.broadcast({
                        "type": "round_timeout",
                        "answer": room.current_puzzle["answer"],
                        "host_message": host_message
                    })
                    await asyncio.sleep(3)
                    room.round_number += 1
                    await start_new_round(room)
            
    except asyncio.CancelledError:
        pass

def get_puzzle_display(answer: str, revealed_positions: Set[int]) -> str:
    """Create the puzzle display with revealed positions"""
    display = ""
    for i, char in enumerate(answer):
        if char.isalpha():
            if i in revealed_positions:
                display += char.upper()
            else:
                display += "_"
        else:
            display += char
    return display

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, name: str = "Player"):
    await websocket.accept()
    
    player_id = str(uuid.uuid4())
    player_name = name if name else f"Player{random.randint(1, 100)}"
    
    # Create room if it doesn't exist
    if room_id not in game_rooms:
        game_rooms[room_id] = GameRoom(room_id)
    
    room = game_rooms[room_id]
    player = Player(player_id, player_name, websocket)
    room.players[player_id] = player
    
    # Send welcome message
    welcome_message = await ai_host.get_intro_message({"players": [player_name]})
    welcome_audio = await ai_host.generate_speech_audio(welcome_message)
    
    welcome_data = {
        "type": "welcome",
        "player_id": player_id,
        "player_name": player_name,
        "room_id": room_id,
        "message": welcome_message
    }
    
    if welcome_audio:
        welcome_data["audio"] = welcome_audio
        welcome_data["audio_format"] = "mp3"
    
    await websocket.send_text(json.dumps(welcome_data))
    
    # Broadcast player list update
    await room.broadcast({
        "type": "player_update",
        "players": [{"id": p.id, "name": p.name, "score": p.score} for p in room.players.values()]
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "start_game":
                if room.game_state == "waiting":
                    await start_new_round(room)
            
            elif message["type"] == "buzz_in":
                if room.game_state == "buzzer_active" and room.buzzed_player is None:
                    room.buzzed_player = player_id
                    room.game_state = "waiting_answer"
                    
                    # Stop the letter revealer
                    if room.current_revealer_task:
                        room.current_revealer_task.cancel()
                    
                    # Start answer countdown timer
                    room.current_answer_timer_task = asyncio.create_task(answer_countdown_timer(room))
                    
                    await room.broadcast({
                        "type": "player_buzzed",
                        "player_name": player.name,
                        "answer_time_limit": room.answer_time_limit,
                        "message": f"{player.name} buzzed in! Timer paused. You have {room.answer_time_limit} seconds to answer..."
                    })
            
            elif message["type"] == "submit_answer":
                if room.buzzed_player == player_id and room.game_state == "waiting_answer":
                    answer = message["answer"].strip().upper()
                    
                    # Notify that the answer was received
                    room.answer_received.set()
                    await room.broadcast({"type": "answer_received", "message": "Answer submitted. Checking..."})

                    # Cancel the answer timer
                    if room.current_answer_timer_task:
                        room.current_answer_timer_task.cancel()
                        room.current_answer_timer_task = None
                    
                    guess = answer
                    correct_answer = room.current_puzzle["answer"].upper()
                    
                    if guess == correct_answer:
                        # Correct answer! Cancel all timers
                        if room.current_timer_task:
                            room.current_timer_task.cancel()
                        if room.current_revealer_task:
                            room.current_revealer_task.cancel()
                            
                        player.score += 100
                        context = {
                            "round": room.round_number,
                            "players": [p.name for p in room.players.values()],
                            "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
                        }
                        host_message = await ai_host.get_correct_answer_message(player.name, correct_answer, context)
                        
                        await room.broadcast({
                            "type": "correct_answer",
                            "winner": player.name,
                            "answer": correct_answer,
                            "host_message": host_message,
                            "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
                        })
                        
                        # Send updated player list with new scores
                        await room.broadcast({
                            "type": "player_update",
                            "players": [{"id": p.id, "name": p.name, "score": p.score} for p in room.players.values()]
                        })
                        
                        # Wait a bit then start next round
                        await asyncio.sleep(3)
                        room.round_number += 1
                        await start_new_round(room)
                        
                    else:
                        # Wrong answer
                        player.can_buzz = False
                        context = {
                            "round": room.round_number,
                            "players": [p.name for p in room.players.values()],
                            "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
                        }
                        host_message = await ai_host.get_incorrect_answer_message(player.name, guess, context)
                        
                        await room.broadcast({
                            "type": "incorrect_answer",
                            "player_name": player.name,
                            "guess": guess,
                            "host_message": host_message
                        })
                        
                        # Reset buzzer state and continue revealing
                        room.buzzed_player = None
                        room.game_state = "buzzer_active"
                        
                        # Notify that timer has resumed
                        await room.broadcast({
                            "type": "timer_resumed",
                            "message": "Timer resumed! Other players can still buzz in."
                        })
                        
                        # Check if anyone can still buzz
                        can_buzz_players = [p for p in room.players.values() if p.can_buzz]
                        if not can_buzz_players:
                            # No one left to buzz, end round
                            room.game_state = "round_over"
                            context = {
                                "round": room.round_number,
                                "players": [p.name for p in room.players.values()],
                                "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
                            }
                            host_message = await ai_host.get_round_complete_message(correct_answer, context)
                            await room.broadcast({
                                "type": "round_timeout",
                                "answer": correct_answer,
                                "host_message": host_message
                            })
                            await asyncio.sleep(3)
                            room.round_number += 1
                            await start_new_round(room)
                            
    except WebSocketDisconnect:
        # Remove player from room
        if player_id in room.players:
            del room.players[player_id]
        
        # Broadcast updated player list
        if room.players:
            await room.broadcast({
                "type": "player_update",
                "players": [{"id": p.id, "name": p.name, "score": p.score} for p in room.players.values()]
            })
        else:
            # Delete empty room
            if room_id in game_rooms:
                del game_rooms[room_id]

async def start_new_round(room: GameRoom):
    """Start a new puzzle round"""
    # Cancel any existing tasks
    if room.current_revealer_task:
        room.current_revealer_task.cancel()
    if room.current_timer_task:
        room.current_timer_task.cancel()
    if room.current_answer_timer_task:
        room.current_answer_timer_task.cancel()
    
    # Reset round state
    room.current_puzzle = random.choice(PUZZLES)
    room.revealed_positions = set()
    room.buzzed_player = None
    room.game_state = "buzzer_active"  # Start with buzzer active immediately
    room.remaining_time = room.round_time_limit
    
    # Reset player buzz capabilities
    for player in room.players.values():
        player.can_buzz = True
    
    # Send round start message
    context = {
        "round": room.round_number,
        "players": [p.name for p in room.players.values()],
        "scores": {p.id: {"name": p.name, "score": p.score} for p in room.players.values()}
    }
    host_message = await ai_host.get_round_start_message(room.round_number, room.current_puzzle["category"], context)
    await room.broadcast({
        "type": "round_start",
        "round_number": room.round_number,
        "category": room.current_puzzle["category"],
        "host_message": host_message,
        "puzzle_display": get_puzzle_display(room.current_puzzle["answer"], room.revealed_positions),
        "time_limit": room.round_time_limit
    })
    
    # Immediately activate buzzer
    await room.broadcast({
        "type": "buzzer_active",
        "message": "Buzzer is active! Buzz in if you know the answer!"
    })
    
    # Start timer and letter revelation
    room.current_timer_task = asyncio.create_task(countdown_timer(room))
    room.current_revealer_task = asyncio.create_task(reveal_letters_gradually(room))

# Static files are served by the frontend service in OpenShift
# No need to serve them from the backend

# Health check endpoint for OpenShift
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "wof-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
