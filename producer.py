from atproto import Client, FirehoseSubscribeReposClient, parse_subscribe_repos_message, CAR, models
from atproto_firehose.exceptions import FirehoseError
import os
import requests
import json
import multiformats_cid
import datetime
import concurrent.futures
import requests
import time
import logging
import sys
import redis

sys.stdout.flush()
sys.stderr.flush()

now = datetime.datetime.now()
noisy = False

# Configure logging
log_file = "firehose_errors.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

last_image_upload_time = None
image_processed_num = 0

r = redis.Redis(host='localhost', port=6379, db=0)

def handle_repo_message(message) -> None:
    commit = parse_subscribe_repos_message(message)

    if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
        return
    if not commit.blocks:
        print("Skipped commit with no blocks.")
        return

    car = CAR.from_bytes(commit.blocks)

    for op in commit.ops:
        if op.action == "create" and op.path.startswith("app.bsky.feed.post"):
            record_raw_data = car.blocks.get(op.cid)
            if not record_raw_data:
                continue

            record = models.get_or_create(record_raw_data, strict=False)

            try:
                if not record.embed.images:
                    continue

                for img in record.embed.images:
                    did = commit.repo
                    imgref = multiformats_cid.from_bytes(img.image.ref)
                    img_url = f"https://bsky.social/xrpc/com.atproto.sync.getBlob?did={did}&cid={imgref}"
                    
                    #For logging in case of crash
                    global last_image_upload_time
                    last_image_upload_time = record.created_at

                    # Optional: include metadata in message
                    payload = {
                        "url": img_url,
                        "text": record.text,
                        "timestamp": record.created_at,
                        "cid": f"{imgref}",
                        "did": f"{did}"
                    }

                    r.rpush('image_queue', json.dumps(payload))
                    global image_processed_num
                    image_processed_num += 1
                    if image_processed_num % 100 == 99:
                        print("100 image URLs added")
                        image_processed_num = 0

            except AttributeError:
                pass


def main():
    client = Client()
    firehose_client = FirehoseSubscribeReposClient()
    print("Client initialized, begining processing")
    while True:
        try:
            firehose_client.start(handle_repo_message)
        except FirehoseError as e:
            error_obj = e.args[0]  # Extract the XrpcError object
            error_type = getattr(error_obj, "error", "UnknownError")  # Get error safely

            # Calculate time difference if last_image_upload_time is set
            if last_image_upload_time:
                last_seen_time = datetime.datetime.strptime(last_image_upload_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                current_utc_time = datetime.datetime.utcnow()
                time_diff = current_utc_time - last_seen_time
                time_lag = f"Data lag: {time_diff}"
            else:
                time_lag = "Data lag: Unknown (No prior uploads recorded)"

            msg = f"Producer: FirehoseError: {error_type}. {time_lag}. Restarting..."
            print(msg)
            logging.warning(msg)
            time.sleep(2)  # Wait before retrying
        except Exception as e:
            msg = f"Producer: Unexpected error: {e}"
            print(msg)
            logging.error(msg)
            #break  # Stop for unknown errors

if __name__ == '__main__':
    main()

