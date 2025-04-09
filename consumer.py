import redis
import json
import requests
from PIL import Image
from io import BytesIO

r = redis.Redis(host='localhost', port=6379, db=0)
pubsub = r.pubsub()
pubsub.subscribe('image_channel')

print("Subscribed to image_channel")

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
                width, height = img.size
                rgb_pixel = img.getpixel((0, 0))

                log_entry = (
                    f"URL: {url}\n"
                    f"Resolution: {width}x{height}\n"
                    f"Top-left pixel RGB: {rgb_pixel}\n"
                    "---------------------------\n"
                )
                f.write(log_entry)
                f.flush()
                print(f"Logged image info for: {url}")
            else:
                print(f"Failed to fetch image: {url} (Status {response.status_code})")

        except Exception as e:
            print(f"Error handling message: {e}")
