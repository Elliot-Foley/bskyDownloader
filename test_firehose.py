from atproto import Client, FirehoseSubscribeReposClient, parse_subscribe_repos_message, CAR, models
import password
import os
import requests
from PIL import Image

def download_images_from_post(post, output_dir, pds_url, jwt):
    if post.get("embed", {}).get("$type") == "app.bsky.embed.images":
        os.makedirs(output_dir, exist_ok=True)
        images = post["embed"]["images"]
        for i, image in enumerate(images):
            cid = image["image"]["ref"]["$link"]
            mime_type = image["image"]["mimeType"]
            extension = mime_type.split("/")[-1]
            alt_text = image.get("alt", f"image_{i}")
            output_path = os.path.join(output_dir, f"{alt_text}.{extension}")

            # Download the blob
            url = f"{pds_url}/xrpc/com.atproto.repo.downloadBlob"
            headers = {"Authorization": f"Bearer {jwt}"}
            params = {"cid": cid}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # Sanitize the image
            sanitized_path = os.path.join(output_dir, f"{alt_text}_sanitized.{extension}")
            with Image.open(output_path) as img:
                img.save(sanitized_path, extension.upper(), optimize=True)
            print(f"Image saved and sanitized: {sanitized_path}")


def handle_repo_message(message) -> None:
    """Handles and decodes repository messages from the Firehose."""
    commit = parse_subscribe_repos_message(message)

    # Ensure it's a commit message with blocks
    if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
        print("Skipped non-commit message.")
        return

    if not commit.blocks:
        print("Skipped commit with no blocks.")
        return

    # Decode the CAR blocks
    car = CAR.from_bytes(commit.blocks)

    #print(f"Event from repo: {commit.repo}")
    for op in commit.ops:
        #print(f" - Action: {op.action}, Path: {op.path}")
        print(f"Path: {op.path}")
        #if op.cid:
            #print(f"   - CID: {op.cid}")

    # Process decoded CAR blocks
    #for block in car.blocks:
        #print(f"Decoded block: {str(block)}")
        #print(f"Block Hash: {block.hash}")
        #print(f"Codec: {block.codec}, Version: {block.version}")


def main():
    # Log in using the AT Protocol client
    client = Client()
    profile = client.login('foleelli@oregonstate.edu', password.password)
    print('Welcome,', profile.display_name)

    # Set up Firehose client and start processing messages
    firehose_client = FirehoseSubscribeReposClient()
    firehose_client.start(handle_repo_message)


if __name__ == '__main__':
    main()

