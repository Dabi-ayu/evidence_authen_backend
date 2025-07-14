import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut

# Cache to avoid repeated requests for same coordinates
GEOCODE_CACHE = {}

def reverse_geocode(lat, lon):
    # Create a unique key for these coordinates
    cache_key = f"{lat:.6f},{lon:.6f}"
    
    # Check cache first
    if cache_key in GEOCODE_CACHE:
        return GEOCODE_CACHE[cache_key]
    
    try:
        geolocator = Nominatim(user_agent="image_evidence_authenticator")
        location = geolocator.reverse((lat, lon), exactly_one=True)
        
        if location:
            address = location.address
            # Save to cache
            GEOCODE_CACHE[cache_key] = address
            return address
    except (GeocoderUnavailable, GeocoderTimedOut):
        pass
    
    return None

def verify_metadata(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    if not tags:
        return {
            "status": "No metadata",
            "details": {},
            "device": None,
            "location": None,
            "address": None,  # New field
            "timestamp": None,
            "inconsistencies": []
        }

    details = {k: str(v) for k, v in tags.items()}
    software = str(tags.get('Image Software', ''))

    # Device Info
    device = None
    # Try multiple possible EXIF tags for device information
    for tag_name in ['Image Model', 'EXIF Model', 'Model', 
                    'Image Make', 'EXIF Make', 'Make',
                    'Image DeviceModelName', 'Device Model Name']:
        if tag_name in tags:
            device_value = str(tags[tag_name])
            # Clean up common prefixes
            if device_value.startswith('samsung') or device_value.startswith('apple'):
                device_value = device_value.capitalize()
            device = device_value
            break

    # If no device found, try manufacturer tags
    if not device:
        for tag_name in ['Image Manufacturer', 'EXIF Manufacturer', 'Manufacturer']:
            if tag_name in tags:
                device = str(tags[tag_name])
                break
    # Timestamp
    timestamp = str(tags.get('EXIF DateTimeOriginal', '')) or None

    # Location
    gps_lat = tags.get("GPS GPSLatitude")
    gps_lat_ref = tags.get("GPS GPSLatitudeRef")
    gps_lon = tags.get("GPS GPSLongitude")
    gps_lon_ref = tags.get("GPS GPSLongitudeRef")

    def convert_to_degrees(value):
        # Handle different GPS formats
        try:
            if hasattr(value, 'values'):
                d = float(value.values[0].num) / float(value.values[0].den)
                m = float(value.values[1].num) / float(value.values[1].den)
                s = float(value.values[2].num) / float(value.values[2].den)
                return d + (m / 60.0) + (s / 3600.0)
            else:
                return float(value)
        except (TypeError, AttributeError, IndexError):
            return None

    location = None
    address = None
    if gps_lat and gps_lon and gps_lat_ref and gps_lon_ref:
        lat = convert_to_degrees(gps_lat)
        lon = convert_to_degrees(gps_lon)

        if lat is not None and lon is not None:
            if gps_lat_ref.values[0] != "N":
                lat = -lat
            if gps_lon_ref.values[0] != "E":
                lon = -lon

            location = f"{lat:.6f}, {lon:.6f}"
            # Get human-readable address
            address = reverse_geocode(lat, lon)

    # Inconsistencies (basic)
    inconsistencies = []
    if "Photoshop" in software:
        inconsistencies.append("Edited with Photoshop")
    if not timestamp:
        inconsistencies.append("Missing timestamp")
    if not device:
        inconsistencies.append("Missing device information")
    if not location:
        inconsistencies.append("Missing GPS data")

    # Status logic
    if "Photoshop" in software:
        status = "Photoshop detected"
    else:
        status = "Clean"

    return {
        "status": status,
        "details": details,
        "device": device,
        "location": location,
        "address": address,  # New field
        "timestamp": timestamp,
        "inconsistencies": inconsistencies
    }