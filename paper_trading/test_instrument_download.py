import requests
import json
from pathlib import Path

print("Starting download...")

url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

r = requests.get(
    url,
    stream=True,
    timeout=(10, 60)
)

print("Status:", r.status_code)

Path("data").mkdir(exist_ok=True)

with open(
    "data/instruments.json",
    "wb"
) as f:

    downloaded = 0

    for chunk in r.iter_content(
        chunk_size=1024 * 1024
    ):

        if chunk:

            f.write(chunk)

            downloaded += len(chunk)

            print(
                f"Downloaded: {downloaded / 1024 / 1024:.2f} MB",
                flush=True
            )

print("Finished")
