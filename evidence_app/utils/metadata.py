import exifread  

def verify_metadata(image_path):  
    with open(image_path, 'rb') as f:  
        tags = exifread.process_file(f)  
    
    # Simple checks  
    if not tags:  
        return "No metadata"  
    elif 'Photoshop' in str(tags.get('Software', '')):  
        return "Photoshop detected"  
    else:  
        return "Clean"  