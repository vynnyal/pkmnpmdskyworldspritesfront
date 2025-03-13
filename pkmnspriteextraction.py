import os
import time
import requests
import xml.etree.ElementTree as ET
from PIL import Image
from io import BytesIO

def get_github_raw_url(sprite_path, filename):
    base_url = "https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/"
    return f"{base_url}{sprite_path}{filename}"

def download_file(url, retries=3, delay=5):
    for attempt in range(retries):
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        elif response.status_code in [403, 429]:  # Rate limit detected
            print(f"GitHub rate limit hit. Waiting {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
        else:
            break  # Other errors, no point in retrying
    return None

def parse_animdata(xml_content, target_anims):
    try:
        root = ET.fromstring(xml_content)
        for target in target_anims:  # Prioritize Idle, then Hover, then Walk
            for anim in root.find("Anims"):
                name_elem = anim.find("Name")
                if name_elem is not None and name_elem.text == target:
                    width_elem = anim.find("FrameWidth")
                    height_elem = anim.find("FrameHeight")
                    if width_elem is not None and height_elem is not None:
                        print(f"Found {name_elem.text}: Width {width_elem.text}, Height {height_elem.text}")
                        return int(width_elem.text), int(height_elem.text), name_elem.text
        print("No matching animation found in AnimData.xml.")
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        input("Press Enter to exit...")
        exit(1)
    return None, None, None

def crop_first_frame(image_content, frame_width, frame_height):
    image = Image.open(BytesIO(image_content))
    first_frame = image.crop((0, 0, frame_width, frame_height))
    return first_frame

def trim_transparency(image):
    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox)
    return image

def process_sprites(textfile, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    processed_files = set(os.listdir(output_folder))
    target_anims = ["Idle", "Hover", "Walk"]
    
    with open(textfile, "r") as f:
        sprite_paths = [line.strip() for line in f.readlines()]
    
    for sprite_path in sprite_paths:
        output_filename = sprite_path.strip("/").replace("/", "-") + ".png"
        output_path = os.path.join(output_folder, output_filename)
        
        # Skip if file already exists
        if output_filename in processed_files:
            print(f"Skipping {sprite_path} (Already processed)")
            continue
        
        xml_url = get_github_raw_url(sprite_path, "AnimData.xml")
        
        # Get animdata first
        xml_content = download_file(xml_url)
        if not xml_content:
            print(f"Missing AnimData.xml for {sprite_path}. Skipping...")
            continue
        
        frame_width, frame_height, anim_name = parse_animdata(xml_content, target_anims)
        if not frame_width or not frame_height:
            print(f"No valid animation found in AnimData.xml for {sprite_path}. Skipping...")
            continue
        
        # Try downloading based on the found animation name
        image_content = download_file(get_github_raw_url(sprite_path, f"{anim_name}-Anim.png"))
        
        if not image_content:
            print(f"No default sprite found for {sprite_path}. Skipping...")
            continue
        
        # Process the sprite
        cropped_image = crop_first_frame(image_content, frame_width, frame_height)
        trimmed_image = trim_transparency(cropped_image)
        
        # Save output file
        trimmed_image.save(output_path)
        print(f"Saved: {output_path}")

# Example usage
process_sprites("sprite_list.txt", "output_sprites")