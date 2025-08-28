#!/usr/bin/env python3
"""
Test script for Higgs Audio v2 TTS integration
This script helps verify that your vLLM server with Higgs Audio v2 is working correctly.
"""

import asyncio
import aiohttp
import base64
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_higgs_audio_v2():
    """Test the Higgs Audio v2 TTS setup"""
    
    # Configuration from environment
    tts_model = os.getenv("TTS_MODEL", "higgs-audio-v2-generation-3B-base")
    tts_base_url = os.getenv("TTS_BASE_URL", "http://localhost:8000")
    tts_api_key = os.getenv("TTS_API_KEY", "")
    
    print("🎤 Testing Higgs Audio v2 TTS Integration")
    print("=" * 50)
    print(f"Model: {tts_model}")
    print(f"Server: {tts_base_url}")
    print(f"API Key: {'✓ Set' if tts_api_key else '✗ Not set'}")
    print()
    
    # Test text for game show hosting
    test_text = "Welcome to Wheel of Fortune Toss-up! Let's see what puzzle we have for you today. Good luck, contestants!"
    
    try:
        # Higgs Audio v2 system prompt for game show hosting
        system_prompt = (
            "Generate expressive game show host audio following instruction.\n\n"
            "<|scene_desc_start|>\n"
            "Audio is recorded in a professional game show studio with good acoustics. "
            "The speaker is an enthusiastic, friendly game show host with natural speech patterns, "
            "appropriate pacing, and engaging intonation suitable for a TV game show audience.\n"
            "<|scene_desc_end|>"
        )
        
        # Prepare payload for Higgs Audio v2 via vLLM
        payload = {
            "model": tts_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": test_text
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
            "Content-Type": "application/json"
        }
        
        if tts_api_key:
            headers["Authorization"] = f"Bearer {tts_api_key}"
        
        print(f"🔗 Connecting to: {tts_base_url}/v1/chat/completions")
        print(f"📝 Test text: {test_text}")
        print()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{tts_base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                print(f"📡 Response status: {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"✅ Success! Response keys: {list(response_data.keys())}")
                    
                    if 'choices' in response_data and len(response_data['choices']) > 0:
                        choice = response_data['choices'][0]
                        print(f"📋 Choice keys: {list(choice.keys())}")
                        
                        # Look for audio data
                        audio_found = False
                        audio_locations = [
                            'audio',
                            'message.audio',
                            'content.audio',
                            'message.content.audio'
                        ]
                        
                        for location in audio_locations:
                            try:
                                keys = location.split('.')
                                data = choice
                                for key in keys:
                                    data = data[key]
                                
                                if data:
                                    print(f"🎵 Audio data found at: {location}")
                                    print(f"🎵 Audio data type: {type(data)}")
                                    if isinstance(data, str):
                                        print(f"🎵 Audio size: {len(data)} chars (base64)")
                                        
                                        # Try to save audio to file for testing
                                        try:
                                            audio_bytes = base64.b64decode(data)
                                            with open('test_higgs_audio.wav', 'wb') as f:
                                                f.write(audio_bytes)
                                            print(f"💾 Audio saved to: test_higgs_audio.wav ({len(audio_bytes)} bytes)")
                                        except Exception as e:
                                            print(f"⚠️  Could not decode audio: {e}")
                                    
                                    audio_found = True
                                    break
                            except (KeyError, TypeError):
                                continue
                        
                        if not audio_found:
                            print("⚠️  No audio data found in response")
                            print("🔍 Full response structure:")
                            print(json.dumps(response_data, indent=2, default=str)[:1000] + "...")
                    else:
                        print("❌ No choices in response")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}: {error_text}")
                    
                    if response.status == 404:
                        print("💡 Tip: Make sure your vLLM server is running Higgs Audio v2")
                        print("💡 Tip: Check that the endpoint URL is correct")
                    elif response.status == 401 or response.status == 403:
                        print("💡 Tip: Check your API key configuration")
                    elif response.status == 422:
                        print("💡 Tip: The request format might need adjustment for your vLLM setup")
    
    except aiohttp.ClientConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Tip: Make sure your vLLM server is running and accessible")
        print("💡 Tip: Check the TTS_BASE_URL in your .env file")
    
    except asyncio.TimeoutError:
        print("❌ Request timed out")
        print("💡 Tip: Higgs Audio v2 generation can take time, especially on first run")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("🔧 Configuration Check:")
    print(f"   TTS_ENABLED should be: true")
    print(f"   TTS_MODEL should be: higgs-audio-v2-generation-3B-base")
    print(f"   TTS_BASE_URL should point to your vLLM server")
    print(f"   TTS_API_KEY should match your vLLM server (if auth required)")

if __name__ == "__main__":
    print("🎡 Higgs Audio v2 TTS Test for Wheel of Fortune")
    print("=" * 50)
    asyncio.run(test_higgs_audio_v2())
