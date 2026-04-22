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

def analyze_image_bytes(image_bytes, image_id):
    """
    Uses GPT-4o Vision to analyze an image (as bytes) and return structured metadata.
    """
    if not client:
        return {"error": "OpenAI API key not found. Please set it in .env or Streamlit secrets."}

    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional archival expert. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": (
                                "Analyze this archival document image and provide a professional, museum-grade description. "
                                "Provide a JSON response with the following fields: "
                                "'label' (short, authoritative title), "
                                "'classification' (e.g., Documents, Photography, Correspondence), "
                                "'date' (estimated or specific historical date), "
                                "'people' (Artist, signatories, or key individuals mentioned), "
                                "'medium' (Materials and technique, e.g., Ink on aged paper, stamp), "
                                "'dimensions' (Estimated or observed physical size), "
                                "'provenance' (Historical context or ownership history if detectable), "
                                "'description' (A rich 3-4 sentence narrative description of content and condition). "
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low" # Using low detail for high-res archival documents to improve stability
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
            response_format={ "type": "json_object" }
        )

        content = response.choices[0].message.content
        
        if content is None:
            finish_reason = response.choices[0].finish_reason
            return {"error": f"AI returned no content. Reason: {finish_reason}. This usually happens when an image is extremely large or triggers a safety filter."}

        analysis = json.loads(content)
        return analysis
    except Exception as e:
        print(f"Error analyzing image {image_id}: {e}")
        return {
            "error": f"AI Analysis failed: {str(e)}",
            "label": f"Image {image_id}",
            "classification": "Incomplete",
            "date": "N/A"
        }

# Helpers for metadata storage (can work with session state too)
def save_metadata(metadata, filename="metadata.json"):
    with open(filename, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_stored_metadata(filename="metadata.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}
