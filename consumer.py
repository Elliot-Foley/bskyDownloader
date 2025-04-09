import redis
import json
import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np

r = redis.Redis(host='localhost', port=6379, db=0)
pubsub = r.pubsub()
pubsub.subscribe('image_channel')

print("Subscribed to image_channel")

def compute_orb_features(pil_image, nlevels=32, scaleFactor=1.2):
    """Compute ORB keypoints and descriptors for a Pillow image."""
    # Convert Pillow image to grayscale OpenCV format
    gray_image = pil_image.convert('L')
    image_np = np.array(gray_image)

    orb = cv2.ORB_create(nlevels=nlevels, scaleFactor=scaleFactor)
    keypoints, descriptors = orb.detectAndCompute(image_np, None)

    return keypoints, descriptors


with open("redis-output.txt", "a") as f:
    for message in pubsub.listen():
        if message['type'] != 'message':
            continue

        try:
            data = json.loads(message['data'])
            url = data['url']
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                keypoints, descriptors = compute_orb_features(img)
                width, height = img.size
                rgb_pixel = img.getpixel((0, 0))

                log_entry = (
                    f"URL: {url}\n"
                    f"Resolution: {width}x{height}\n"
                    f"Top-left pixel RGB: {rgb_pixel}\n"
                    f"Descriptors: {descriptors}\n"
                    f"Descriptors size: {[len(descriptors), len(descriptors[0])]}\n"
                    "---------------------------\n"
                )
                f.write(log_entry)
                f.flush()
                print(f"Logged image info for: {url}")
            else:
                print(f"Failed to fetch image: {url} (Status {response.status_code})")

        except Exception as e:
            print(f"Error handling message: {e}")
