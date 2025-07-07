import exifread

def verify_metadata(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    if not tags:
        return {
            "status": "No metadata",
            "details": {}
        }
    elif 'Photoshop' in str(tags.get('Software', '')):
        return {
            "status": "Photoshop detected",
            "details": {k: str(v) for k, v in tags.items()}
        }
    else:
        return {
            "status": "Clean",
            "details": {k: str(v) for k, v in tags.items()}
        }
