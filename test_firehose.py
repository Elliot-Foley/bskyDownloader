from atproto import Client, FirehoseSubscribeReposClient, parse_subscribe_repos_message, CAR, models
#import password
import os
import requests
import json
import multiformats_cid
import datetime
import concurrent.futures
import requests
now = datetime.datetime.now()
Images = []
output_path_base = "./output"

def download_image(image):
    # Create directory for this image
    image_dir = os.path.join(output_path_base, f"{image.filename}")
    os.makedirs(image_dir, exist_ok=True)

    # File paths
    image_path = os.path.join(image_dir, f"{image.filename}.jpeg")
    text_path = os.path.join(image_dir, "description.txt")

    # Download the image
    response = requests.get(image.url, stream=True)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded {image_path}")

        # Save text description
        with open(text_path, 'w', encoding="utf-8") as f:
            f.write(image.text)
        print(f"Saved text description: {text_path}")
    else:
        print(f"Failed to download {image.url}")

def download_image_old(image):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        #print(f"Downloaded {image.filename}")
        os.makedirs()
    else:
        print(f"Failed to download {image.url}")

class Image:
    def __init__(self, did, cid, text):
        self.did = did
        self.cid = cid
        self.text = text
        self.url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg"
        self.filename = f"{now} {did}-{cid}"

def handle_repo_message(message) -> None:
    """Handles and decodes repository messages from the Firehose."""
    global now, Images
    commit = parse_subscribe_repos_message(message)

    # Ensure it's a commit message with blocks
    if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
        #print("Skipped non-commit message.")
        return

    if not commit.blocks:
        print("Skipped commit with no blocks.")
        return

    # Decode the CAR blocks
    car = CAR.from_bytes(commit.blocks)
    
    # Check for post-related events and ignore others
    for op in commit.ops:
        if op.action == "create" and op.path.startswith("app.bsky.feed.post"):
                
            # Optionally, retrieve and print the post content from the CAR blocks
            record_raw_data = car.blocks.get(op.cid)
            if record_raw_data:
                record = models.get_or_create(record_raw_data, strict=False)
                #print(f"   - Post content: {record.text}")
                try:
                    #print(f"   - Image data: {record.embed.images}")
                    for img in record.embed.images:
                        did = commit.repo
                        #print(did)
                        imgref = img.image.ref
                        imgref = multiformats_cid.from_bytes(imgref)
                        #print(imgref)
                        #print(img)
                
                        #print(f"   - Post content: {record.text}")
                        imgURL = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{imgref}@jpeg"
                        #print(f"   - URL: {imgURL}")
                        Images.append(Image(did, imgref, record.text))
                        if datetime.datetime.now() - now >= datetime.timedelta(seconds=1):
                            print("\n\n\n")
                            now = datetime.datetime.now()
                            img_count = 0
                            for i in Images:
                                img_count += 1
                                print(f"Saving image from {i.url} at {i.filename}")
                            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                                futures = [executor.submit(download_image, i) for i in Images]
                                concurrent.futures.wait(futures)
                            print(f"1 second passed, {img_count} images processed")
                            Images = []
                   
                except AttributeError:
                    pass
                    #print("No images")

                # Convert the parsed message to a JSON string for inspection
                message_json = json.dumps(record, default=str, indent=4)
    
                # Print the full structure of the message for debugging purposes
                #print("Full JSON structure of the message:")
                #print(message_json)


            #print("\n---\n")  # Separate multiple posts for clarity
        #else:
            #print(f"Skipped non-post event: {op.path}")
        

def main():
    # Log in using the AT Protocol client
    client = Client()
    # profile = client.login('foleelli@oregonstate.edu', password.password)
    # print('Welcome,', profile.display_name)

    # Set up Firehose client and start processing messages
    firehose_client = FirehoseSubscribeReposClient()
    firehose_client.start(handle_repo_message)

if __name__ == '__main__':
    main()

