import asyncio
import json
import sys
import wave

import websockets


async def transcribe_audio_file(audio_file_path: str, server_url: str = "ws://localhost:8765/ws/transcribe"):
    async with websockets.connect(server_url) as websocket:
        print("Connected to server")
        
        init_message = {
            "type": "init",
            "participant_info": {
                "user": "example_user",
                "meeting": "example_meeting"
            }
        }
        await websocket.send(json.dumps(init_message))
        print(f"Sent init message: {init_message}")
        
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"Server response: {response_data}")
        
        if response_data.get("type") != "ready":
            print(f"Error: Expected 'ready' message, got: {response_data}")
            return
        
        print(f"Session ID: {response_data.get('session_id')}")
        
        async def receive_transcripts():
            try:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "transcript":
                        is_final = data.get("is_final", False)
                        text = data.get("text", "")
                        prefix = "[FINAL]" if is_final else "[PARTIAL]"
                        print(f"{prefix} {text}")
                    elif data.get("type") == "error":
                        print(f"Error from server: {data.get('message')}")
                        break
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by server")
            except Exception as e:
                print(f"Error receiving transcripts: {e}")
        
        receive_task = asyncio.create_task(receive_transcripts())
        
        try:
            with wave.open(audio_file_path, 'rb') as wav_file:
                print(f"Reading audio file: {audio_file_path}")
                print(f"Channels: {wav_file.getnchannels()}")
                print(f"Sample width: {wav_file.getsampwidth()}")
                print(f"Frame rate: {wav_file.getframerate()}")
                
                chunk_size = 1024
                while True:
                    frames = wav_file.readframes(chunk_size)
                    if not frames:
                        break
                    
                    await websocket.send(frames)
                    await asyncio.sleep(0.05)
                
                print("Finished sending audio")
                
                await asyncio.sleep(2)
                
                stop_message = {"type": "stop"}
                await websocket.send(json.dumps(stop_message))
                print("Sent stop message")
                
        except Exception as e:
            print(f"Error sending audio: {e}")
        finally:
            await asyncio.sleep(1)
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass


async def transcribe_microphone(server_url: str = "ws://localhost:8765/ws/transcribe"):
    try:
        import pyaudio
    except ImportError:
        print("PyAudio not installed. Install it with: pip install pyaudio")
        return
    
    async with websockets.connect(server_url) as websocket:
        print("Connected to server")
        
        init_message = {
            "type": "init",
            "participant_info": {
                "user": "example_user",
                "meeting": "live_meeting"
            }
        }
        await websocket.send(json.dumps(init_message))
        
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"Server response: {response_data}")
        
        if response_data.get("type") != "ready":
            print(f"Error: Expected 'ready' message, got: {response_data}")
            return
        
        print(f"Session ID: {response_data.get('session_id')}")
        print("Recording from microphone... Press Ctrl+C to stop")
        
        async def receive_transcripts():
            try:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "transcript":
                        is_final = data.get("is_final", False)
                        text = data.get("text", "")
                        prefix = "[FINAL]" if is_final else "[PARTIAL]"
                        print(f"{prefix} {text}")
            except:
                pass
        
        receive_task = asyncio.create_task(receive_transcripts())
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        try:
            while True:
                audio_data = stream.read(1024, exception_on_overflow=False)
                await websocket.send(audio_data)
                await asyncio.sleep(0.01)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            stop_message = {"type": "stop"}
            await websocket.send(json.dumps(stop_message))
            
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python example_client.py <audio_file.wav>")
        print("  python example_client.py --microphone")
        sys.exit(1)
    
    if sys.argv[1] == "--microphone":
        asyncio.run(transcribe_microphone())
    else:
        audio_file = sys.argv[1]
        asyncio.run(transcribe_audio_file(audio_file))


if __name__ == "__main__":
    main()
