import streamlit as st
import os
import json
import base64
import io

# Note: streamlit-drawable-canvas is handled via st_canvas_safe wrapper below to bypass image serving issues.

from ai_processor import analyze_image_bytes, load_stored_metadata
from storage_manager import StorageManager
import streamlit.components.v1 as components
from PIL import Image, ImageOps
import streamlit_drawable_canvas as sdc
_orig_st_canvas = sdc.st_canvas

def st_canvas_wrapped(*args, **kwargs):
    """
    A robust wrapper for st_canvas that bypasses Streamlit's buggy internal image serving.
    It converts PIL images to Base64 Data URLs before they reach the internal st_canvas logic.
    """
    bg_img = kwargs.get("background_image")
    if bg_img and isinstance(bg_img, Image.Image):
        # Resize to requested dimensions manually
        h = kwargs.get("height", 400)
        w = kwargs.get("width", 600)
        bg_img = bg_img.resize((w, h))
        
        # Convert to Base64
        buffered = io.BytesIO()
        bg_img.save(buffered, format="PNG")
        bg_b64 = base64.b64encode(buffered.getvalue()).decode()
        bg_url = f"data:image/png;base64,{bg_b64}"
        
        # Inject the URL and REMOVE the PIL image to avoid internal processing
        kwargs["background_image"] = None
        # We need to manually set the backgroundImageURL prop in the underlying component call
        # But wait, st_canvas doesn't expose it directly.
        # Let's try setting background_color to "" and then monkey-patching the internal call?
        # Actually, if we set background_image to None, st_canvas will return None for background_image_url.
    
    return _orig_st_canvas(*args, **kwargs)

# Wait, the above won't work because we can't easily pass the URL to the underlying React component 
# without rewriting the whole st_canvas function.

# BETTER VERSION: Completely redefine st_canvas to be safe
def st_canvas_safe(
    fill_color="#eee", stroke_width=20, stroke_color="black", background_color="",
    background_image=None, update_streamlit=True, height=400, width=600,
    drawing_mode="freedraw", initial_drawing=None, display_toolbar=True,
    point_display_radius=3, key=None
):
    from hashlib import md5
    import numpy as np
    
    bg_url = None
    bg_obj = None
    if background_image:
        if isinstance(background_image, Image.Image):
            # Manually resize
            background_image = background_image.resize((width, height))
            # Manually convert to base64
            buffered = io.BytesIO()
            background_image.convert("RGB").save(buffered, format="JPEG", quality=75)
            bg_b64 = base64.b64encode(buffered.getvalue()).decode()
            bg_url = f"data:image/jpeg;base64,{bg_b64}"
            background_color = ""
            
            # Deep Injection: Create a Fabric.js background image object
            bg_obj = {
                "type": "image",
                "version": "4.4.0",
                "originX": "left",
                "originY": "top",
                "left": 0,
                "top": 0,
                "width": width,
                "height": height,
                "fill": "rgb(0,0,0)",
                "stroke": None,
                "strokeWidth": 0,
                "strokeDashArray": None,
                "strokeLineCap": "butt",
                "strokeDashOffset": 0,
                "strokeLineJoin": "miter",
                "strokeUniform": False,
                "strokeMiterLimit": 4,
                "scaleX": 1,
                "scaleY": 1,
                "angle": 0,
                "flipX": False,
                "flipY": False,
                "opacity": 1,
                "shadow": None,
                "visible": True,
                "backgroundColor": "",
                "fillRule": "nonzero",
                "paintFirst": "fill",
                "globalCompositeOperation": "source-over",
                "skewX": 0,
                "skewY": 0,
                "cropX": 0,
                "cropY": 0,
                "src": bg_url,
                "crossOrigin": None,
                "filters": []
            }
    
    if initial_drawing is None:
        initial_drawing = {"version": "4.4.0", "objects": []}
    
    initial_drawing["background"] = background_color
    if bg_obj:
        initial_drawing["backgroundImage"] = bg_obj
    
    # Call the internal component function directly
    comp_val = sdc._component_func(
        fillColor=fill_color,
        strokeWidth=stroke_width,
        strokeColor=stroke_color,
        backgroundColor=background_color,
        backgroundImageURL=bg_url, # Keep as fallback
        realtimeUpdateStreamlit=update_streamlit and (drawing_mode != "polygon"),
        canvasHeight=height,
        canvasWidth=width,
        drawingMode=drawing_mode,
        initialDrawing=initial_drawing,
        displayToolbar=display_toolbar,
        displayRadius=point_display_radius,
        key=key,
        default={"data": None, "raw": None},
    )
    
    if comp_val is None or comp_val.get("data") is None:
        from streamlit_drawable_canvas import CanvasResult
        return CanvasResult(json_data=initial_drawing)

    # Result parsing
    return sdc.CanvasResult(
        np.asarray(sdc._data_url_to_image(comp_val["data"])),
        comp_val["raw"],
    )

st_canvas = st_canvas_safe
import math

# --- Streamlit UI Config ---
st.set_page_config(
    page_title="Digital Scriptorium | Archival Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Premium Design System (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500&display=swap');

    /* Global Typography Enhancements */
    h1, h2, h3, h4, h5, h6, p, div, span {
        color: #e0e0e0 !important; /* Ensure light text for dark background */
    }

    /* SPECIFIC FIX: Force Dark Background for the whole app */
    .stApp {
        background-color: #0e1117 !important;
    }

    /* SPECIFIC FIX: Force Dark Sidebar background */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#111827, #0f172a) !important;
        background-color: #0e1117 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* SPECIFIC FIX: Force text visibility in sidebar */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
        color: #f3f4f6 !important;
    }

    /* SPECIFIC FIX: Sidebar Toggle Visibility */
    [data-testid="stSidebarCollapseButton"] {
        background-color: rgba(99, 102, 241, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 50% !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #ffffff !important;
    }

    /* SPECIFIC FIX: Fix white File Uploader */
    [data-testid="stFileUploader"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
        padding: 10px !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
        color: #e0e0e0 !important;
    }
    [data-testid="stFileUploader"] section div {
        color: #e0e0e0 !important;
    }
    [data-testid="stFileUploader"] label {
        color: #61DAFB !important;
    }
    
    /* Browse Files button inside uploader */
    [data-testid="stFileUploader"] button {
        background: rgba(99, 102, 241, 0.2) !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
        color: white !important;
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
    }

    /* Metadata Labels */
    .meta-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #61DAFB !important; /* Bright cyan for dark mode */
        font-weight: 700;
        margin-bottom: 5px;
    }
    .meta-value {
        font-size: 1.05rem;
        margin-bottom: 15px;
        color: #ffffff !important;
    }

    /* Custom Gradient Buttons */
    .stButton>button {
        border-radius: 12px;
        background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%) !important;
        color: white !important;
        padding: 10px 20px;
        font-weight: 600 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: 0 5px 15px rgba(99, 102, 241, 0.3);
    }

    /* File Uploader visibility */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 2px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
    }

    /* Sidebar Toggle - UNHIDE HEADER and style button */
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button, 
    button[aria-label="Expand sidebar"] {
        color: #ffffff !important;
        background: rgba(99, 102, 241, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.5) !important;
    }

    /* Hide only the unnecessary bits, NOT the whole header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Column Glass Card Effect */
    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 25px !important;
        margin: 10px !important;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5) !important;
    }

    /* Sidebar Selection Buttons */
    [data-testid="stSidebar"] .stButton button {
        text-align: left !important;
        display: block !important;
        width: 100% !important;
        padding: 12px 15px !important;
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(99, 102, 241, 0.15) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        transform: translateX(3px);
    }

    /* Metadata Field Spacing */
    .meta-field {
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    .meta-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #61DAFB;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .meta-value {
        font-size: 1.1rem;
        color: #ffffff;
        font-weight: 400;
    }

    /* Hide standard UI clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Internal Utilities ---
def format_list_field(val):
    if not isinstance(val, list):
        return str(val)
    processed = []
    for item in val:
        if isinstance(item, dict):
            processed.append(item.get("name") or item.get("label") or str(item))
        else:
            processed.append(str(item))
    return ", ".join(processed)

# --- Session State Initialization ---
if 'metadata' not in st.session_state:
    st.session_state.metadata = {}
if 'images' not in st.session_state:
    st.session_state.images = {} # id -> metadata dict
if 'manifest_ts' not in st.session_state:
    st.session_state.manifest_ts = None
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False

# --- Default Manifest State ---
cloud_manifest_url = "#"

# --- Cloud Storage Initialization ---
storage = StorageManager()

# --- Helper Functions ---
def get_base64(bin_file):
    return base64.b64encode(bin_file).decode()

# --- HEADER SECTION ---
st.markdown("""
    <div style='margin-bottom: 40px;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 5px; color: #ffffff;'>🏛️ Digital Scriptorium</h1>
        <p style='color: #61DAFB; font-size: 1.4rem; font-weight: 500;'>Archival Intelligence & IIIF Vision Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR: Digital Intake ---
with st.sidebar:
    st.header("📤 Repository Intake")
    uploaded_files = st.file_uploader("Drop archival assets here", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True, disabled=st.session_state.is_analyzing)
    
    if uploaded_files:
        # Generate a unique timestamp for this specific collection set if not already set
        if not st.session_state.manifest_ts:
            from datetime import datetime
            now = datetime.now()
            st.session_state.manifest_ts = now.strftime("%H%M%S%f")[:-3] # HHMMSSMS

        for uploaded_file in uploaded_files:
            file_id = uploaded_file.name
            if file_id not in st.session_state.images:
                bytes_data = uploaded_file.read()
                try:
                    img = Image.open(io.BytesIO(bytes_data))
                    w, h = img.size
                except Exception:
                    w, h = 1000, 1000
                
                with st.spinner(f"Archiving {file_id} to cloud..."):
                    public_url = storage.upload_image(bytes_data, file_id)
                
                st.session_state.images[file_id] = {
                    "bytes": bytes_data, 
                    "public_url": public_url,
                    "width": w,
                    "height": h
                }
    
    st.divider()
    status_color = "#22c55e" if storage.active else "#ef4444"
    st.markdown(f"<div style='font-size:0.8rem; color:{status_color};' align='right'>● Cloud Storage: {'Connected' if storage.active else 'Offline'}</div>", unsafe_allow_html=True)
    st.header("🗂️ Collection Index")
    
    if st.session_state.images:
        for file_id in sorted(st.session_state.images.keys()):
            is_processed = file_id in st.session_state.metadata
            cols = st.columns([5, 1])
            with cols[0]:
                icon = '🔬' if is_processed else '📄'
                if st.button(f"{icon} {file_id}", key=f"sel_{file_id}", disabled=st.session_state.is_analyzing):
                    st.session_state.current_image = file_id
            with cols[1]:
                color = '#22c55e' if is_processed else '#64748b'
                st.markdown(f"<div style='background: {color}; width: 8px; height: 8px; border-radius: 50%; margin-top: 15px; box-shadow: 0 0 10px {color};'></div>", unsafe_allow_html=True)
        
        st.divider()
        if st.button("🗑️ Purge Workspace", disabled=st.session_state.is_analyzing):
            st.session_state.images = {}
            st.session_state.metadata = {}
            st.session_state.manifest_ts = None
            st.rerun()

        if st.session_state.metadata:
            json_string = json.dumps(st.session_state.metadata, indent=4)
            st.download_button(
                label="📥 Export Manifest Data",
                file_name="archival_intelligence.json",
                mime="application/json",
                data=json_string,
                disabled=st.session_state.is_analyzing
            )
    else:
        st.info("Awaiting archival ingestion...")

# --- MAIN DASHBOARD AREA ---
if not st.session_state.images:
    st.info("### Welcome to the Digital Scriptorium\nPlease upload your archival documents in the sidebar to begin AI-powered enrichment.")
    st.stop()

if 'current_image' not in st.session_state or st.session_state.current_image not in st.session_state.images:
    st.session_state.current_image = sorted(st.session_state.images.keys())[0]

current_id = st.session_state.current_image
image_data = st.session_state.images[current_id]
image_bytes = image_data['bytes']

# Initialize manifest URLs
cloud_manifest_url = "#"
expected_manifest_url = "https://app/manifest.json"

col_view, col_meta = st.columns([1.5, 1], gap="large")

# Left side: Image and Analysis
with col_view:
    st.subheader("🔬 Visual Intelligence & Curation")
    
    tab_auto, tab_manual = st.tabs(["✨ AI Auto-Detect", "🖋️ Manual Curation"])
    
    with tab_auto:
        st.image(image_bytes, use_container_width=True)
        
        is_processed = current_id in st.session_state.metadata
        analyze_label = "✅ Analysis Complete" if is_processed else "✨ Run Deep Analysis (AI Vision)"
        
        if st.button(analyze_label, key="analyze_btn", use_container_width=True, disabled=st.session_state.is_analyzing or is_processed):
            st.session_state.is_analyzing = True
            st.rerun() # Ensure UI reflects 'is_analyzing' immediately
        
        if st.session_state.is_analyzing:
            with st.spinner("Decoding document semiotics..."):
                result = analyze_image_bytes(image_bytes, current_id)
                if "error" not in result:
                    st.session_state.metadata[current_id] = result
                    st.session_state.is_analyzing = False
                    st.success("Deep Analysis Completed")
                    st.rerun()
                else:
                    st.session_state.is_analyzing = False
                    st.error(f"Analysis Interrupted: {result['error']}")
                    st.rerun()

    with tab_manual:
        st.caption("Draw a rectangle on the image below, then give it a label.")
        
        # We need to scale the canvas to fit the column width but keep aspect ratio
        canvas_width = 700 
        scale_factor = canvas_width / image_data["width"]
        canvas_height = int(image_data["height"] * scale_factor)
        
        # Use a more reliable way to serve background to canvas
        # We resize the image manually to match canvas dimensions to solve the 'no attribute height' issue
        img_pil = Image.open(io.BytesIO(image_bytes))
        img_resized = img_pil.resize((canvas_width, canvas_height))
        
        # Selection tools
        tool_col1, tool_col2 = st.columns([2, 1])
        with tool_col1:
            manual_label = st.text_input("Annotation Label", placeholder="e.g., Archival Stamp, Signature", key=f"lab_{current_id}")
        with tool_col2:
            rect_color = st.color_picker("Color", "#FF0000")

        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color=rect_color,
            background_image=img_resized,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="rect",
            key=f"canvas_{current_id}",
        )

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if objects:
                # Get the last added object
                last_obj = objects[-1]
                if last_obj["type"] == "rect":
                    # Convert canvas coordinates to 0-1000 scale
                    # Canvas: x, y, width, height (top-left based)
                    # We need [ymin, xmin, ymax, xmax]
                    xmin = (last_obj["left"] / canvas_width) * 1000
                    ymin = (last_obj["top"] / canvas_height) * 1000
                    xmax = ((last_obj["left"] + last_obj["width"]) / canvas_width) * 1000
                    ymax = ((last_obj["top"] + last_obj["height"]) / canvas_height) * 1000
                    
                    if st.button("➕ Save Manual Annotation", use_container_width=True):
                        if current_id not in st.session_state.metadata:
                            st.session_state.metadata[current_id] = {"label": current_id, "detections": []}
                        if "detections" not in st.session_state.metadata[current_id]:
                             st.session_state.metadata[current_id]["detections"] = []
                        
                        st.session_state.metadata[current_id]["detections"].append({
                            "label": manual_label or "Manual Detection",
                            "bbox": [ymin, xmin, ymax, xmax]
                        })
                        st.success(f"Added '{manual_label}' to record.")
                        st.rerun()

    # View/Delete existing detections
    if current_id in st.session_state.metadata and st.session_state.metadata[current_id].get("detections"):
        with st.expander("📝 Manage Annotations", expanded=False):
            for i, det in enumerate(st.session_state.metadata[current_id]["detections"]):
                dcols = st.columns([4, 1])
                with dcols[0]:
                    st.write(f"**{det['label']}** (BBOX: {[int(x) for x in det['bbox']]})")
                with dcols[1]:
                    if st.button("🗑️", key=f"del_{current_id}_{i}"):
                        st.session_state.metadata[current_id]["detections"].pop(i)
                        st.rerun()

# Right side: Metadata
with col_meta:
    if current_id in st.session_state.metadata:
        data = st.session_state.metadata[current_id]
        st.subheader("📜 Curated Archival Record")
        st.markdown(f"<h4 style='color: #61DAFB; margin-bottom: 20px;'>{data.get('label', 'Untitled Asset')}</h4>", unsafe_allow_html=True)
        
        m_cols = st.columns(2)
        fields = [
            ("Classification", "classification"),
            ("Temporal Context", "date"),
            ("Key Personals", "people"),
            ("Media & Method", "medium"),
        ]
        
        for i, (label, key) in enumerate(fields):
            with m_cols[i % 2]:
                val = data.get(key, 'Undetermined')
                if key == "people":
                    val = format_list_field(val)
                st.markdown(f"<div class='meta-field'><div class='meta-label'>{label}</div><div class='meta-value'>{val}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='meta-field'><div class='meta-label'>Physical Dimensions</div><div class='meta-value'>{data.get('dimensions', 'N/A')}</div></div>", unsafe_allow_html=True)
        
        with st.expander("📚 Historical Provenance", expanded=True):
            st.write(data.get('provenance', 'No provenance records detected.'))
        with st.expander("📝 Descriptive Narrative", expanded=True):
            st.write(data.get('description', 'Narrative description unavailable.'))

        # --- IIIF TECHNICAL EXPORT SUITE ---
        st.divider()
        st.markdown("<div class='meta-label' style='margin-bottom:15px;'>🏛️ IIIF Interoperability</div>", unsafe_allow_html=True)
        
        # Build the global IIIF manifest
        manifest_filename = f"manifest_{st.session_state.manifest_ts}.json" if st.session_state.manifest_ts else "manifest.json"
        expected_manifest_url = storage.get_public_url(manifest_filename) or "https://app/manifest.json"
        
        manifest_obj = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": expected_manifest_url,
            "type": "Manifest",
            "label": { "en": ["Digital Scriptorium Collection"] },
            "summary": { "en": ["Archival collection enriched by AI Intelligence."] },
            "requiredStatement": {
                "label": { "en": ["Attribution"] },
                "value": { "en": ["Digital enrichment via Archival Intelligence (Aurexus)."] }
            },
            "items": []
        }
        
        for f_id, img_f in st.session_state.images.items():
            meta_f = st.session_state.metadata.get(f_id, {})
            image_url = img_f.get("public_url") or f"blob:{f_id}"
            
            # Map metadata to IIIF 3.0 format for the cloud manifest
            iiif_metadata = []
            if meta_f.get("classification"): iiif_metadata.append({"label": {"en": ["Classification"]}, "value": {"en": [meta_f["classification"]]}})
            if meta_f.get("date"): iiif_metadata.append({"label": {"en": ["Date"]}, "value": {"en": [meta_f["date"]]}})
            if meta_f.get("people"): 
                people_val = format_list_field(meta_f["people"])
                iiif_metadata.append({"label": {"en": ["People"]}, "value": {"en": [people_val]}})
            if meta_f.get("medium"): iiif_metadata.append({"label": {"en": ["Medium"]}, "value": {"en": [meta_f["medium"]]}})
            if meta_f.get("dimensions"): iiif_metadata.append({"label": {"en": ["Dimensions"]}, "value": {"en": [meta_f["dimensions"]]}})
            if meta_f.get("provenance"): iiif_metadata.append({"label": {"en": ["Provenance"]}, "value": {"en": [meta_f["provenance"]]}})

            # --- BBOX ANNOTATION INTEGRATION ---
            # Group annotations in an AnnotationPage
            annotation_items = []
            if meta_f.get("detections"):
                for i, det in enumerate(meta_f["detections"]):
                    label = det.get("label", f"Detection {i+1}")
                    bbox = det.get("bbox") # [ymin, xmin, ymax, xmax] in 0-1000
                    
                    if bbox and len(bbox) == 4:
                        ymin, xmin, ymax, xmax = bbox
                        # Scale normalized coordinates to pixels
                        # x, y, w, h
                        px = int((xmin / 1000) * img_f["width"])
                        py = int((ymin / 1000) * img_f["height"])
                        pw = int(((xmax - xmin) / 1000) * img_f["width"])
                        ph = int(((ymax - ymin) / 1000) * img_f["height"])
                        
                        annotation_items.append({
                            "id": f"https://app/annotation/{f_id}_{i}",
                            "type": "Annotation",
                            "motivation": "commenting",
                            "body": {
                                "type": "TextualBody",
                                "value": label,
                                "format": "text/plain"
                            },
                            "target": f"https://app/canvas/{f_id}#xywh={px},{py},{pw},{ph}"
                        })

            canvas_obj = {
                "id": f"https://app/canvas/{f_id}",
                "type": "Canvas",
                "label": { "en": [meta_f.get("label", f_id)] },
                "metadata": iiif_metadata,
                "height": img_f["height"],
                "width": img_f["width"],
                "items": [{
                    "id": f"https://app/page/{f_id}",
                    "type": "AnnotationPage",
                    "items": [{
                        "id": f"https://app/anno/{f_id}",
                        "type": "Annotation",
                        "motivation": "painting",
                        "body": {
                            "type": "Image",
                            "format": "image/jpeg",
                            "id": image_url
                        },
                        "target": f"https://app/canvas/{f_id}"
                    }]
                }]
            }

            # Add the AnnotationPage for metadata detections if any exist
            if annotation_items:
                canvas_obj["annotations"] = [{
                    "id": f"https://app/annotations/{f_id}",
                    "type": "AnnotationPage",
                    "items": annotation_items
                }]

            manifest_obj["items"].append(canvas_obj)

        manifest_json_str = json.dumps(manifest_obj, indent=2)
        # Upload manifest to cloud for global access
        with st.spinner("Synchronizing manifest to cloud..."):
            cloud_manifest_url = storage.upload_manifest(manifest_json_str, manifest_filename) or "#"

        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.download_button(
                "📥 Download Manifest",
                data=manifest_json_str,
                file_name="manifest.json",
                mime="application/json",
                use_container_width=True,
                key="dl_manifest_btn"
            )
        with col_ex2:
            st.markdown(f"""
                <a href="{cloud_manifest_url}" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; border-radius:12px; background:rgba(97,218,241,0.1); color:#61DAFB; border:1px solid #61DAFB; padding:10px; cursor:pointer; font-weight:600;">
                        🌐 Universal Data-Link
                    </button>
                </a>
            """, unsafe_allow_html=True)
        
        with st.expander("🛠️ View Raw IIIF Source"):
            st.code(manifest_json_str, language="json")
            st.caption("Copy this JSON or the Data-Link above to use in Project Mirador or UV.")
    else:
        st.subheader("📜 Curated Archival Record")
        st.info("Click 'Run Deep Analysis' to generate AI metadata for this document.")

st.markdown("---")
st.subheader("🌐 High-Fidelity IIIF Explorer")

# Preparation for IIIF Viewer remains similar but formatted
collection_data = []
for file_id in sorted(st.session_state.images.keys()):
    img_entry = st.session_state.images[file_id]
    b64 = get_base64(img_entry['bytes'])
    meta = st.session_state.metadata.get(file_id, {})
    collection_data.append({
        "id": file_id,
        "base64": b64,
        "width": img_entry['width'],
        "height": img_entry['height'],
        "metadata": meta
    })

mirador_html = f"""
<!DOCTYPE html>
<html>
  <head>
    <script src="https://unpkg.com/mirador@latest/dist/mirador.min.js"></script>
    <style>
      #mirador {{ width: 100%; height: 800px; position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.5); background: #000; border: 1px solid rgba(255,255,255,0.1); }}
    </style>
  </head>
  <body>
    <div id="mirador"></div>
    <script>
      (async function() {{
        const collection = {json.dumps(collection_data)};
        const current_id = "{current_id}";
        
        async function b64toBlobUrl(b64Data, contentType = 'image/jpeg') {{
          const res = await fetch(`data:${{contentType}};base64,${{b64Data}}`);
          const blob = await res.blob();
          return URL.createObjectURL(blob);
        }}

        const items = await Promise.all(collection.map(async (item) => {{
          const meta = item.metadata;
          const image_url = item.public_url || await b64toBlobUrl(item.base64);
          const iiifMetadata = [];
          if (meta.classification) iiifMetadata.push({{ label: {{ en: ["Classification"] }}, value: {{ en: [meta.classification] }} }});
          if (meta.date) iiifMetadata.push({{ label: {{ en: ["Date"] }}, value: {{ en: [meta.date] }} }});
          if (meta.people) iiifMetadata.push({{ label: {{ en: ["People"] }}, value: {{ en: [Array.isArray(meta.people) ? meta.people.join(", ") : meta.people] }} }});
          if (meta.medium) iiifMetadata.push({{ label: {{ en: ["Medium"] }}, value: {{ en: [meta.medium] }} }});
          if (meta.dimensions) iiifMetadata.push({{ label: {{ en: ["Dimensions"] }}, value: {{ en: [meta.dimensions] }} }});
          if (meta.provenance) iiifMetadata.push({{ label: {{ en: ["Provenance"] }}, value: {{ en: [meta.provenance] }} }});

          const annotationItems = [];
          if (meta.detections) {{
            meta.detections.forEach((det, i) => {{
              const label = det.label || `Detection ${{i + 1}}`;
              const bbox = det.bbox;
              if (bbox && bbox.length === 4) {{
                const [ymin, xmin, ymax, xmax] = bbox;
                const px = Math.round((xmin / 1000) * item.width);
                const py = Math.round((ymin / 1000) * item.height);
                const pw = Math.round(((xmax - xmin) / 1000) * item.width);
                const ph = Math.round(((ymax - ymin) / 1000) * item.height);
                
                annotationItems.push({{
                  "id": `https://app/annotation/${{item.id}}_${{i}}`,
                  "type": "Annotation",
                  "motivation": "commenting",
                  "body": {{
                    "type": "TextualBody",
                    "value": label,
                    "format": "text/plain"
                  }},
                  "target": `https://app/canvas/${{item.id}}#xywh=${{px}},${{py}},${{pw}},${{ph}}`
                }});
              }}
            }});
          }}

          const canvas = {{
            "id": `https://app/canvas/${{item.id}}`,
            "type": "Canvas",
            "label": {{ "en": [meta.label || item.id] }},
            "summary": {{ "en": [meta.description || ""] }},
            "height": item.height, "width": item.width,
            "metadata": iiifMetadata,
            "items": [{{
              "id": `https://app/page/${{item.id}}`,
              "type": "AnnotationPage",
              "items": [{{
                "id": `https://app/anno/${{item.id}}`,
                "type": "Annotation",
                "motivation": "painting",
                "body": {{
                  "id": image_url,
                  "type": "Image",
                  "format": "image/jpeg"
                }},
                "target": `https://app/canvas/${{item.id}}`
              }}]
            }}]
          }};

          if (annotationItems.length > 0) {{
            canvas.annotations = [{{
              "id": `https://app/annotations/${{item.id}}`,
              "type": "AnnotationPage",
              "items": annotationItems
            }}];
          }}

          return canvas;
        }}));

        const manifest = {{
          "@context": "http://iiif.io/api/presentation/3/context.json",
          "id": "{expected_manifest_url}",
          "type": "Manifest",
          "label": {{ "en": ["Digital Scriptorium Collection"] }},
          "summary": {{ "en": ["AI-curated archival collection. Deep-scan intelligence by AI Vision."] }},
          "items": items
        }};

        const manifestDataUri = "{cloud_manifest_url}" !== "#" ? "{cloud_manifest_url}" : "data:application/json;base64," + btoa(unescape(encodeURIComponent(JSON.stringify(manifest))));

        Mirador.viewer({{
          id: 'mirador',
          windows: [{{
            manifestId: manifestDataUri,
            canvasId: `https://app/canvas/${{current_id}}`,
            thumbnailNavigationPosition: 'far-bottom',
          }}],
          window: {{
            sideBarOpenByDefault: true,
            defaultSideBarPanel: 'info'
          }},
          thumbnailNavigation: {{
            defaultPosition: 'far-bottom',
          }}
        }});
      }})();
    </script>
  </body>
</html>
"""

st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
components.html(mirador_html, height=850)
st.markdown('</div>', unsafe_allow_html=True)
