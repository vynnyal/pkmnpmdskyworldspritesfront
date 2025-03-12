import os
import requests
import xml.etree.ElementTree as ET
from PIL import Image
from io import BytesIO

def get_github_raw_url(sprite_path, filename):
    base_url = "https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/"
    return f"{base_url}{sprite_path}{filename}"

def download_file(url):
    print(f"Downloading: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        print("Download successful.")
        return response.content
    print("Download failed.")
    return None

def parse_animdata(xml_content):
    try:
        print("Parsing XML...")
        root = ET.fromstring(xml_content)
        for anim in root.find("Anims"):
            name_elem = anim.find("Name")
            width_elem = anim.find("FrameWidth")
            height_elem = anim.find("FrameHeight")
            if name_elem is not None and width_elem is not None and height_elem is not None:
                print(f"Found animation: {name_elem.text}, Width: {width_elem.text}, Height: {height_elem.text}")
                return int(width_elem.text), int(height_elem.text), name_elem.text
        print("No valid animation found.")
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    return None, None, None

def crop_first_frame(image_content, frame_width, frame_height):
    print(f"Cropping first frame with dimensions: {frame_width}x{frame_height}")
    image = Image.open(BytesIO(image_content))
    first_frame = image.crop((0, 0, frame_width, frame_height))
    return first_frame

def trim_transparency(image):
    print("Trimming transparency...")
    bbox = image.getbbox()
    if bbox:
        print("Transparency trimmed.")
        return image.crop(bbox)
    print("No transparency to trim.")
    return image

def debug_single_sprite(sprite_path):
    print(f"Processing sprite: {sprite_path}")
    xml_url = get_github_raw_url(sprite_path, "AnimData.xml")
    xml_content = download_file(xml_url)
    if not xml_content:
        print("AnimData.xml missing.")
        return
    
    frame_width, frame_height, anim_name = parse_animdata(xml_content)
    if not frame_width or not frame_height:
        print("Frame dimensions could not be determined.")
        return
    
    # Try downloading Idle-Anim.png first, then Hover-Anim.png, then Walk-Anim.png
    image_content = download_file(get_github_raw_url(sprite_path, "Idle-Anim.png")) or \
                    download_file(get_github_raw_url(sprite_path, "Hover-Anim.png")) or \
                    download_file(get_github_raw_url(sprite_path, "Walk-Anim.png"))
    
    if not image_content:
        print("No valid sprite image found.")
        return
    
    # Process the sprite
    cropped_image = crop_first_frame(image_content, frame_width, frame_height)
    trimmed_image = trim_transparency(cropped_image)
    
    output_filename = sprite_path.strip("/").replace("/", "-") + "_debug.png"
    output_path = os.path.join("debug_output", output_filename)
    os.makedirs("debug_output", exist_ok=True)
    trimmed_image.save(output_path)
    print(f"Saved debug output: {output_path}")

# Run interactive debug mode
sprite_path = input("Enter sprite path (e.g., sprite/0006/0000/0001/): ")
debug_single_sprite(sprite_path)