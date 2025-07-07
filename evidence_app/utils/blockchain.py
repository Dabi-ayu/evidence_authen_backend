import requests
import hashlib
import datetime
import os

ORIGINSTAMP_API_KEY = os.getenv("ORIGINSTAMP_API_KEY")

def log_verification(image_path):
    """Logs a blockchain timestamp using OriginStamp and returns TXID or error."""

    # 1. Hash the image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()

    # 2. Prepare request
    headers = {
        "Authorization": f"Bearer {ORIGINSTAMP_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "hash_string": sha256_hash,
        "comment": f"Evidence timestamp - {datetime.datetime.now().isoformat()}",
        "metadata": {
            "filename": os.path.basename(image_path)
        }
    }

    # 3. Send request to OriginStamp
    response = requests.post(
        "https://api.originstamp.com/v4/timestamp/create",
        headers=headers,
        json=data
    )

    try:
        result = response.json()
    except ValueError:
        return "Blockchain error: Invalid response format"

    if response.status_code == 200 and "payload" in result:
        return f"OriginStamp TXID: {result['payload']['id']}"
    else:
        error_msg = result.get("error", {}).get("message") or result.get("message") or "Unknown error"
        return f"Blockchain error: {error_msg}"
