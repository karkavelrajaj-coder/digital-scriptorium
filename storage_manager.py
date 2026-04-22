import os
import streamlit as st
from supabase import create_client, Client

class StorageManager:
    """
    Manages archival image uploads to Supabase Storage and permanent URL generation.
    """
    
    def __init__(self):
        self.url = st.secrets["supabase"]["url"]
        self.key = st.secrets["supabase"]["key"]
        self.bucket_name = "archival-assets"
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
            self.active = True
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {str(e)}")
            self.active = False

    def upload_image(self, file_bytes, file_id):
        """
        Uploads image bytes to the 'archival-assets' bucket and returns the public URL.
        """
        if not self.active:
            return None
            
        try:
            # Overwrite if exists (archival logic)
            self.supabase.storage.from_(self.bucket_name).upload(
                path=file_id,
                file=file_bytes,
                file_options={"content-type": "image/jpeg", "upsert": "true"}
            )
            
            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_id)
            return public_url
        except Exception as e:
            print(f"Error uploading {file_id} to cloud storage: {e}")
            return None

    def get_public_url(self, file_id):
        """
        Calculates the public URL for an existing file.
        """
        if not self.active:
            return None
        return self.supabase.storage.from_(self.bucket_name).get_public_url(file_id)

    def upload_manifest(self, manifest_json, manifest_id="manifest.json"):
        """
        Uploads the IIIF manifest to cloud storage for global interoperability.
        """
        if not self.active:
            return None
            
        try:
            self.supabase.storage.from_(self.bucket_name).upload(
                path=manifest_id,
                file=manifest_json.encode('utf-8'),
                file_options={"content-type": "application/json", "upsert": "true"}
            )
            return self.supabase.storage.from_(self.bucket_name).get_public_url(manifest_id)
        except Exception as e:
            print(f"Error uploading manifest to cloud: {e}")
            return None
