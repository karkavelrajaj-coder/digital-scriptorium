import streamlit as st
import os
import json
import base64
import io
from ai_processor import analyze_image_bytes, load_stored_metadata
from storage_manager import StorageManager
import streamlit.components.v1 as components
from PIL import Image

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

    /* Global Typography Enhancements (Works with theme config) */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em !important;
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
        color: #61DAFB;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .meta-value {
        font-size: 1.05rem;
        margin-bottom: 15px;
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
                with st.spinner(f"Archiving {file_id} to cloud..."):
                    public_url = storage.upload_image(bytes_data, file_id)
                
                try:
                    img = Image.open(io.BytesIO(bytes_data))
                    w, h = img.size
                except Exception:
                    w, h = 1000, 1000
                
                st.session_state.images[file_id] = {
                    "bytes": bytes_data, # kept for local display speed
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

col_view, col_meta = st.columns([1.2, 1], gap="large")

# Left side: Image and Analysis
with col_view:
    st.subheader("🔬 Visual Intelligence Scan")
    st.image(image_bytes, width="stretch")
    
    is_processed = current_id in st.session_state.metadata
    analyze_label = "✅ Analysis Complete" if is_processed else "✨ Run Deep Analysis (AI Vision)"
    
    if st.button(analyze_label, key="analyze_btn", width="stretch", disabled=st.session_state.is_analyzing or is_processed):
        st.session_state.is_analyzing = True
        st.rerun() # Ensure UI reflects 'is_analyzing' immediately
    
    # This block runs after the rerun triggered above
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
                if key == "people" and isinstance(val, list): val = ", ".join(val)
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
                people_val = meta_f["people"]
                if isinstance(people_val, list): people_val = ", ".join(people_val)
                iiif_metadata.append({"label": {"en": ["People"]}, "value": {"en": [people_val]}})
            if meta_f.get("medium"): iiif_metadata.append({"label": {"en": ["Medium"]}, "value": {"en": [meta_f["medium"]]}})
            if meta_f.get("dimensions"): iiif_metadata.append({"label": {"en": ["Dimensions"]}, "value": {"en": [meta_f["dimensions"]]}})
            if meta_f.get("provenance"): iiif_metadata.append({"label": {"en": ["Provenance"]}, "value": {"en": [meta_f["provenance"]]}})

            manifest_obj["items"].append({
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
            })

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

          return {{
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
