import redis
import json
import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
from datetime import datetime
import os
import sys

# Global storage location
BASE_DIR = "/data/output_sorted"

image_processed_num = 0

# Redis setup
r = redis.Redis(host='localhost', port=6379, db=0)
pubsub = r.pubsub()
pubsub.subscribe('image_queue')

print("Subscribed to image_queue")

def compute_orb_features(pil_image, nlevels=32, scaleFactor=1.2):
    """Compute ORB keypoints and descriptors for a Pillow image."""
    gray_image = pil_image.convert('L')
    image_np = np.array(gray_image)

    orb = cv2.ORB_create(nlevels=nlevels, scaleFactor=scaleFactor)
    keypoints, descriptors = orb.detectAndCompute(image_np, None)

    return keypoints, descriptors

def make_output_dir(cid):
    """Create a directory structure based on current time and CID."""
    now = datetime.utcnow()
    path = os.path.join(
        BASE_DIR,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H"),
        now.strftime("%M"),
        cid
    )
    os.makedirs(path, exist_ok=True)
    return path

while True:

    try:
        _, raw_data = r.brpop('image_queue')
        data = json.loads(raw_data)
        url = data['url']
        post_text = data['text']
        cid = data['cid']
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            #keypoints, descriptors = compute_orb_features(img)
            width, height = img.size
            #rgb_pixel = img.getpixel((0, 0))

            output_dir = make_output_dir(cid)
            img_path = os.path.join(output_dir, "image.jpg")
            meta_path = os.path.join(output_dir, "info.txt")

            img.save(img_path)

            with open(meta_path, "w") as meta_file:
                meta_file.write(
                    f"URL: {url}\n"
                    f"Resolution: {width}x{height}\n"
                    f"Post text: {post_text}\n"
                )

            image_processed_num += 1
            if image_processed_num % 100 == 99:
                print("100 image URLs added")
                image_processed_num = 0

    except Exception as e:
        print(f"Error processing message: {e}", file=sys.stderr)

