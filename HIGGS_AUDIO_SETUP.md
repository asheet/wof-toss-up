# 🎤 Higgs Audio v2 TTS Integration Guide

This guide helps you integrate the [Higgs Audio v2 model](https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base) as your Wheel of Fortune game host's Text-to-Speech system.

## 🌟 Why Higgs Audio v2?

Higgs Audio v2 is a state-of-the-art TTS model that:
- **Achieves 75.7% win rate over GPT-4o-mini** on emotional expression
- **Generates highly expressive speech** perfect for game show hosting
- **Supports multiple languages** and natural prosody
- **Built on Llama-3.2-3B** with advanced DualFFN architecture

## 🛠️ Setup Instructions

### 1. Configure Your vLLM Server

Make sure your external vLLM server is running the Higgs Audio v2 model:

```bash
# Example vLLM server command (adjust for your setup)
python -m vllm.entrypoints.openai.api_server \
    --model bosonai/higgs-audio-v2-generation-3B-base \
    --port 8000 \
    --host 0.0.0.0
```

### 2. Update Environment Configuration

Copy `backend/env_example.txt` to `backend/.env` and configure:

```bash
# Text-to-Speech Configuration using Higgs Audio v2 via vLLM
TTS_ENABLED=true

# Higgs Audio v2 model - state-of-the-art TTS with 75.7% win rate over GPT-4o-mini
TTS_MODEL=higgs-audio-v2-generation-3B-base

# vLLM server endpoint for Higgs Audio v2 (use your external server URL)
TTS_BASE_URL=http://your_vllm_server:port

# API key for your vLLM server (if required)
TTS_API_KEY=your_vllm_api_key_here

# Voice settings (currently used for logging/identification)
TTS_VOICE=game_host
```

### 3. Test Your Setup

Run the test script to verify everything is working:

```bash
cd backend
python test_higgs_audio.py
```

This will:
- ✅ Test connection to your vLLM server
- ✅ Generate a sample game show host audio
- ✅ Save test audio file for verification
- ✅ Provide debugging information

### 4. Deploy to OpenShift

After testing locally, rebuild and deploy to OpenShift:

```bash
cd openshift
git add -A
git commit -m "Add Higgs Audio v2 TTS integration"
git push origin main

# Rebuild backend with new TTS integration
oc start-build wof-backend
```

## 🎮 How It Works

### Game Show Host Personality

The integration includes an optimized system prompt for game show hosting:

```
Generate expressive game show host audio following instruction.

<|scene_desc_start|>
Audio is recorded in a professional game show studio with good acoustics. 
The speaker is an enthusiastic, friendly game show host with natural speech patterns, 
appropriate pacing, and engaging intonation suitable for a TV game show audience.
<|scene_desc_end|>
```

### API Integration

The backend sends requests to your vLLM server using the chat completions format:

```python
payload = {
    "model": "higgs-audio-v2-generation-3B-base",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Welcome to Wheel of Fortune!"}
    ],
    "max_tokens": 1024,
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 50,
    "stop": ["<|end_of_text|>", "<|eot_id|>"]
}
```

### Audio Processing

- Audio is generated as base64-encoded data
- Automatically passed to frontend for playback
- Fallback to text-only if TTS fails
- Comprehensive error handling and debugging

## 🔧 Troubleshooting

### Common Issues

**Connection Failed:**
- ✅ Check `TTS_BASE_URL` points to your vLLM server
- ✅ Ensure vLLM server is running and accessible
- ✅ Verify network connectivity

**Authentication Errors:**
- ✅ Check `TTS_API_KEY` configuration
- ✅ Verify API key format matches your vLLM setup

**No Audio Generated:**
- ✅ Run `backend/test_higgs_audio.py` for debugging
- ✅ Check vLLM server logs for errors
- ✅ Verify Higgs Audio v2 model is loaded correctly

**Audio Not Playing:**
- ✅ Check browser console for audio playback errors
- ✅ Ensure browser allows audio autoplay
- ✅ Verify audio data is base64 encoded correctly

### Debug Mode

Enable detailed logging by checking backend console output:

```
🎤 Generating TTS with Higgs Audio v2 for: Welcome to Wheel of Fortune!
🔍 Higgs Audio v2 response keys: ['choices', 'usage', 'model']
🔍 Choice keys: ['message', 'finish_reason', 'index']
✅ TTS generated successfully with Higgs Audio v2 (15432 chars base64)
```

## 🎯 Expected Performance

With Higgs Audio v2, your game host will:
- 🎭 **Express emotions naturally** (excitement, suspense, congratulations)
- 🎪 **Match game show energy** with appropriate pacing and intonation
- 🗣️ **Sound conversational** rather than robotic
- 🌍 **Support multiple languages** if needed
- ⚡ **Generate high-quality audio** suitable for broadcast

## 📚 References

- [Higgs Audio v2 Model Card](https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base)
- [Higgs Audio GitHub Repository](https://github.com/boson-ai/higgs-audio)
- [vLLM Documentation](https://docs.vllm.ai/)
- [OpenAI API Compatibility](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)

---

**🎡 Ready to Host!** Your Wheel of Fortune game now has a professional, expressive AI host powered by cutting-edge TTS technology!
