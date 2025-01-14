from atproto import Client, FirehoseSubscribeReposClient, parse_subscribe_repos_message, CAR, models
import password
import os
import requests

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
            print(f"Received new post from repo: {commit.repo}")
            # Print the details for the created post
            print(f" - Action: {op.action}, Path: {op.path}")
            if op.cid:
                print(f"   - CID: {op.cid}")
                
            # Optionally, retrieve and print the post content from the CAR blocks
            record_raw_data = car.blocks.get(op.cid)
            if record_raw_data:
                record = models.get_or_create(record_raw_data, strict=False)
                print(f"   - Post content: {record.text}")

            print("\n---\n")  # Separate multiple posts for clarity
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

