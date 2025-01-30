from atproto import Client, FirehoseSubscribeReposClient, parse_subscribe_repos_message, CAR, models
import password
import os
import requests
import json
import multiformats_cid


def print_op_info(op):
    print(op)

    # Print the details for the created post
    print(f" - Action: {op.action}, Path: {op.path}")
    if op.cid:
        print(f"   - CID: {op.cid}")
    return op

def handle_repo_message(message) -> None:
    """Handles and decodes repository messages from the Firehose."""
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
                    print(f"   - Image data: {record.embed.images}")
                    for img in record.embed.images:
                        imgref = img.image.ref
                        print(imgref)
                        imgref = multiformats_cid.from_bytes(imgref)
                        print(imgref)
                        img = car.blocks.get(imgref)
                        print(img)
                
                    print(f"   - Post content: {record.text}")
                    print("\n")
                    print_op_info(op)
                    print("\n\n\n")
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

