import exifread

def verify_metadata(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    if not tags:
        return {
            "status": "No metadata",
            "details": {},
            "device": None,
            "location": None,
            "timestamp": None,
            "inconsistencies": []
        }

    details = {k: str(v) for k, v in tags.items()}
    software = str(tags.get('Image Software', ''))

    # Device Info
    device = str(tags.get('Image Model', '')) or str(tags.get('Image Make', '')) or None

    # Timestamp
    timestamp = str(tags.get('EXIF DateTimeOriginal', '')) or None

    # Location
    gps_lat = tags.get("GPS GPSLatitude")
    gps_lat_ref = tags.get("GPS GPSLatitudeRef")
    gps_lon = tags.get("GPS GPSLongitude")
    gps_lon_ref = tags.get("GPS GPSLongitudeRef")

    def convert_to_degrees(value):
        # value is a list of Ratio objects: [deg, min, sec]
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)

    location = None
    if gps_lat and gps_lon and gps_lat_ref and gps_lon_ref:
        lat = convert_to_degrees(gps_lat)
        lon = convert_to_degrees(gps_lon)

        if gps_lat_ref.values[0] != "N":
            lat = -lat
        if gps_lon_ref.values[0] != "E":
            lon = -lon

        location = f"{lat:.6f}, {lon:.6f}"

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
        "timestamp": timestamp,
        "inconsistencies": inconsistencies
    }
