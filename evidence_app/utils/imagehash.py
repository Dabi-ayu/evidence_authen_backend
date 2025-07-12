import hashlib

def generate_sha256_hash(image_path):
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return hashlib.sha256(image_data).hexdigest()
    except Exception as e:
        print(f"[Hash Error] {e}")
        return None
