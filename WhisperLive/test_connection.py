import asyncio
import websockets

async def test_connection():
    uri = "ws://localhost:9090"
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        await websocket.send("Hello, server!")
        response = await websocket.recv()
        print(f"Received response: {response}")

asyncio.get_event_loop().run_until_complete(test_connection())