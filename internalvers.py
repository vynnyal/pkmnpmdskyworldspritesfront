import os
import xml.etree.ElementTree as ET
from PIL import Image

def parse_animdata(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for anim in root.find("Anims"):
            if anim.find("Name") is not None and anim.find("Name").text == "Idle":
                width_elem = anim.find("FrameWidth")
                height_elem = anim.find("FrameHeight")
                if width_elem is not None and height_elem is not None:
                    return int(width_elem.text), int(height_elem.text)
        for anim in root.find("Anims"):
            if anim.find("Name") is not None and anim.find("Name").text == "Hover":
                width_elem = anim.find("FrameWidth")
                height_elem = anim.find("FrameHeight")
                if width_elem is not None and height_elem is not None:
                    return int(width_elem.text), int(height_elem.text)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        input("Press Enter to exit...")
        exit(1)
    return None, None  # If neither Idle nor Hover is found

def crop_first_frame(image_path, frame_width, frame_height):
    image = Image.open(image_path)
    first_frame = image.crop((0, 0, frame_width, frame_height))
    return first_frame

def trim_transparency(image):
    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox)
    return image

def process_local_sprites(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    processed_files = set(os.listdir(output_folder))
    
    for root, _, files in os.walk(input_folder):
        if "AnimData.xml" not in files:
            print(f"Skipping {root} (AnimData.xml missing)")
            continue
        
        xml_path = os.path.join(root, "AnimData.xml")
        frame_width, frame_height = parse_animdata(xml_path)
        if not frame_width or not frame_height:
            print(f"Skipping {root} (No valid animation found)")
            continue
        
        image_path = None
        for img_name in ["Idle-Anim.png", "Hover-Anim.png"]:
            if img_name in files:
                image_path = os.path.join(root, img_name)
                break
        
        if not image_path:
            print(f"Skipping {root} (No sprite image found)")
            continue
        
        output_filename = root.strip(os.sep).replace(os.sep, "-") + ".png"
        output_path = os.path.join(output_folder, output_filename)
        
        if output_filename in processed_files:
            print(f"Skipping {root} (Already processed)")
            continue
        
        # Process the sprite
        cropped_image = crop_first_frame(image_path, frame_width, frame_height)
        trimmed_image = trim_transparency(cropped_image)
        
        # Save output file
        trimmed_image.save(output_path)
        print(f"Saved: {output_path}")

# Example usage
process_local_sprites("1004", "output_sprites")
