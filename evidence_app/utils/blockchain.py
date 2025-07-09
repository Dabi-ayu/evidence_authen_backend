import hashlib
import subprocess
import os

# Define and create the directory for .ots files
OTS_DIR = os.path.join('media', 'ots_files')
os.makedirs(OTS_DIR, exist_ok=True)

def generate_ots(image_path):
    """
    Generates a .ots timestamp file for the given image and returns the (ots_path, sha256_hash).
    """
    try:
        # Compute SHA256 hash of the image
        with open(image_path, 'rb') as f:
            image_data = f.read()
            sha256_hash = hashlib.sha256(image_data).hexdigest()

        # Define final path where .ots will be saved
        ots_path = os.path.join(OTS_DIR, f"{sha256_hash}.ots")

        # Run OpenTimestamps
        subprocess.run(['ots', 'stamp', image_path], check=True)

        # Original .ots is created beside the image
        temp_ots = image_path + '.ots'
        if os.path.exists(temp_ots):
            os.replace(temp_ots, ots_path)
            return ots_path, sha256_hash
        else:
            print("[Blockchain Error] OTS file not found after stamping.")
            return None, sha256_hash

    except subprocess.CalledProcessError as e:
        print(f"[Blockchain Error] OTS command failed: {e}")
        return None, None
    except Exception as e:
        print(f"[Blockchain Error] Unexpected error: {e}")
        return None, None


def verify_ots(ots_path):
    """
    Verifies a given .ots file and returns a structured result.
    """
    if not os.path.exists(ots_path):
        return {'valid': False, 'message': 'OTS file not found'}

    try:
        result = subprocess.run(
            ['ots', 'verify', ots_path],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            'valid': True,
            'timestamp': 'Verification successful',  # Optional: parse result.stdout for real time
            'output': result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {'valid': False, 'message': e.stderr}
    except Exception as e:
        return {'valid': False, 'message': str(e)}
