import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/audio"
    
    # Update this to match your actual test file path
    test_audio_path = r"D:\Projects\VoiceGuard\audios\real\sample.wav" 
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to VoiceGuard Backend at {uri}")
            
            # Read the audio file as binary
            with open(test_audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
                
            print(f"📤 Sending {len(audio_bytes)} bytes of audio data...")
            await websocket.send(audio_bytes)
            
            # Wait for the AI risk score from the server
            print("⏳ Waiting for AI analysis...")
            response = await websocket.recv()
            
            # Parse and print the JSON response beautifully
            result = json.loads(response)
            print("\n🎯 Server Response:")
            print(json.dumps(result, indent=4))
            
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{test_audio_path}'. Please check the file name and path.")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    # Run the async WebSocket client
    asyncio.run(test_websocket())