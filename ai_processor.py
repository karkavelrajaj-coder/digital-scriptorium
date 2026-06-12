import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Load environment variables from .env
load_dotenv()

# Get API key from env or streamlit secrets
api_key = os.getenv("OPENAI_API_KEY")
if not api_key and HAS_STREAMLIT:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

client = OpenAI(api_key=api_key) if api_key else None

import io
from PIL import Image, ImageDraw

def analyze_image_bytes(image_bytes, image_id):
    """
    Uses High-Contrast Anchors to ground AI spatial perception.
    """
    if not client:
        return {"error": "OpenAI API key not found."}

    original_img = Image.open(io.BytesIO(image_bytes))
    w, h = original_img.size
    img = original_img.copy()
    draw = ImageDraw.Draw(img)
    
    # Draw huge, high-contrast anchor points
    anchors = [
        (0, 0), (500, 0), (1000, 0),
        (0, 500), (500, 500), (1000, 500),
        (0, 1000), (500, 1000), (1000, 1000)
    ]
    
    for ax, ay in anchors:
        px = int((ax/1000) * (w-1))
        py = int((ay/1000) * (h-1))
        
        # Draw a big black dot with white cross
        box_size = 80
        draw.rectangle([px-box_size, py-box_size, px+box_size, py+box_size], fill="black")
        draw.line([(px-box_size, py), (px+box_size, py)], fill="white", width=5)
        draw.line([(px, py-box_size), (px, py+box_size)], fill="white", width=5)
        
        # Draw the coordinate text
        text = f"{ax},{ay}"
        draw.text((px-50, py+box_size+5), text, fill="red")

    # Save to buffer for AI
    buff = io.BytesIO()
    img.save(buff, format="JPEG")
    base64_image = base64.b64encode(buff.getvalue()).decode('utf-8')

    prompt = (
        "Analyze this archival document image and provide a professional description. "
        "I have added 9 BLACK ANCHORS with labels like '500,500' (X,Y) to guide you. "
        "Use these as reference points to provide pixel-perfect bounding boxes. "
        "Provide a JSON response with: "
        "'label' (document title), 'classification', 'date', 'people', 'medium', 'dimensions', 'provenance', 'description', "
        "'detections' (list of stamps/signatures). "
        "Each detection MUST have 'label' and 'bbox' ([ymin, xmin, ymax, xmax] in 0-1000 scale)."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional archival expert. Be extremely precise with spatial coordinates."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high" 
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
            response_format={ "type": "json_object" }
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        # Ensure it has the metadata fields the app expects
        defaults = {
            "label": "Document", "classification": "Archival", "date": "Unknown",
            "people": [], "medium": "Paper", "dimensions": "Unknown",
            "provenance": "Unknown", "description": ""
        }
        for k, v in defaults.items():
            if k not in data: data[k] = v
        return data
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e), "label": f"Image {image_id}"}

# Helpers for metadata storage (can work with session state too)
def save_metadata(metadata, filename="metadata.json"):
    with open(filename, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_stored_metadata(filename="metadata.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}
