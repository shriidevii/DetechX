import folium
from folium.plugins import HeatMap
import os
from exif import Image as ExifImage

# 1. Setup Map centered on Solapur
solapur_map = folium.Map(location=[17.6701, 75.9010], zoom_start=14, tiles="cartodbpositron")

def get_coords(img_path):
    """Extracts raw decimal coordinates for mapping"""
    try:
        with open(img_path, 'rb') as f:
            img = ExifImage(f)
            if img.has_exif and hasattr(img, 'gps_latitude'):
                # Convert degrees/minutes/seconds to decimal
                lat = img.gps_latitude[0] + img.gps_latitude[1]/60 + img.gps_latitude[2]/3600
                lng = img.gps_longitude[0] + img.gps_longitude[1]/60 + img.gps_longitude[2]/3600
                return [lat, lng]
    except Exception as e:
        print(f"Skipping {img_path}: {e}")
        return None
    return None

# 2. Gather all coordinates from your 'pothole_dataset'
heat_data = []
# Ensure this path matches your folder exactly
dataset_path = r"C:\Users\Shrid\OneDrive\Desktop\final\pothole_dataset"

if not os.path.exists(dataset_path):
    print("Error: Dataset folder not found! Check your path.")
else:
    for filename in os.listdir(dataset_path):
        if filename.lower().endswith((".jpg", ".png", ".jpeg")):
            coords = get_coords(os.path.join(dataset_path, filename))
            if coords:
                heat_data.append(coords)

# 3. Add HeatMap layer to satisfy the Smart City PS
if heat_data:
    # Radius and blur control the intensity of the 'glow'
    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.5).add_to(solapur_map)
    
    # Save the map as an interactive HTML file
    solapur_map.save("smc_heatmap.html")
    print(f"Success! Map generated with {len(heat_data)} data points.")
    print("Open 'smc_heatmap.html' in your browser to see the results.")
else:
    print("No GPS data found in images. Did you run geotag_dataset.py first?")