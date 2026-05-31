import piexif
import os
import random
from PIL import Image


LAT_RANGE = (17.6590, 17.6900)
LNG_RANGE = (75.8900, 75.9200)

def to_deg(value, loc):
    """Convert decimal to degrees/minutes/seconds for EXIF format"""
    if value < 0: loc_ref = loc[0]
    else: loc_ref = loc[1]
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = int((t1 - min) * 60 * 100)
    return [(deg, 1), (min, 1), (sec, 100)], loc_ref

def inject_gps(img_path, lat, lng):
    """Injects Lat/Long into an image file"""
    img = Image.open(img_path)
    exif_dict = {"GPS": {}}
    
    lat_deg, lat_ref = to_deg(lat, ["S", "N"])
    lng_deg, lng_ref = to_deg(lng, ["W", "E"])

    exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_deg
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lng_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lng_deg

    exif_bytes = piexif.dump(exif_dict)
    img.save(img_path, exif=exif_bytes)
    print(f"Fixed: {img_path} at {lat}, {lng}")


dataset_path = r"C:\Users\Shrid\OneDrive\Desktop\final\pothole_dataset"
for filename in os.listdir(dataset_path):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        file_path = os.path.join(dataset_path, filename)
        random_lat = random.uniform(*LAT_RANGE)
        random_lng = random.uniform(*LNG_RANGE)
        inject_gps(file_path, random_lat, random_lng)
