from atproto import Client
import asyncio
import websockets
import json
import password

# Configuration
FIREHOSE_URL = "wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos"

async def handle_event(event_data):
    """Process an individual event from the firehose."""
    # Decode the CBOR event data (if required, depending on the format)
    event = json.loads(event_data)  # Replace this with CBOR decoding if needed
    print("Received event:")
    print(json.dumps(event, indent=2))

    # Example: Process "repoCommit" events
    if "repoCommit" in event:
        repo_commit = event["repoCommit"]
        print(f"Event from repo: {repo_commit.get('repo')}")
        for op in repo_commit.get("ops", []):
            print(f" - {op['action']} record {op['path']}")

async def connect_to_firehose():
    """Connect to the Firehose WebSocket and listen for events."""
    async with websockets.connect(FIREHOSE_URL) as websocket:
        print("Connected to Firehose")
        while True:
            try:
                # Read each message from the WebSocket
                message = await websocket.recv()
                await handle_event(message)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
                break

def main():
    client = Client()
    profile = client.login('foleelli@oregonstate.edu', password.password)
    print('Welcome,', profile.display_name)

    # Firehose connection
    asyncio.run(connect_to_firehose())

if __name__ == '__main__':
    main()

