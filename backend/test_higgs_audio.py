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
    tts_base_url = os.getenv("TTS_BASE_URL", "https://vllm-route-wheel-of-fortune.apps.cluster-rpdb4.rpdb4.sandbox1254.opentlc.com:8000")
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
        # Prepare payload for Higgs Audio v2 via vLLM /v1/audio/speech endpoint
        # Based on AudioSpeechRequest schema from OpenAPI
        payload = {
            "model": tts_model,
            "input": test_text,
            "voice": "game_host",
            "speed": 1.0,
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 50,
            "response_format": "mp3",
            "max_tokens": 1024
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if tts_api_key and tts_api_key != "your_vllm_api_key_here":
            headers["Authorization"] = f"Bearer {tts_api_key}"
        
        # Use the correct /v1/audio/speech endpoint
        if tts_base_url.endswith('/v1'):
            api_url = f"{tts_base_url}/audio/speech"
        else:
            api_url = f"{tts_base_url}/v1/audio/speech"
        
        print(f"🔗 Connecting to: {api_url}")
        print(f"📝 Test text: {test_text}")
        print()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                print(f"📡 Response status: {response.status}")
                
                if response.status == 200:
                    # Check content type - might be audio directly or JSON with audio data
                    content_type = response.headers.get('content-type', '')
                    print(f"✅ Success! Content-Type: {content_type}")
                    
                    if 'audio' in content_type or 'application/octet-stream' in content_type:
                        # Response is direct audio data
                        audio_data = await response.read()
                        print(f"🎵 Direct audio response: {len(audio_data)} bytes")
                        
                        # Try to save audio to file for testing
                        try:
                            with open('test_higgs_audio.mp3', 'wb') as f:
                                f.write(audio_data)
                            print(f"💾 Audio saved to: test_higgs_audio.mp3 ({len(audio_data)} bytes)")
                        except Exception as e:
                            print(f"⚠️  Could not save audio: {e}")
                    else:
                        # Response might be JSON with audio data
                        try:
                            response_data = await response.json()
                            print(f"📋 JSON Response keys: {list(response_data.keys())}")
                            
                            # Look for audio data in various possible locations
                            audio_found = False
                            audio_locations = ['audio', 'data', 'content']
                            
                            for location in audio_locations:
                                if location in response_data:
                                    audio_data = response_data[location]
                                    print(f"🎵 Audio data found at: {location}")
                                    print(f"🎵 Audio data type: {type(audio_data)}")
                                    
                                    if isinstance(audio_data, str):
                                        print(f"🎵 Audio size: {len(audio_data)} chars (base64)")
                                        
                                        # Try to save audio to file for testing
                                        try:
                                            audio_bytes = base64.b64decode(audio_data)
                                            with open('test_higgs_audio.mp3', 'wb') as f:
                                                f.write(audio_bytes)
                                            print(f"💾 Audio saved to: test_higgs_audio.mp3 ({len(audio_bytes)} bytes)")
                                        except Exception as e:
                                            print(f"⚠️  Could not decode audio: {e}")
                                    
                                    audio_found = True
                                    break
                            
                            if not audio_found:
                                print("⚠️  No audio data found in JSON response")
                                print("🔍 Full response structure:")
                                print(json.dumps(response_data, indent=2, default=str)[:1000] + "...")
                        except Exception as json_error:
                            print(f"⚠️  Could not parse JSON response: {json_error}")
                            # Try treating as raw audio data
                            audio_data = await response.read()
                            if audio_data:
                                print(f"🎵 Fallback: Raw audio data {len(audio_data)} bytes")
                                try:
                                    with open('test_higgs_audio.mp3', 'wb') as f:
                                        f.write(audio_data)
                                    print(f"💾 Audio saved to: test_higgs_audio.mp3 ({len(audio_data)} bytes)")
                                except Exception as e:
                                    print(f"⚠️  Could not save audio: {e}")
                        
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
