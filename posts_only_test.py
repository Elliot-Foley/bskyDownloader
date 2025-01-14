import asyncio
import websockets
from cbor2 import loads

async def connect_to_firehose():
    websocket_url = "wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos"

    try:
        async with websockets.connect(websocket_url) as websocket:
            print("Connected to the Bluesky Firehose.")
            while True:
                message = await websocket.recv()
                try:
                    # Decode CBOR event data
                    event_data = loads(message)
                    
                    if event_data.get("t") == "#commit":
                        print("Commit event received:")
                        # Print the entire event for debugging
                        print(event_data)
                        
                        repo = event_data.get("repo", "N/A")
                        commit_ops = event_data.get("ops", [])
                        
                        print(f" - Repo: {repo}")
                        for op in commit_ops:
                            action = op.get("action", "N/A")
                            path = op.get("path", "N/A")
                            print(f"   - Action: {action}, Path: {path}")
                    else:
                        print(f"Other event type: {event_data.get('t')}")
                except Exception as decode_error:
                    print(f"Error decoding CBOR: {decode_error}")
    except Exception as e:
        print(f"Error connecting to the firehose: {e}")

asyncio.run(connect_to_firehose())

