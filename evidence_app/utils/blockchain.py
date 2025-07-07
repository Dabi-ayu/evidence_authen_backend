import hashlib  
import datetime  

def log_verification(image_path):  
    """Creates fake blockchain entry"""  
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  
    image_hash = hashlib.sha256(open(image_path, 'rb').read()).hexdigest()  
    return f"{timestamp}_{image_hash[:10]}"  # Fake transaction ID  